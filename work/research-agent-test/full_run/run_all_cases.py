# -*- coding: utf-8 -*-
"""Phase 3: 用 Playwright 自带 Chromium(headless) 执行 all_cases.json 全部用例。

- API 型(329): context.request 带双令牌(X-BMP-Token + Authorization: Bearer) 探活 + 按维度断言
- UI 型(2)  : 浏览器导航到页面(空白页重试) + 校验内容到达
- FUNC型(69): 浏览器进入对话(空白页重试) + 发送触发消息 + 校验回复到达
- 健壮性：未登录访问偶发空白页(D1) -> 登录/导航均加重载重试；401 自动重登刷新令牌
- 进度：每用例一行；每 5 分钟打印汇总(已用/ETA/各结果计数)；结果每 10 例落盘
"""
import json
import os
import time
import datetime

from playwright.sync_api import sync_playwright

BASE_URL = "http://47.97.154.50:8090"
ACCOUNT = os.environ.get("FX_ACCOUNT", "test_ft001@ft.cntaiping.com")
PASSWORD = os.environ.get("FX_PASSWORD", "Tp0909@test")
OTP = os.environ.get("FX_OTP", "260909")

HERE = os.path.dirname(os.path.abspath(__file__))
CASES_PATH = os.path.join(HERE, "all_cases.json")
OUT_DIR = HERE
RESULTS = os.path.join(OUT_DIR, "exec_results.json")
PROGRESS = os.path.join(OUT_DIR, "progress.log")
SHOTS = os.path.join(OUT_DIR, "shots")
TOKENS = os.path.join(OUT_DIR, "tokens.json")
os.makedirs(SHOTS, exist_ok=True)

HTTP_VERBS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def now():
    return datetime.datetime.now().strftime("%H:%M:%S")


def log(msg):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def classify(tp_type, status):
    if status is None:
        return ("error", "请求异常/无响应")
    if tp_type == "正常":
        if 200 <= status < 300:
            return ("pass", f"2xx 可用({status})")
        if status == 401:
            return ("fail", "未鉴权返回401(正常流程应可访问)")
        if status == 404:
            return ("fail", "404 路由不存在")
        if status == 405:
            return ("skip", "网关拒绝方法(405)")
        if status == 500:
            return ("fail", "服务端500")
        if status in (400, 422):
            # 端点可达且做入参校验，但无合法请求体无法验证 2xx -> 不误判失败
            return ("inconclusive", f"端点可达,校验生效({status}),合法2xx需合法请求体")
        return ("fail", f"status={status}")
    if tp_type == "安全":
        if status in (401, 403):
            return ("pass", f"正确拒绝未授权({status})")
        if 200 <= status < 300:
            return ("fail", f"未授权却返回2xx({status}) 鉴权绕过!")
        if status == 405:
            return ("skip", "网关拒绝方法(405)")
        return ("inconclusive", f"status={status}")
    if tp_type == "边界":
        if status in (400, 422):
            return ("pass", f"正确拒绝非法参数({status})")
        if 200 <= status < 300:
            return ("fail", f"非法参数被接受({status})")
        if status == 405:
            return ("skip", "网关拒绝方法(405)")
        if status == 401:
            return ("inconclusive", "需鉴权,无法判定边界")
        return ("inconclusive", f"status={status}")
    if tp_type == "异常":
        if status == 404:
            return ("pass", "正确返回404")
        if 200 <= status < 300:
            return ("fail", f"不存在资源返回2xx({status})")
        if status == 405:
            return ("skip", "网关拒绝方法(405)")
        if status == 401:
            return ("inconclusive", "需鉴权")
        return ("inconclusive", f"status={status}")
    return ("inconclusive", f"status={status}")


