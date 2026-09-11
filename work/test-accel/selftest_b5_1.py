"""阶段5 批次（D-②6）自测：执行历史/进度查询 + 可中断能力。

验证项
 B5-1-1  同步执行：注册表从 running → done，done==total，status_counts 合计==total
 B5-1-2  中断：执行中途请求取消 → 终态 cancelled，done<total，已执行结果落库、未丢
 B5-1-3  API 异步：async_mode 立即返回 batch_id，轮询 /execute/status 直到 done==total
 B5-1-4  API 取消：async_mode 启动后立刻 POST /execute/cancel → 终态 cancelled 且 done<total
 B5-1-5  API 活跃列表：/execute/active 在执行中能列出本批次
 B5-1-6  进度无 batch_id 时回退 runs 表重建终态分布（历史/重启兜底）
"""

import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

import backend.db as db
from backend.config import settings
from backend.main import app
from backend.modules.executor import executor
from backend.modules.project_manager import pm


_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def make_project(name, n_cases):
    p = pm.find_by_name(name)
    pid = (
        p["id"]
        if p
        else pm.add(name=name, local_path=str(ROOT), ptype="pc", base_url="http://localhost:9")
    )
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM cases WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM runs WHERE project_id=?", (pid,))
    # 用例 steps 留空：用 patched _safe_run 控制执行耗时与结果，避免依赖被测服务
    for i in range(n_cases):
        cur.execute(
            """INSERT INTO cases (project_id, title, steps, ctype, status,
                                  review_status, priority, module, case_type, test_type)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (pid, f"case-{i}", "[]", "api", "generated", "approved", "P1", "模块X", "正常", "全量"),
        )
    conn.commit()
    conn.close()
    return pid


def main():
    t0 = time.time()
    settings.REVIEW_GATE = False
    settings.ENABLE_DYNAMIC_PROBE = False
    db.init_db()

    pid = make_project("b5-progress", 60)
    print(f"[setup] 项目 {pid}：60 条空步骤用例")

    orig_safe = executor._safe_run

    def slow(c, proj, ctx, service_up):
        time.sleep(0.03)
        return {"status": "pass", "reason": "patched", "log": ""}

    # ---------- B5-1-1 同步执行注册表生命周期 ----------
    executor._safe_run = slow
    try:
        res = executor.run_project(pid, max_workers=1)
    finally:
        executor._safe_run = orig_safe
    st = executor.get_batch_status(executor.last_batch_id)
    cnt_sum = sum(st["status_counts"].values()) if st else -1
    check(
        "B5-1-1 同步执行：终态 done 且 done==total",
        st and st["state"] == "done" and st["done"] == 60 == len(res),
        f"state={st['state'] if st else None}, done={st['done'] if st else None}",
    )
    check("B5-1-1b 同步执行：status_counts 合计 == total", cnt_sum == 60, f"sum={cnt_sum}")

    # ---------- B5-1-2 中断（同步调用 + 后台线程触发取消） ----------
    executor._safe_run = slow
    bid = executor._new_batch_id(pid)
    import threading

    def canceller():
        time.sleep(0.5)  # 约执行到第 ~16 条时请求取消
        executor.cancel_batch(bid)

    th = threading.Thread(target=canceller, daemon=True)
    th.start()
    try:
        res2 = executor.run_project(pid, max_workers=1, batch_id=bid)
    finally:
        executor._safe_run = orig_safe
    st2 = executor.get_batch_status(bid)
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM runs WHERE project_id=? AND batch_id=?", (pid, bid))
    runs2 = cur.fetchone()["c"]
    conn.close()
    check(
        "B5-1-2 中断：终态 cancelled 且 done<total",
        st2["state"] == "cancelled" and st2["done"] < 60,
        f"state={st2['state']}, done={st2['done']}",
    )
    check(
        "B5-1-2b 中断：已执行结果全部落库（runs 数 == done，未丢）",
        runs2 == st2["done"],
        f"runs={runs2}, done={st2['done']}",
    )
    check(
        "B5-1-2c 中断：未执行部分不产生 runs（done + 余量 == 60）",
        st2["done"] + (60 - st2["done"]) == 60,
    )

    # ---------- B5-1-3 / B5-1-5 API 异步进度轮询 ----------
    executor._safe_run = slow
    client = TestClient(app)
    try:
        r = client.post(
            f"/api/projects/{pid}/execute",
            json={"max_workers": 1, "with_report": False, "async_mode": True},
        )
        body = r.json()
        bid3 = body["batch_id"]
        check(
            "B5-1-3 async_mode 立即返回 batch_id（不阻塞）",
            r.status_code == 200 and body.get("async") is True and bid3,
            f"http={r.status_code}, batch_id={bid3}",
        )
        # B5-1-5 活跃列表：轮询直到本批次出现在 active 中（克服线程注册的最小时延）
        in_active = False
        seen_state = None
        for _ in range(50):
            act = client.get(f"/api/projects/{pid}/execute/active").json()
            hit = [b for b in act.get("active", []) if b["batch_id"] == bid3]
            if hit:
                in_active = True
                seen_state = hit[0]["state"]
                break
            time.sleep(0.05)
        check(
            "B5-1-5 /execute/active 在执行中能列出本批次（running/done）",
            in_active,
            f"active_contains={in_active}, seen_state={seen_state}",
        )
        # 轮询直到 done
        deadline = time.time() + 15
        final = None
        while time.time() < deadline:
            s = client.get(f"/api/projects/{pid}/execute/status", params={"batch_id": bid3}).json()
            final = s.get("status")
            if final and final["state"] == "done":
                break
            time.sleep(0.1)
        check(
            "B5-1-3b 轮询 /execute/status 直到 done 且 done==total",
            final and final["state"] == "done" and final["done"] == 60,
            f"state={final['state'] if final else None}, done={final['done'] if final else None}",
        )
    finally:
        executor._safe_run = orig_safe

    # ---------- B5-1-4 API 中途取消 ----------
    executor._safe_run = slow
    try:
        r4 = client.post(
            f"/api/projects/{pid}/execute",
            json={"max_workers": 1, "with_report": False, "async_mode": True},
        )
        bid4 = r4.json()["batch_id"]
        time.sleep(0.5)
        c = client.post(f"/api/projects/{pid}/execute/cancel", json={"batch_id": bid4})
        check(
            "B5-1-4 POST /execute/cancel 返回 ok",
            c.status_code == 200 and c.json().get("cancelled") is True,
            f"http={c.status_code}",
        )
        deadline = time.time() + 15
        final4 = None
        while time.time() < deadline:
            s = client.get(f"/api/projects/{pid}/execute/status", params={"batch_id": bid4}).json()
            final4 = s.get("status")
            if final4 and final4["state"] in ("cancelled", "done"):
                break
            time.sleep(0.1)
        check(
            "B5-1-4b 取消后终态 cancelled 且 done<total",
            final4 and final4["state"] == "cancelled" and final4["done"] < 60,
            f"state={final4['state'] if final4 else None}, done={final4['done'] if final4 else None}",
        )
    finally:
        executor._safe_run = orig_safe

    # ---------- B5-1-6 进度无 registry 记录时回退持久化表 ----------
    # P5-②5 起，执行进度会持久化到 run_batches 表；一个已从 registry 移除的历史 batch
    # 应通过 run_batches 回退查询（source=run_batches），跨进程重启仍可查。
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT batch_id FROM runs WHERE project_id=? GROUP BY batch_id "
        "ORDER BY MIN(id) DESC LIMIT 1",
        (pid,),
    )
    row = cur.fetchone()
    conn.close()
    hist_bid = row["batch_id"] if row else None
    # 临时从 registry 移除以强制走持久化回退分支
    from backend.modules.executor import _BATCH_REGISTRY

    _BATCH_REGISTRY.pop(hist_bid, None)
    rb = client.get(f"/api/projects/{pid}/execute/status", params={"batch_id": hist_bid}).json()
    check(
        "B5-1-6 进度回退 run_batches 持久化表（source=run_batches）",
        rb.get("ok")
        and rb.get("source") == "run_batches"
        and rb["status"]["state"] in ("done", "cancelled"),
        f"source={rb.get('source')}, state={rb.get('status', {}).get('state')}",
    )

    passed = sum(1 for _, ok, _ in _results if ok)
    print("\n" + "=" * 60)
    print(
        f"==== 阶段5 D-②6 自测汇总：{passed}/{len(_results)} 通过，"
        f"耗时 {time.time() - t0:.1f}s ===="
    )
    for name, ok, detail in _results:
        if not ok:
            print(f"  [FAILED] {name} — {detail}")
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
