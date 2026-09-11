"""阶段4 批次2 自测：D-★1（动态结果参与判定）+ D-★2（expect/异常反向断言）。

用本地 mock HTTP 服务做**可控真实请求**，验证判定不再靠源码字符串匹配：

 B4-2-1  expect 解析：`→ 404` / `（2xx）` / 语义兜底 / 无预期 四类均正确
 B4-2-2  结构断言收紧：路径仅出现在注释里不再判命中（旧 `path in text` 假阳性已消除）
 B4-2-3  动态判定生效：正常 expect+200→pass、+500→fail；401→blocked_auth
 B4-2-4  异常反向断言：期望 404 实际 404→pass；期望 404 实际 200→fail（非法输入未被拦截）
 B4-2-5  占位符填充：`/x/{tid}` 正常填 1、异常填 nonexistent（C-②6 前置）
 B4-2-6  服务不可达：静态命中也只标 structural_only，不再伪装成 pass
 B4-2-7  报告统计：structural_only / blocked_auth 正确入 summary，真实通过率口径正确
 B4-2-8  集成回归：默认配置下 263 条，**pass==0**（不再有虚假通过），且无 error
"""

import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import backend.db as db
from backend.config import PROJECT_ROOT
from backend.main import _analyze_project, bulk_review
from backend.modules import tp_store
from backend.modules.case_generator import case_generator
from backend.modules.executor import Executor, executor
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


TARGET = PROJECT_ROOT.parent / "targets" / "research-agent"

_results = []
RECEIVED = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


# ---------- mock 被测服务 ----------
class Handler(BaseHTTPRequestHandler):
    def _handle(self):
        RECEIVED.append(self.path)
        p = self.path
        if p.startswith("/notfound") or p.startswith("/threads/nonexistent"):
            code = 404
        elif p.startswith("/boom"):
            code = 500
        elif p.startswith("/secret"):
            code = 401
        else:
            code = 200
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    do_GET = do_POST = _handle

    def log_message(self, *a):
        pass