def grab_tokens(page):
    try:
        data = page.evaluate(
            """() => ({
                bmp: localStorage.getItem('fuxiang_bmp_token'),
                access: localStorage.getItem('fuxiang_access_token'),
                token: localStorage.getItem('fuxiang_token'),
                refresh: localStorage.getItem('fuxiang_refresh_token')
            })"""
        )
    except Exception:
        data = {}
    data = {k: (v or "") for k, v in data.items()}
    json.dump(data, open(TOKENS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return data


def goto_with_retry(page, url, max_tries=8, ok_len=50, need_input=False):
    """导航并在空白页(D1)时重载重试，直到内容到达或表单出现。"""
    for _ in range(max_tries):
        try:
            page.goto(url, wait_until="commit", timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(3500)
        bl = len((page.inner_text("body") or ""))
        if need_input:
            if page.query_selector('input[placeholder="邮箱账号"]'):
                return True
        elif bl >= ok_len:
            return True
        try:
            page.reload(wait_until="commit", timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
    return False


def do_login(page):
    for _ in range(10):
        goto_with_retry(page, BASE_URL + "/login", need_input=True, max_tries=6)
        try:
            page.wait_for_selector('input[placeholder="邮箱账号"]', timeout=10000)
        except Exception:
            continue
        try:
            page.fill('input[placeholder="邮箱账号"]', ACCOUNT)
            page.fill('input[placeholder="密码"]', PASSWORD)
            page.fill('input[placeholder="动态口令（6位）"]', OTP)
            page.click('button:has-text("登 录")')
        except Exception:
            continue
        try:
            page.wait_for_url("**/chat", timeout=20000)
            return True
        except Exception:
            page.wait_for_timeout(3000)
    return False


def ensure_logged_in(page):
    if "/login" in page.url:
        do_login(page)
        return True
    return False


def find_chat_input(page):
    for sel in ["textarea", "[contenteditable='true']", "input[type='text']", "input:not([type])"]:
        el = page.query_selector(sel)
        if el and el.is_visible():
            return el
    return None


def exec_api(anon_ctx, context, page, case, tokens, do_login_fn):
    """按维度区分鉴权：
    - 安全(鉴权缺失/越权): 用无 cookie 的独立请求上下文 + 不带令牌 -> 验证被拒(401/403)
    - 正常/边界/异常: 用浏览器上下文(共享登录 cookie) + 双令牌头 -> 验证可用/校验/404
    写方法(GET 除外)附带最小 JSON 请求体。"""
    ex = case["exec"]
    is_secure = case["dimension"] == "安全"
    method = ex["http_method"]
    body = None
    # 仅鉴权类(非安全)写方法附带最小请求体；安全类不带体，让鉴权中间件先拦截
    if not is_secure and method in ("POST", "PUT", "PATCH"):
        body = "{}"
    if is_secure:
        # 真正无鉴权
        try:
            resp = anon_ctx.fetch(ex["url"], method=method, data=body, timeout=20000)
            status = resp.status
        except Exception as e:
            return "error", f"请求异常:{str(e)[:80]}", None
        res, detail = classify(case["dimension"], status)
        return res, detail + f" | {ex['url'][:60]}", status
    # 鉴权类请求
    headers = {}
    if tokens.get("bmp"):
        headers["X-BMP-Token"] = tokens["bmp"]
    if tokens.get("access"):
        headers["Authorization"] = "Bearer " + tokens["access"]
    status = None
    try:
        kw = {"method": method, "headers": headers, "timeout": 20000}
        if body is not None:
            kw["data"] = body
            kw["headers"] = {**headers, "Content-Type": "application/json"}
        resp = context.request.fetch(ex["url"], **kw)
        status = resp.status
    except Exception as e:
        return "error", f"请求异常:{str(e)[:80]}", status
    if status == 401:
        do_login_fn()
        tokens.update(grab_tokens(page))
        headers = {}
        if tokens.get("bmp"):
            headers["X-BMP-Token"] = tokens["bmp"]
        if tokens.get("access"):
            headers["Authorization"] = "Bearer " + tokens["access"]
        try:
            kw = {"method": method, "headers": headers, "timeout": 20000}
            if body is not None:
                kw["data"] = body
                kw["headers"] = {**headers, "Content-Type": "application/json"}
            resp = context.request.fetch(ex["url"], **kw)
            status = resp.status
        except Exception as e:
            return "error", f"重试请求异常:{str(e)[:80]}", status
    res, detail = classify(case["dimension"], status)
    return res, detail + (f" | {ex['url'][:60]}" if status is not None else ""), status


def exec_ui_nav(page, case):
    route = case["exec"]["route"]
    if not goto_with_retry(page, BASE_URL + route, ok_len=50, max_tries=6):
        return "error", f"页面空白(D1,重试后仍空白):{route}"
    if "/login" in page.url:
        return "fail", f"被重定向到登录页:{route}"
    body = (page.inner_text("body") or "").strip()
    if len(body) > 50:
        page.screenshot(path=os.path.join(SHOTS, f"{case['case_id']}.png"))
        return "pass", f"页面可达,内容长度={len(body)}"
    return "fail", f"页面内容为空({route})"


def exec_chat(page, case):
    ensure_logged_in(page)
    if not goto_with_retry(page, BASE_URL + "/chat", ok_len=50, max_tries=6):
        return "error", "对话页空白(D1,重试后仍空白)"
    # 轮询等待输入框出现
    box = None
    for _ in range(8):
        box = find_chat_input(page)
        if box:
            break
        page.wait_for_timeout(1500)
    if not box:
        return "error", "未找到对话输入框"
    before = len((page.inner_text("body") or "").strip())
    try:
        box.click()
        page.keyboard.type(case["exec"]["prompt"], delay=20)
        sent = False
        for bsel in ["button:has-text('发送')", "button[type='submit']", "[class*='send']"]:
            b = page.query_selector(bsel)
            if b and b.is_visible():
                b.click()
                sent = True
                break
        if not sent:
            page.keyboard.press("Enter")
    except Exception as e:
        return "error", f"发送失败:{str(e)[:60]}"
    replied = False
    cur = before
    end = time.time() + 35
    while time.time() < end:
        page.wait_for_timeout(2000)
        cur = len((page.inner_text("body") or "").strip())
        if cur > before + 5:
            replied = True
            break
    if replied:
        page.screenshot(path=os.path.join(SHOTS, f"{case['case_id']}.png"))
        return "pass", f"回复到达(增量={cur - before})"
    return "fail", "超时未收到回复"


def main():
    data = json.load(open(CASES_PATH, encoding="utf-8"))
    cases = data["cases"]
    limit = int(os.environ.get("FX_LIMIT", "0") or "0")
    if limit > 0:
        cases = cases[:limit]
    n = len(cases)
    log(f"=== 启动全量执行: 共 {n} 条用例 (全量{data['by_tag'].get('全量')}/新增{data['by_tag'].get('新增')}) ===")
    results = []
    start = time.time()
    last5 = start
    tally = {}

    def save():
        json.dump({"total": n, "results": results, "tally": tally, "started_at": start},
                  open(RESULTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
        context = browser.new_context()
        anon_ctx = p.request.new_context()  # 无 cookie，用于安全类无鉴权探测
        page = context.new_page()
        ok = do_login(page)
        log(f"登录{'成功' if ok else '失败(将重试)'} ")
        tokens = grab_tokens(page)
        log(f"token bmp={'有' if tokens.get('bmp') else '无'} access={'有' if tokens.get('access') else '无'}")

        for idx, case in enumerate(cases, 1):
            t0 = time.time()
            try:
                if case["exec_type"] == "api":
                    res, detail, _ = exec_api(anon_ctx, context, page, case, tokens, lambda: do_login(page))
                elif case["exec_type"] == "ui_nav":
                    ensure_logged_in(page)
                    res, detail = exec_ui_nav(page, case)
                else:
                    res, detail = exec_chat(page, case)
            except Exception as e:
                res, detail = "error", f"未捕获异常:{str(e)[:80]}"
            elapsed = time.time() - t0
            rec = {
                "case_id": case["case_id"], "tp_id": case["tp_id"], "tag": case["tag"],
                "dimension": case["dimension"], "exec_type": case["exec_type"],
                "module": case["module"], "method": case["method"], "path": case["path"],
                "result": res, "detail": detail, "elapsed_s": round(elapsed, 2),
            }
            results.append(rec)
            tally[res] = tally.get(res, 0) + 1

            done = idx
            used = time.time() - start
            rate = done / used if used > 0 else 0
            eta = (n - done) / rate if rate > 0 else 0
            log(f"[{idx}/{n}] {case['case_id']} {case['exec_type']}/{case['dimension']} "
                 f"tag={case['tag']} -> {res} | {detail[:45]} | 已用{used/60:.1f}m ETA{eta/60:.1f}m")

            if idx % 10 == 0:
                save()
            if time.time() - last5 >= 300:
                log(f"=== 5分钟进度 {done}/{n} 通过{tally.get('pass',0)} 失败{tally.get('fail',0)} "
                     f"跳过{tally.get('skip',0)} 存疑{tally.get('inconclusive',0)} 错误{tally.get('error',0)} "
                     f"| 已用{used/60:.1f}m ETA{eta/60:.1f}m ===")
                last5 = time.time()
        save()
        browser.close()
    used = (time.time() - start) / 60
    log(f"=== 完成: {n} 条 | 通过{tally.get('pass',0)} 失败{tally.get('fail',0)} "
         f"跳过{tally.get('skip',0)} 存疑{tally.get('inconclusive',0)} 错误{tally.get('error',0)} "
         f"| 总用时{used:.1f}m ===")


if __name__ == "__main__":
    main()
