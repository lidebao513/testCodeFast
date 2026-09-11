"""最小执行器：不依赖被测服务运行也能出测试结果。
- api       → 结构性断言(后端文件确有该路由定义)；被测服务可达时再做 HTTP 探活(附加信息)
- page      → 路由断言(前端 router 文件确有该 path)
- component → 交互断言(组件文件含交互钩子)
status 以结构性断言为准；动态探活仅记录，不覆盖结构性结论。
被动态探测开关(ENABLE_DYNAMIC_PROBE)关闭或服务不可达时，动态探活标记 skipped，不阻塞、不误报。
单次服务探活：每个项目仅做一次 /health 检查并缓存结果，避免逐 case 网络超时。
"""

"""测试执行器。

演进（阶段4）：
- 批次1（D-★4/D-★5）：单条异常隔离 + 分批 commit；一次执行一个 batch_id 贯穿 runs/reports。
- 批次2（D-★1/D-★2）：以真实 HTTP 响应为主判定，按 expect 校验（异常维度走反向断言）；
  服务不可达时降级 static 并标 `structural_only`，绝不把"没测"伪装成"通过"。
- 批次3（D-★6/D-②1/D-②2）：支持执行子集筛选；自动取鉴权态并注入 Authorization；
  IO 并发执行（写库仍串行，规避 SQLite 写锁）。
- 批次4（D-★3）：page 类用例可走真实浏览器渲染断言 + 失败自动截图（可选依赖，缺则降级）。
"""
import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.config import settings
from backend.core.enums import (
    ExecStatus,
    FType,
    VerifyLayer,
    derive_verify_layer,
    method_kind,
    select_execution_mode,
)
from backend.db import get_conn
from backend.modules import auth as auth_mod
from backend.modules import batch_store as bs_mod
from backend.modules import browser as browser_mod
from backend.modules.project_manager import pm


# —— 阶段5 批次（D-②6）：执行进度注册表 + 中断信号 ——
# 进度与中断都是「执行中与本轮」的瞬时状态，用进程内注册表即可；
# 重启后历史进度可由 runs 表重建（见 main.py 的 /execute/status 回退）。
_BATCH_REGISTRY = {}  # batch_id -> 进度快照（live）
_BATCH_REGISTRY_LOCK = threading.Lock()
_CANCEL_SET = set()  # 被请求中断的 batch_id 集合（跨线程信号）
_CANCEL_LOCK = threading.Lock()

# —— 阶段5（P5-②1）：cases.status 语义清理 ——
# cases.status 只承载「用例生命周期状态」，与执行结果（runs.status）解耦，
# 避免监控/趋势把「未执行」与「失败」混为一谈。取值：
#   generated  新生成（尚未/刚生成，未参与对账）
#   updated    已更新——代码变更导致对应用例被修订（增量对账结果）
#   obsolete   已废弃——原用例对应的功能点被移除或不再需要
#   archived   软删除——保留历史 runs 不被悬挂，查询默认排除
# 执行结论（pass/fail/structural_only/blocked_auth/error/skipped/blocked_review）
# 只写 runs.status，并冗余到 cases.last_result 供快速查看。
CASE_LIFECYCLE_STATUS = {"generated", "updated", "obsolete", "archived"}