def start_mock():
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main():
    t0 = time.time()
    db.init_db()
    srv, port = start_mock()
    proj = {"base_url": f"http://127.0.0.1:{port}", "local_path": str(TARGET)}
    print(f"[mock] 被测服务 http://127.0.0.1:{port}")

    OK_EXPECT = "功能可用：GET /ok 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整"
    ERR_EXPECT = "资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节"

    # ---------- B4-2-1 expect 解析 ----------
    ex = Executor._expected
    check(
        "B4-2-1 expect 解析：显式码/状态段/语义兜底/无预期 四类均正确",
        ex(ERR_EXPECT) == ("code", 404)
        and ex(OK_EXPECT) == ("band", 2)
        and ex("资源不存在：XXX") == ("band", 4)
        and ex("越权访问应被拒绝") == ("band", 4)
        and ex("随便一段描述") == ("unknown", None),
        f"{ex(ERR_EXPECT)}, {ex(OK_EXPECT)}, {ex('随便一段描述')}",
    )

    # ---------- B4-2-2 结构断言收紧 ----------
    tmp = Path(tempfile.mkdtemp())
    (tmp / "app.py").write_text('@app.get("/ok")\ndef ok(): pass\n', encoding="utf-8")
    (tmp / "comment.py").write_text("# 这里只是注释提到 /ghost 路径\nx = 1\n", encoding="utf-8")
    rd = Executor._route_defined
    check(
        "B4-2-2 结构断言收紧：路径仅出现在注释中不再判命中（消除假阳性）",
        rd("# 注释提到 /ghost", "GET", "/ghost") is False,
        "旧逻辑 `path in text` 会误判为 True",
    )
    check(
        "B4-2-2b 真实路由装饰器仍可正确命中",
        rd('@app.get("/ok")\ndef ok(): pass', "GET", "/ok") is True,
    )

    # ---------- B4-2-3 动态判定 ----------
    def probe(path, expect, method="GET", p=None):
        return executor._api_probe(
            {
                "action": "http_probe",
                "method": method,
                "path": path,
                "file": "app.py",
                "expect": expect,
            },
            p or proj,
            True,
        )

    r_ok = probe("/ok", OK_EXPECT)
    r_500 = probe("/boom", OK_EXPECT)
    r_401 = probe("/secret", OK_EXPECT)
    check(
        "B4-2-3 动态判定生效：正常 expect + 200 → pass",
        r_ok["status"] == "pass",
        r_ok.get("reason", ""),
    )
    check(
        "B4-2-3b 动态判定生效：正常 expect + 500 → fail（不再被静态断言掩盖）",
        r_500["status"] == "fail",
        r_500.get("reason", ""),
    )
    check(
        "B4-2-3c 401/403 → blocked_auth（缺鉴权态，不计失败也不计通过）",
        r_401["status"] == "blocked_auth",
        r_401.get("reason", ""),
    )

    # ---------- B4-2-4 异常反向断言 ----------
    r_e404 = probe("/notfound", ERR_EXPECT)
    r_e200 = probe("/ok", ERR_EXPECT)
    check(
        "B4-2-4 异常反向断言：期望 404 实际 404 → pass（异常维度被真正验证）",
        r_e404["status"] == "pass",
        r_e404.get("reason", ""),
    )
    check(
        "B4-2-4b 异常反向断言：期望 404 实际 200 → fail（非法输入未被拦截）",
        r_e200["status"] == "fail",
        r_e200.get("reason", ""),
    )

    # ---------- B4-2-5 占位符填充 ----------
    RECEIVED.clear()
    r_norm = probe("/threads/{tid}", OK_EXPECT)
    r_err = probe("/threads/{tid}", ERR_EXPECT)
    check(
        "B4-2-5 占位符填充：正常场景填 1、异常场景填 nonexistent 以触发拒绝（C-②6 前置）",
        "/threads/1" in RECEIVED
        and "/threads/nonexistent" in RECEIVED
        and r_norm["status"] == "pass"
        and r_err["status"] == "pass",
        f"实际请求路径={RECEIVED[-2:]}",
    )

    # ---------- B4-2-6 服务不可达降级 ----------
    local_proj = {"base_url": f"http://127.0.0.1:{port}", "local_path": str(tmp)}
    r_static = executor._api_probe(
        {
            "action": "http_probe",
            "method": "GET",
            "path": "/ok",
            "file": "app.py",
            "expect": OK_EXPECT,
        },
        local_proj,
        False,
    )
    check(
        "B4-2-6 服务不可达：静态命中也只标 structural_only（不再伪装成 pass）",
        r_static["status"] == "structural_only",
        r_static.get("reason", ""),
    )

    # ---------- B4-2-7 报告统计 ----------
    fake = (
        [{"status": "pass", "ctype": "api"}] * 3
        + [{"status": "fail", "ctype": "api"}]
        + [{"status": "structural_only", "ctype": "e2e"}] * 5
        + [{"status": "blocked_auth", "ctype": "api"}] * 2
        + [{"status": "error", "ctype": "api"}]
    )
    rep = reporter.build(999, fake, meta={"project": "mock"})
    s = rep["summary"]
    check(
        "B4-2-7 报告统计：structural_only/blocked_auth/error 正确入 summary",
        s["structural_only"] == 5
        and s["blocked_auth"] == 2
        and s["error"] == 1
        and s["pass"] == 3
        and s["fail"] == 1,
        f"pass={s['pass']} fail={s['fail']} 静态={s['structural_only']} 鉴权={s['blocked_auth']}",
    )
    check(
        "B4-2-7b 真实通过率口径：分母只算真实执行并有结论的用例（4 而非 12）",
        s["effective_total"] == 4,
        f"effective_total={s['effective_total']}, total={s['total']}",
    )

    # ---------- B4-2-8 集成回归 ----------
    if not pm.find_by_name("research-agent"):
        pm.add(
            name="research-agent",
            local_path=str(TARGET),
            type="pc",
            base_url="http://localhost:8010",
        )
    pid = pm.find_by_name("research-agent")["id"]
    conn = db.get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    conn.commit()
    conn.close()

    _analyze_project(pid)
    tp_store.import_test_points(pid)
    case_generator.generate_for_project(pid)
    bulk_review(pid, type("R", (), {"action": "approve", "comment": "b4", "ids": None})())
    res = executor.run_project(pid)

    def c(st):
        return sum(1 for r in res if r["status"] == st)

    check(
        "B4-2-8 集成回归：默认配置下 pass==0（263 条虚假通过已消除）",
        len(res) == 263 and c("pass") == 0,
        f"pass={c('pass')} 静态={c('structural_only')} fail={c('fail')}",
    )
    check(
        "B4-2-8b 集成回归：无 error / 无 skipped，每条都有明确结论",
        c("error") == 0
        and c("skipped") == 0
        and c("structural_only") + c("fail") + c("blocked_auth") == 263,
        f"error={c('error')} skipped={c('skipped')}",
    )

    # ---------- B4-2-9 批次分布完整性 ----------
    from fastapi.testclient import TestClient

    from backend.main import app

    bid = executor.last_batch_id
    resp = TestClient(app).get(f"/api/projects/{pid}/batches")
    b = next((x for x in resp.json() if x["batch_id"] == bid), {})
    parts = ("passed", "failed", "structural_only", "blocked_auth", "errored", "skipped", "blocked")
    check(
        "B4-2-9 批次分布完整：各状态分项之和 == total（新状态未丢失）",
        b.get("total") == 263 and sum(b.get(k, 0) for k in parts) == b.get("total"),
        f"total={b.get('total')}, 分项和={sum(b.get(k, 0) for k in parts)}, "
        f"静态={b.get('structural_only')}",
    )

    srv.shutdown()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n==== 批次2 自测汇总：{passed}/{total} 通过，耗时 {int(time.time() - t0)}s ====")
    for name, ok, detail in _results:
        if not ok:
            print(f"  X {name} — {detail}")
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