class Executor:
    # 长事务保护：每执行 N 条提交一次，避免数百条共用一个事务；
    # 即便中途抛出未捕获异常，finally 也会补提交，已执行结果不丢（D-★4）。
    COMMIT_EVERY = 50
    _LOCAL = threading.local()  # 每线程独立 Session：requests.Session 非线程安全（D-②2）
    _AUTH_LOCK = threading.Lock()  # token 刷新只允许整轮一次，且需跨线程互斥（D-②1）
    # 允许的筛选字段白名单：防止任意列名拼进 SQL
    FILTER_FIELDS = {
        "priority",
        "module",
        "case_type",
        "test_type",
        "ctype",
        "ids",
        "fp_contract_id",
        "tp_id",
        "review_status",
    }

    def __init__(self):
        self.last_batch_id = None
        self.last_meta = {}

    def _new_batch_id(self, pid: int) -> str:
        """一次执行 = 一个批次（D-★5）。时间戳 + 短随机，保证同秒多轮也可区分。"""
        ts = time.strftime("%Y%m%d_%H%M%S")
        return f"run_{pid}_{ts}_{uuid.uuid4().hex[:6]}"

    # —— 阶段5（D-②6 / P5-②5）：进度注册与中断 ——
    def register_batch(self, batch_id, pid, total, filters, webhook_url=""):
        """执行开始即在注册表登记（供实时查询）并同步落库（P5-②5 持久化）。"""
        with _BATCH_REGISTRY_LOCK:
            _BATCH_REGISTRY[batch_id] = {
                "batch_id": batch_id,
                "project_id": pid,
                "total": total,
                "done": 0,
                "status_counts": {},
                "state": "running",
                "cancelled": False,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "finished_at": None,
                "filters": filters or {},
                ExecStatus.ERROR.value: None,
                "webhook_url": webhook_url or "",
                "live": True,
            }
        bs_mod.upsert(batch_id, pid, total, filters, webhook_url=webhook_url, state="running")

    def update_progress(self, batch_id, status):
        """每执行完一条用例，推进进度计数（D-②6），并同步落库（P5-②5）。"""
        with _BATCH_REGISTRY_LOCK:
            e = _BATCH_REGISTRY.get(batch_id)
            if not e:
                return
            e["done"] += 1
            e["status_counts"][status] = e["status_counts"].get(status, 0) + 1
        bs_mod.inc_progress(batch_id, status)

    def finish_batch(self, batch_id, state="done", error=None):
        """执行结束（正常/中断/异常）写入终态（D-②6），并同步落库（P5-②5）。"""
        with _BATCH_REGISTRY_LOCK:
            e = _BATCH_REGISTRY.get(batch_id)
            if not e:
                return
            e["state"] = state
            e["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            if error:
                e[ExecStatus.ERROR.value] = error
        bs_mod.set_state(batch_id, state, error=error)

    def cancel_batch(self, batch_id):
        """请求中断某一轮执行（D-②6）：执行循环在下一条/下一个分块边界退出。"""
        with _CANCEL_LOCK:
            _CANCEL_SET.add(batch_id)
        with _BATCH_REGISTRY_LOCK:
            e = _BATCH_REGISTRY.get(batch_id)
            if e and e["state"] == "running":
                e["cancelled"] = True

    def is_cancelled(self, batch_id):
        with _CANCEL_LOCK:
            return batch_id in _CANCEL_SET

    def get_batch_status(self, batch_id):
        """返回某批次进度快照：优先 registry（进行中/刚结束，live=True），
        不在注册表（已结束/进程重启）则回退 run_batches 持久化表（live=False）。"""
        with _BATCH_REGISTRY_LOCK:
            e = _BATCH_REGISTRY.get(batch_id)
            if e:
                return dict(e)
        return bs_mod.get(batch_id)

    def active_batches(self):
        """返回当前仍在进行（running/queued）的批次列表（D-②6）。"""
        with _BATCH_REGISTRY_LOCK:
            return [
                dict(e) for e in _BATCH_REGISTRY.values() if e["state"] in ("running", "queued")
            ]

    def all_tasks(self, pid=None):
        """返回全部任务（含已结束，P5-★4 异步任务化可见性）。

        以 run_batches 持久化表为主（含跨重启的历史），叠加注册表中仍在进行中
        的 live 进度（实时 done/total）。"""
        items = bs_mod.list_all(pid)
        with _BATCH_REGISTRY_LOCK:
            live = {
                e["batch_id"]: e
                for e in _BATCH_REGISTRY.values()
                if e["state"] in ("running", "queued")
            }
        out = []
        for it in items:
            b = it["batch_id"]
            if b in live:
                out.append(live[b])
            else:
                out.append(it)
        # 极少数尚未落库但已在 registry 的 live 批次（保底）
        for b, e in live.items():
            if not any(x["batch_id"] == b for x in out):
                out.append(e)
        return sorted(out, key=lambda e: e.get("started_at") or "", reverse=True)

    @staticmethod
    def fire_webhook(url, payload, timeout=5):
        """执行结束回调（P5-★4）：best-effort POST JSON；失败静默吞掉不阻塞主流程。

        用独立 Session + trust_env=False，避免本机透明代理把回调用流量劫持到 127.0.0.1。
        """
        if not url:
            return False
        try:
            import json as _json

            import requests
            from requests.adapters import HTTPAdapter

            s = requests.Session()
            s.trust_env = False
            s.proxies = {"http": None, "https": None}
            s.mount("http://", HTTPAdapter(pool_connections=2, pool_maxsize=4))
            s.mount("https://", HTTPAdapter(pool_connections=2, pool_maxsize=4))
            r = s.post(
                url,
                data=_json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )
            return 200 <= r.status_code < 500
        except Exception:
            return False

    # —— 批次3（D-★6）：执行子集筛选 ——

    def build_filter(self, pid: int, filters=None, include_archived: bool = False):
        """把 filters 编译成 (where_sql, params)。未知字段直接报错，避免脏列名进 SQL。"""
        f = filters or {}
        unknown = [k for k in f if k not in self.FILTER_FIELDS]
        if unknown:
            raise ValueError(f"不支持的筛选字段: {unknown}，可选: {sorted(self.FILTER_FIELDS)}")
        where, params = ["project_id=?"], [pid]
        if not include_archived:
            # 正常执行排除软删(archived)与代码已废弃(obsolete)用例：
            # 后者由 C-②8 对账置位，对应功能点已移除，再跑无意义。
            where.append("status NOT IN ('archived','obsolete')")
        for key in (
            "priority",
            "module",
            "case_type",
            "test_type",
            "ctype",
            "fp_contract_id",
            "tp_id",
            "review_status",
        ):
            val = f.get(key)
            if not val:
                continue
            vals = val if isinstance(val, (list, tuple)) else [val]
            where.append(f"{key} IN ({','.join('?' * len(vals))})")
            params.extend(vals)
        if f.get("ids"):
            vals = list(f["ids"])
            where.append(f"id IN ({','.join('?' * len(vals))})")
            params.extend(vals)
        return " AND ".join(where), params

    def select_cases(self, pid: int, filters=None, include_archived: bool = False, limit: int = 0):
        """按筛选条件取待执行用例（D-★6）。返回 (cases, where_sql)。"""
        where, params = self.build_filter(pid, filters, include_archived)
        sql = f"SELECT * FROM cases WHERE {where} ORDER BY id"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        cases = [dict(r) for r in cur.fetchall()]
        conn.close()
        return cases, where

    def run_project(
        self,
        pid: int,
        filters=None,
        max_workers: int | None = None,
        use_browser: bool | None = None,
        include_archived: bool = False,
        limit: int = 0,
        batch_id: str | None = None,
        webhook_url: str | None = None,
        preferred_layer: str | None = None,
    ):
        """执行一轮测试。

        - preferred_layer：执行层偏好（VerifyLayer 取值，"接口"/"UI"）；
          None → 沿用每条用例自带的 verify_layer；UI 优先但无法覆盖时自动回退接口层。
        """
        """执行一轮测试。

        - filters：{'priority': ['P1'], 'test_type': '新增', 'module': [...], 'ids': [...]} 等
        - max_workers：并发度；1 或 None 受 settings.EXEC_MAX_WORKERS 控制
        - use_browser：是否启用真实浏览器（page 类）；None → 取 settings.ENABLE_BROWSER
        - batch_id：可外部指定（异步模式下由端点预生成，便于立即返回并轮询进度）
        """
        cases, where_sql = self.select_cases(pid, filters, include_archived, limit)
        proj = pm.get(pid) or {}
        # 单次探活（仅当开关开启），缓存结果供所有 case 复用
        service_up = self._service_check(proj) if settings.ENABLE_DYNAMIC_PROBE else False

        # 批次3（D-②1）：鉴权态；仅在服务可达时取，避免无谓登录
        auth_headers, auth_info = (
            {},
            {"source": ExecStatus.SKIPPED.value, "reason": "服务不可达，跳过登录"},
        )
        if service_up:
            auth_headers, auth_info = auth_mod.auth_headers(proj)

        # 批次4（D-★3）：浏览器可用性
        browser_on, browser_reason = self._prepare_browser(use_browser)

        ctx = {
            "service_up": service_up,
            "auth_headers": auth_headers,
            "auth_enabled": bool(auth_headers),
            "browser_on": browser_on,
            "browser_reason": browser_reason,
            "_auth_refreshed": False,
        }

        workers = max_workers if max_workers is not None else settings.EXEC_MAX_WORKERS
        workers = max(1, min(int(workers or 1), 16))

        # 本轮批次号：贯穿本轮所有 runs，供 reporter 关联 reports（D-★5）
        batch_id = batch_id or self._new_batch_id(pid)
        self.last_batch_id = batch_id
        self.last_meta = {
            "batch_id": batch_id,
            "requested": len(cases),
            "filters": filters or {},
            "where": where_sql,
            "workers": workers,
            "service_up": service_up,
            "auth": auth_info,
            "browser_on": browser_on,
            "browser_reason": browser_reason,
        }
        # 阶段5（D-②6）：执行开始即登记进度，供 /execute/status 实时查询
        # P5-②5：进度同步持久化到 run_batches 表（跨重启可查、可触发 webhook 中断回调）
        self.register_batch(batch_id, pid, len(cases), filters, webhook_url=webhook_url)

        results = []
        conn = get_conn()
        cur = conn.cursor()
        state = "done"
        try:
            if workers <= 1 or len(cases) <= 1:
                # 串行：逐条执行 + 逐条写库（崩溃时已执行部分全部保住）
                for _idx, c in enumerate(cases, 1):
                    if self.is_cancelled(batch_id):
                        state = "cancelled"
                        break
                    res = self._safe_run(
                        c,
                        proj,
                        ctx,
                        service_up,
                        preferred_layer=preferred_layer,
                        ui_available=browser_on,
                    )
                    self._persist(cur, pid, c, res, batch_id)
                    # 先提交主事务，释放写锁，再让 batch_store 进度落库（P5-②5，避免锁冲突）
                    conn.commit()
                    self.update_progress(batch_id, res["status"])
                    results.append(res)
            else:
                # 并发：分批「并发执行 → 顺序写库」，写库留在主线程规避 SQLite 写锁
                for start in range(0, len(cases), self.COMMIT_EVERY):
                    if self.is_cancelled(batch_id):
                        state = "cancelled"
                        break
                    chunk = cases[start : start + self.COMMIT_EVERY]
                    with ThreadPoolExecutor(max_workers=workers) as pool:
                        futs = [
                            pool.submit(
                                self._safe_run,
                                c,
                                proj,
                                ctx,
                                service_up,
                                preferred_layer,
                                browser_on,
                            )
                            for c in chunk
                        ]
                        chunk_res = [f.result() for f in futs]
                    for c, res in zip(chunk, chunk_res, strict=False):
                        self._persist(cur, pid, c, res, batch_id)
                    # 提交主事务后，再批量推进进度（batch_store 独立连接写 run_batches 表）
                    conn.commit()
                    for res in chunk_res:
                        self.update_progress(batch_id, res["status"])
                    results.extend(chunk_res)
        except Exception as e:
            state = ExecStatus.ERROR.value
            self.finish_batch(
                batch_id, state=ExecStatus.ERROR.value, error=f"{type(e).__name__}: {str(e)[:200]}"
            )
            raise
        finally:
            # 无论正常结束还是中途异常，已执行的部分都必须落库（D-★4）
            conn.commit()
            conn.close()
        if self.is_cancelled(batch_id):
            state = "cancelled"
        self.finish_batch(batch_id, state=state)
        return results

    @staticmethod
    def _persist(cur, pid, c, res, batch_id):
        res["case_id"] = c["id"]
        res["ctype"] = c["ctype"]
        res["batch_id"] = batch_id
        cur.execute(
            """INSERT INTO runs (project_id, case_id, batch_id, status, screenshot_path,
                                 log_path, duration_ms)
               VALUES (?,?,?,?,?,?,?)""",
            (
                pid,
                c["id"],
                batch_id,
                res["status"],
                res.get("screenshot_path"),
                res.get("log", ""),
                res.get("duration_ms", 0),
            ),
        )
        # P5-②1：执行结论只写 runs.status（每轮一份），并冗余到 cases.last_result
        # 供快速查看；**绝不回写 cases.status**（那是生命周期状态，避免语义混淆）。
        cur.execute("UPDATE cases SET last_result=? WHERE id=?", (res["status"], c["id"]))

    def _safe_run(self, c, proj, ctx, service_up, preferred_layer=None, ui_available=False):
        """单条执行 + 异常隔离（D-★4）。

        执行层决策（VerifyLayer）：按「用户偏好 preferred_layer / 用例自带 verify_layer」
        + 测试点来源 ftype + UI 可用性，由 select_execution_mode 决定实际执行层；
        UI 优先但测试点本质是接口型或无浏览器时自动回退接口层，并记录 layer_fallback。
        """
        # —— 执行层推导 ——
        ftype = c.get("ftype") or (
            method_kind(c.get("method")) if c.get("method") else FType.BUSINESS.value
        )
        pref = preferred_layer or c.get("verify_layer") or derive_verify_layer(ftype).value
        try:
            pref_enum = VerifyLayer(pref)
        except ValueError:
            pref_enum = VerifyLayer.INTERFACE
        actual = select_execution_mode(pref_enum, ftype, bool(ui_available))
        layer_fallback = actual != pref_enum

        if settings.REVIEW_GATE and c.get("review_status") != "approved":
            return {
                "status": ExecStatus.BLOCKED_REVIEW.value,
                "reason": f"review_gate: status={c.get('review_status')}",
                "log": "用例未通过人工审核，按设计意图跳过执行",
                "layer": actual.value,
                "layer_fallback": layer_fallback,
            }
        t0 = time.time()
        try:
            res = self._run_case(c, proj, service_up, ctx)
            res.setdefault("duration_ms", int((time.time() - t0) * 1000))
        except Exception as e:
            res = {
                "status": ExecStatus.ERROR.value,
                "reason": f"executor_error: {type(e).__name__}: {str(e)[:200]}",
                "log": f"用例执行器内部异常：{type(e).__name__}: {str(e)[:200]}",
                "duration_ms": int((time.time() - t0) * 1000),
            }
        res.setdefault("layer", actual.value)
        res["layer_fallback"] = layer_fallback
        return res

    @staticmethod
    def _prepare_browser(use_browser):
        """批次4（D-★3）：决定是否启用浏览器。返回 (enabled, reason)。"""
        if use_browser is None:
            use_browser = settings.ENABLE_BROWSER
        if not use_browser:
            return False, "ENABLE_BROWSER=off（未启用真实浏览器）"
        ok_avail, reason = browser_mod.available()
        if not ok_avail:
            return False, reason
        return True, "playwright 可用"

    @classmethod
    def _session(cls):
        """HTTP 会话：禁用系统代理与 trust_env，每线程一份。

        本机存在透明代理，若沿用 requests 默认行为，127.0.0.1 的探测会被代理拦截而假性失败；
        并发执行（D-②2）下 Session 不能跨线程共享，故用 thread-local 各持一份并复用连接。
        """
        s = getattr(cls._LOCAL, "session", None)
        if s is None:
            import requests
            from requests.adapters import HTTPAdapter

            s = requests.Session()
            s.trust_env = False  # 忽略 HTTP(S)_PROXY 等环境变量
            s.proxies = {"http": None, "https": None}
            s.mount("http://", HTTPAdapter(pool_connections=8, pool_maxsize=16))
            s.mount("https://", HTTPAdapter(pool_connections=8, pool_maxsize=16))
            cls._LOCAL.session = s
        return s

    @staticmethod
    def _base(proj) -> str:
        """被测根地址：localhost 会解析到 IPv6(::1) 导致超时，统一改 127.0.0.1。"""
        return (proj.get("base_url") or "").rstrip("/").replace("localhost", "127.0.0.1")

    def _service_check(self, proj):
        base = self._base(proj)
        if not base:
            return False
        try:
            r = self._session().get(base + "/health", timeout=3)
            return r.status_code < 500
        except Exception:
            return False

    # —— 预期（expect）解析与校验（D-★2）——

    @staticmethod
    def _expected(expect: str):
        """从自然语言 expect 解析期望状态码，贴合阶段 2 实际产物。

        支持三类：
          - 显式码：`→ 404` / `-> 404`
          - 状态码段：`（2xx）` / `(4xx)` / `（5xx）`
          - 语义兜底：资源不存在/非法/越权 → 4xx；功能可用/可正常触发 → 2xx
        返回 (kind, value)：kind ∈ {'code','band','unknown'}。
        """
        e = expect or ""
        m = re.search(r"(?:→|->)\s*(\d{3})", e)
        if m:
            return "code", int(m.group(1))
        m = re.search(r"[（(]\s*([2-5])\s*xx\s*[)）]", e)
        if m:
            return "band", int(m.group(1))
        if "资源不存在" in e or "不存在或非法的" in e:
            return "band", 4
        if any(k in e for k in ("非法", "无效", "越权", "未授权", "拒绝", "超长", "越界")):
            return "band", 4
        if "功能可用" in e or "可正常触发" in e or "逻辑正确" in e:
            return "band", 2
        return "unknown", None

    def _check_expect(self, expect: str, code: int):
        """按 expect 校验真实响应码，异常维度走**反向断言**（期望被拒绝）。"""
        kind, val = self._expected(expect)
        if kind == "code":
            return code == val, f"期望 HTTP {val}（来自 expect），实际 {code}"
        if kind == "band":
            return (code // 100) == val, f"期望 {val}xx（来自 expect），实际 {code}"
        return 200 <= code < 400, f"expect 无明确状态码预期，按 2xx/3xx 判定，实际 {code}"

    @staticmethod
    def _expect_is_error(expect: str) -> bool:
        kind, val = Executor._expected(expect)
        return (kind == "code" and 400 <= val < 500) or (kind == "band" and val == 4)

    @staticmethod
    def _fill_path(path: str, expect_error: bool) -> str:
        """路径占位符填充（C-②6 前置）：`/x/{tid}` 正常场景填 1，异常场景填 nonexistent 以触发拒绝。"""
        return re.sub(r"\{[^}]+\}", "nonexistent" if expect_error else "1", path or "")

    @staticmethod
    def _route_defined(text, method, path) -> bool:
        """路由结构断言（收紧兜底，D-★1）：

        不再接受裸子串命中——此前 `path in text` 会让"路径只出现在注释里"也判 pass。
        """
        if not text:
            return False
        m, p = re.escape((method or "").lower()), re.escape(path or "")
        if re.search(r"[\.@]\s*" + m + r'\s*\(\s*["\']' + p + r'["\']', text, re.I):
            return True  # .get("/x") / @app.post('/x')
        return bool(re.search(r'["\']' + p + r'["\']', text))  # 路径被引号包裹出现

    def _run_case(self, c, proj, service_up, ctx=None):
        steps = json.loads(c["steps"]) if c.get("steps") else []
        step = steps[0] if steps else {}
        action = step.get("action")
        if action == "http_probe":
            return self._api_probe(step, proj, service_up, ctx)
        if action == "route_assert":
            return self._route_assert(step, proj)
        if action == "component_assert":
            return self._component_assert(step, proj)
        if action == "ui_probe":
            return self._ui_probe(step, proj, ctx)
        return {"status": ExecStatus.SKIPPED.value, "reason": "no executable step", "log": ""}

    def _ui_probe(self, step, proj, ctx=None):
        """前端/业务函数类用例的执行。

        page 类（批次4 · D-★3）：启用浏览器时做**真实渲染断言**并失败自动截图；
        浏览器不可用则降级为静态路由断言，并在 reason 里写明降级原因。
        component / business：仍为静态断言（`structural_only`）。
        """
        kind = step.get("kind")
        if kind == FType.PAGE.value:
            ctx = ctx or {}
            if ctx.get("browser_on"):
                return self._browser_page(step, proj)
            res = self._route_assert(step, proj)
            if res.get("status") == ExecStatus.STRUCTURAL_ONLY.value:
                res["reason"] += (
                    f"；未启用浏览器（{ctx.get('browser_reason', 'ENABLE_BROWSER=off')}）"
                )
            return res
        if kind == FType.COMPONENT.value:
            return self._component_assert(step, proj)
        if kind == FType.BUSINESS.value:
            text = self._read(proj, step.get("file"))
            func = step.get("func", "")
            if text is None:
                return {
                    "status": ExecStatus.FAIL.value,
                    "reason": f"file missing: {step.get('file')}",
                    "log": f"file missing {step.get('file')}",
                }
            ok = (f"def {func}" in text) or (f"async def {func}" in text) or (func in text)
            if not ok:
                return {
                    "status": ExecStatus.FAIL.value,
                    "reason": f"function {func} not found",
                    "log": f"func {func} missing",
                }
            # 函数"存在"≠ 逻辑正确：真实校验需调用该函数（D-★3 之后的业务级执行）
            return {
                "status": ExecStatus.STRUCTURAL_ONLY.value,
                "reason": f"业务函数 {func} 已定义（静态断言），未做真实逻辑验证",
                "log": f"func {func} found (static only)",
            }
        return {"status": ExecStatus.SKIPPED.value, "reason": "unknown ui_probe kind", "log": ""}

    def _page_url(self, proj, path: str) -> str:
        """page 类用例的真实访问地址：优先前端地址，回退后端 base_url。"""
        base = (settings.RA_FRONTEND_URL or proj.get("base_url") or "").rstrip("/")
        base = base.replace("localhost", "127.0.0.1")
        p = path if (path or "").startswith("/") else "/" + (path or "")
        return base + p

    def _browser_page(self, step, proj):
        """真实浏览器渲染断言（D-★3）：失败自动截图并写入 runs.screenshot_path。"""
        url = self._page_url(proj, step.get("path"))
        name = step.get("tc_no") or step.get("tp_id") or FType.PAGE.value
        rep = browser_mod.check_page(url, name=name)
        if rep.get(ExecStatus.SKIPPED.value):
            # 依赖缺失/启动超时 → 降级为静态断言，绝不因环境问题中断整轮
            res = self._route_assert(step, proj)
            res["browser_error"] = rep.get(ExecStatus.ERROR.value)
            res["browser_unavailable"] = True
            res["reason"] = (
                res.get("reason") or ""
            ) + f"；浏览器不可用已降级为静态断言（{rep.get(ExecStatus.ERROR.value)}）"
            return res
        ok = bool(rep.get("ok"))
        return {
            "status": ExecStatus.PASS.value if ok else ExecStatus.FAIL.value,
            "screenshot_path": rep.get("screenshot_path"),
            "browser": {
                "url": url,
                "http_status": rep.get("status"),
                "title": rep.get("title"),
                "text_len": rep.get("text_len"),
                "elapsed_ms": rep.get("elapsed_ms"),
            },
            "reason": (
                f"真实浏览器渲染通过（HTTP {rep.get('status')}，标题「{rep.get('title')}」）"
                if ok
                else f"真实浏览器渲染未通过：HTTP {rep.get('status')}、"
                f"标题「{rep.get('title')}」、可见文本 {rep.get('text_len')} 字"
            ),
            "log": f"browser={url} status={rep.get('status')} "
            f"title={rep.get('title')} shot={rep.get('screenshot_path')}",
        }

    def _read(self, proj, fpath):
        if not fpath:
            return None
        root = Path(proj.get("local_path", ""))
        full = root / fpath
        if not full.exists():
            return None
        try:
            return full.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    def _api_probe(self, step, proj, service_up, ctx=None):
        """API 用例判定（D-★1 + D-★2 + D-②1）。

        - 服务可达：以**真实 HTTP 响应**为主判定，按 expect 校验（异常维度走反向断言）；
        - 携带鉴权态（D-②1）；首次 401/403 会强制刷新 token 并**仅重试一次**，
          仍被拒才判 `blocked_auth`；
        - 服务不可达/未开动态探测：降级为静态路由断言，状态标 `structural_only`
          （明确"未真测"，不再伪装成 pass）；静态都没命中才判 fail。
        """
        ctx = ctx or {}
        text = self._read(proj, step.get("file"))
        method = (step.get("method") or "GET").upper()
        raw_path = step.get("path") or ""
        expect = step.get("expect") or ""
        struct_ok = self._route_defined(text, method, raw_path)
        head = f"structural={'ok' if struct_ok else 'missing'}"
        path = self._fill_path(raw_path, self._expect_is_error(expect))

        if not service_up:
            if not struct_ok:
                return {
                    "status": ExecStatus.FAIL.value,
                    "structural_ok": False,
                    "dynamic": None,
                    "reason": "源码中未找到该路由定义",
                    "log": f"{head}; dynamic=unavailable",
                }
            return {
                "status": ExecStatus.STRUCTURAL_ONLY.value,
                "structural_ok": True,
                "dynamic": None,
                "reason": "服务不可达或动态探测未开启：仅完成静态路由断言，未做真实请求",
                "log": f"{head}; dynamic=unavailable",
            }

        headers = dict(ctx.get("auth_headers") or {})
        dyn = self._http_probe(proj, method, path, headers=headers)
        code = dyn.get("status_code")
        if code is None:
            return {
                "status": ExecStatus.STRUCTURAL_ONLY.value,
                "structural_ok": struct_ok,
                "dynamic": dyn,
                "reason": f"动态请求未成功：{str(dyn.get(ExecStatus.ERROR.value))[:80]}",
                "log": f"{head}; dynamic=error",
            }
        if code in (401, 403):
            # 批次3（D-②1）：有机会是 token 过期 → 强制刷新后重试一次
            refreshed = self._try_refresh_auth(proj, ctx)
            if refreshed:
                dyn = self._http_probe(proj, method, path, headers=refreshed)
                code = dyn.get("status_code")
                if code is not None and code not in (401, 403):
                    ok, why = self._check_expect(expect, code)
                    return {
                        "status": ExecStatus.PASS.value if ok else ExecStatus.FAIL.value,
                        "structural_ok": struct_ok,
                        "dynamic": dyn,
                        "auth": "refreshed",
                        "reason": why,
                        "log": f"{head}; dynamic={code}; auth=refreshed; {why}",
                    }
            # 未携带鉴权态或刷新后仍被拒：既不算被测失败，也不能算通过
            return {
                "status": ExecStatus.BLOCKED_AUTH.value,
                "structural_ok": struct_ok,
                "dynamic": dyn,
                "reason": (
                    f"需要鉴权态（HTTP {code}）"
                    f"{'：已刷新 token 仍被拒' if refreshed else '：当前执行未携带有效 token'}"
                ),
                "log": f"{head}; dynamic={code}",
            }
        ok, why = self._check_expect(expect, code)
        res = {
            "status": ExecStatus.PASS.value if ok else ExecStatus.FAIL.value,
            "structural_ok": struct_ok,
            "dynamic": dyn,
            "reason": why,
            "log": f"{head}; dynamic={code}; {why}",
        }
        if headers:
            res["auth"] = "bearer"
        return res

    @staticmethod
    def _try_refresh_auth(proj, ctx):
        """401/403 后强制刷新 token；整轮**只刷新一次**，返回新 headers 或 None。"""
        if not ctx.get("auth_enabled"):
            return None
        with Executor._AUTH_LOCK:
            if ctx.get("_auth_refreshed"):
                return None
            ctx["_auth_refreshed"] = True
            headers, info = auth_mod.auth_headers(proj, force_refresh=True)
        if headers:
            ctx["auth_headers"] = headers
            return headers
        ctx["auth_info"] = info
        return None

    def _http_probe(self, proj, method, path, headers=None):
        base = self._base(proj)
        if not base:
            return {ExecStatus.ERROR.value: "项目未配置 base_url，无法发起动态请求"}
        try:
            r = self._session().request(method, base + path, timeout=5, headers=headers or None)
            return {"status_code": r.status_code, "snippet": (r.text or "")[:200]}
        except Exception as e:
            return {ExecStatus.ERROR.value: f"{type(e).__name__}: {str(e)[:120]}"}

    def _route_assert(self, step, proj):
        """前端路由断言。

        静态命中 ≠ 路由真实可达：真实可达性需浏览器/HTTP 实测（D-★3），
        因此命中时标注 `structural_only`，未命中才是确定的 fail。
        """
        text = self._read(proj, step.get("file"))
        p = step.get("path", "")
        if text is None:
            return {
                "status": ExecStatus.FAIL.value,
                "reason": f"file missing: {step.get('file')}",
                "log": f"file missing {step.get('file')}",
            }
        ok = (
            (f'"{p}"' in text)
            or (f"'{p}'" in text)
            or (f'path: "{p}"' in text)
            or (f"path: '{p}'" in text)
            or (p in text)
        )
        if not ok:
            return {
                "status": ExecStatus.FAIL.value,
                "reason": f"route {p} not found",
                "log": f"route {p} missing",
            }
        return {
            "status": ExecStatus.STRUCTURAL_ONLY.value,
            "reason": f"路由 {p} 在源码中存在（静态断言），未做真实可达性验证",
            "log": f"route {p} found (static only)",
        }

    def _component_assert(self, step, proj):
        """交互元素断言：命中仍为 `structural_only`——真实交互需浏览器验证（D-★3）。"""
        text = self._read(proj, step.get("file"))
        if text is None:
            return {
                "status": ExecStatus.FAIL.value,
                "reason": f"file missing: {step.get('file')}",
                "log": f"file missing {step.get('file')}",
            }
        ok = bool(re.search(r"(@click|v-on|<button|el-button|upload|<form|input)", text, re.I))
        if not ok:
            return {
                "status": ExecStatus.FAIL.value,
                "reason": "no interactive element",
                "log": "interactive=no",
            }
        return {
            "status": ExecStatus.STRUCTURAL_ONLY.value,
            "reason": "源码含交互钩子（静态断言），未做真实交互验证",
            "log": "interactive=yes (static only)",
        }


executor = Executor()
