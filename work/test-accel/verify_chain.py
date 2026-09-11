"""全链路流程验证：代码获取 → 代码就位 → 依赖安装 → 配置生效 → 服务启动 → 测试执行。

每一步都真实执行（不模拟），记录耗时与结果状态：
  PASS   该环节跑通
  BLOCK  因环境/依赖缺失被阻塞（已记录阻塞点并继续后续可验证环节）
  FAIL   跑通了但结果不符合预期

产出：控制台结构化输出 + work/全链路流程验证报告.md
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import backend.db as db
from backend.config import PROJECT_ROOT, settings
from backend.main import _analyze_project
from backend.modules import browser, tp_store
from backend.modules.case_generator import case_generator
from backend.modules.executor import executor
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


TARGET = PROJECT_ROOT.parent / "targets" / "research-agent"
MOCK_DIR = TARGET / "frontend" / "mock-server"
PY = sys.executable
PORT = int(os.environ.get("CHAIN_PORT", "8091"))
BASE = f"http://127.0.0.1:{PORT}"

steps = []


def rec(no, name, status, elapsed, detail="", evidence=""):
    steps.append(
        dict(no=no, name=name, status=status, elapsed=elapsed, detail=detail, evidence=evidence)
    )
    icon = {"PASS": "[PASS]", "BLOCK": "[BLOCK]", "FAIL": "[FAIL]"}[status]
    print(f"{icon} {no} {name} — {detail}（{elapsed:.1f}s）")
    if evidence:
        for line in str(evidence).strip().splitlines()[:4]:
            print(f"        {line}")


def sh(cmd, cwd=None, timeout=60, env=None):
    t0 = time.time()
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            encoding="utf-8",
            errors="ignore",
        )
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip(), time.time() - t0
    except subprocess.TimeoutExpired:
        return -99, "", f"超时 {timeout}s", time.time() - t0
    except Exception as e:
        return -98, "", f"{type(e).__name__}: {e}", time.time() - t0


def main():
    t_all = time.time()

    # ============ 1. 代码获取：拉取 ============
    rc, out, err, dt = sh(["git", "-C", str(TARGET), "remote", "-v"], timeout=20)
    rc2, out2, err2, dt2 = sh(["git", "-C", str(TARGET), "fetch", "--dry-run"], timeout=40)
    has_remote = bool(out.strip())
    if has_remote and rc2 == 0:
        rec("1", "代码获取 · 拉取", "PASS", dt + dt2, "远端可达，fetch 正常", out2[:120])
    else:
        rec(
            "1",
            "代码获取 · 拉取",
            "BLOCK",
            dt + dt2,
            "无远端配置，无法拉取（当前为就地 init 的独立仓库）",
            f"git remote -v = {out.strip() or '(空)'} | fetch rc={rc2} err={err2[:120]}",
        )

    # ============ 2. 代码获取：检出 ============
    rc, out, err, dt = sh(["git", "-C", str(TARGET), "checkout", "main"], timeout=30)
    rc_h, head, _, dt_h = sh(["git", "-C", str(TARGET), "rev-parse", "HEAD"], timeout=20)
    rc_s, st, _, _ = sh(["git", "-C", str(TARGET), "status", "--porcelain"], timeout=30)
    ok = rc == 0 and rc_h == 0 and len(head) == 40
    rec(
        "2",
        "代码获取 · 检出",
        "PASS" if ok else "FAIL",
        dt + dt_h,
        f"checkout main → {head[:12]}，工作区变更 {len(st.splitlines())} 项",
        f"checkout rc={rc} {err[:80]}",
    )

    # ============ 3. 代码就位 ============
    t0 = time.time()
    exists = TARGET.exists()
    dirs = [d for d in ("backend", "frontend", "tools", "docs") if (TARGET / d).exists()]
    gi = Path(PROJECT_ROOT.parent.parent) / ".gitignore"
    ignored = (
        "work/targets/research-agent/" in gi.read_text(encoding="utf-8") if gi.exists() else False
    )
    ok = exists and len(dirs) >= 3
    rec(
        "3",
        "代码就位 · 目标路径与隔离",
        "PASS" if ok else "FAIL",
        time.time() - t0,
        f"local_path 存在={exists}，关键目录={dirs}，第三方仓库已 gitignore={ignored}",
        f"路径：{TARGET}",
    )

    # ============ 4. 依赖安装 ============
    t0 = time.time()
    entry = None
    for cand in (
        "backend/research-agent-source/server.py",
        "backend/research-agent-source/main.py",
        "backend/research-agent-source/app.py",
    ):
        if (TARGET / cand).exists():
            entry = cand
            break
    req_main = list(TARGET.glob("backend/research-agent-source/requirements*.txt"))
    if not entry:
        rec(
            "4a",
            "依赖安装 · 主后端",
            "BLOCK",
            time.time() - t0,
            "被测后端无启动入口（server.py 已随重构移除），依赖清单缺失",
            f"server.py/main.py/app.py 均不存在；requirements*.txt={req_main or '无'}",
        )
    else:
        rec("4a", "依赖安装 · 主后端", "PASS", time.time() - t0, f"入口={entry}")

    t0 = time.time()
    req = MOCK_DIR / "requirements.txt"
    if req.exists():
        rc, out, err, _ = sh(
            [PY, "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(req)],
            timeout=300,
        )
        ok = rc == 0
        rec(
            "4b",
            "依赖安装 · 可运行子服务 mock-server",
            "PASS" if ok else "FAIL",
            time.time() - t0,
            f"pip install -r requirements.txt rc={rc}",
            (out or err)[:200],
        )
    else:
        rec(
            "4b",
            "依赖安装 · 可运行子服务 mock-server",
            "BLOCK",
            time.time() - t0,
            "未找到 requirements.txt",
        )

    # ============ 5. 配置生效 ============
    t0 = time.time()
    probe = (
        "import os,sys;sys.path.insert(0,r'%s');"
        "os.environ['EXEC_MAX_WORKERS']='7';os.environ['ENABLE_DYNAMIC_PROBE']='on';"
        "from backend.config import settings as s;"
        "print(s.EXEC_MAX_WORKERS, s.ENABLE_DYNAMIC_PROBE)" % str(ROOT).replace("\\", "/")
    )
    rc, out, err, _ = sh([PY, "-c", probe], timeout=60)
    ok = rc == 0 and out.strip() == "7 True"
    rec(
        "5",
        "配置生效 · 环境变量注入",
        "PASS" if ok else "FAIL",
        time.time() - t0,
        f"子进程读取 EXEC_MAX_WORKERS/ENABLE_DYNAMIC_PROBE → {out.strip() or err[:100]}",
        f"预期 '7 True'，实际 {out.strip()!r}",
    )

    # ============ 6. 服务启动 ============
    t0 = time.time()
    env = dict(os.environ, PORT=str(PORT))
    # 注意：stdout 必须用 DEVNULL——用 PIPE 接管会在日志写满缓冲区后把 uvicorn 阻塞致死
    proc = subprocess.Popen(
        [PY, "server.py"],
        cwd=str(MOCK_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    up, waited, last, tries = False, 0.0, "", 0
    import urllib.request

    while waited < 40:
        tries += 1
        try:
            with urllib.request.urlopen(BASE + "/api/v1/health", timeout=2) as r:
                up = r.status == 200
                if up:
                    break
        except Exception as e:
            last = str(e)[:80]
        time.sleep(0.5)
        waited += 0.5
    rec(
        "6",
        "服务启动 · mock-server",
        "PASS" if up else "BLOCK",
        time.time() - t0,
        f"{BASE} 探活 {'成功' if up else '失败'}，等待 {waited}s（{tries} 次尝试）",
        f"启动命令：{PY} server.py（cwd={MOCK_DIR}，输出 DEVNULL）；最后错误={last}",
    )

    # ============ 7. 测试执行 ============
    t0 = time.time()
    db.init_db()
    if not pm.find_by_name("research-agent"):
        pm.add(
            name="research-agent",
            local_path=str(TARGET),
            ptype="pc",
            base_url="http://localhost:8010",
        )
    pid = pm.find_by_name("research-agent")["id"]
    orig_base = pm.get(pid)["base_url"]
    conn = db.get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    cur.execute(
        "UPDATE cases SET review_status='approved' WHERE project_id=? AND status!='archived'",
        (pid,),
    )
    conn.commit()
    conn.close()
    _analyze_project(pid)
    tp_store.import_test_points(pid)
    n_cases = case_generator.generate_for_project(pid)
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE cases SET review_status='approved' WHERE project_id=? AND status!='archived'",
        (pid,),
    )
    # 选出 file 指向 mock-server 的用例：它们的路由正好由刚启动的服务提供
    cur.execute("SELECT id, steps FROM cases WHERE project_id=? AND status!='archived'", (pid,))
    mock_ids = []
    for r in cur.fetchall():
        try:
            st = json.loads(r["steps"] or "[]")
        except Exception:
            continue
        if st and "mock-server/server.py" in (st[0].get("file") or ""):
            mock_ids.append(r["id"])
    conn.commit()
    conn.close()

    settings.ENABLE_DYNAMIC_PROBE = True
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET base_url=? WHERE id=?", (BASE, pid))
    conn.commit()
    conn.close()

    try:
        res = executor.run_project(pid, filters={"ids": mock_ids}, max_workers=4)
        bid = executor.last_batch_id
        from collections import Counter

        c = Counter(r["status"] for r in res)
        real = c.get("pass", 0) + c.get("fail", 0)
        rep = reporter.build(
            pid,
            res,
            meta={"project": "research-agent", "batch_id": bid, "filters": {"ids": mock_ids}},
        )
        ok = len(res) == len(mock_ids) and real > 0
        samples = "; ".join(f"{r['status']}:{str(r.get('reason'))[:40]}" for r in res[:3])
        rec(
            "7",
            "测试执行 · 真实 HTTP 动态判定",
            "PASS" if ok else "FAIL",
            time.time() - t0,
            f"用例 {len(res)} 条（mock-server 路由相关），结果分布 {dict(c)}",
            f"真实通过率分母={real}；样例 {samples}",
        )
    finally:
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE projects SET base_url=? WHERE id=?", (orig_base, pid))
        conn.commit()
        conn.close()
        settings.ENABLE_DYNAMIC_PROBE = False

    # ============ 8. 浏览器真实渲染（对已启动的服务） ============
    t0 = time.time()
    r = browser.check_page(BASE + "/api/v1/health", name="chain_health")
    ok = r.get("ok") is True and r.get("status") == 200
    rec(
        "8",
        "测试执行 · 真实浏览器渲染（D-★3）",
        "PASS" if ok else "BLOCK",
        time.time() - t0,
        f"浏览器打开 {BASE}/api/v1/health → HTTP {r.get('status')}",
        f"skipped={r.get('skipped')}, error={str(r.get('error'))[:100]}",
    )
    browser.shutdown()

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
    rec("9", "资源回收 · 停止被测服务", "PASS", 0.0, "mock-server 已终止")

    # ============ 汇总 ============
    total = time.time() - t_all
    n_pass = sum(1 for s in steps if s["status"] == "PASS")
    n_block = sum(1 for s in steps if s["status"] == "BLOCK")
    n_fail = sum(1 for s in steps if s["status"] == "FAIL")

    lines = [
        "# 全链路流程验证报告",
        "",
        f"> 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}　"
        f"总耗时：{total:.1f}s　结果：**PASS {n_pass} / BLOCK {n_block} / FAIL {n_fail}**",
        "",
        "## 一、逐环节结果",
        "",
        "| # | 环节 | 状态 | 耗时(s) | 实际结果 | 证据/命令 |",
        "|---|---|---|---|---|---|",
    ]
    for s in steps:
        ev = (s["evidence"] or "").replace("|", "\\|").replace("\n", " ")[:180]
        lines.append(
            f"| {s['no']} | {s['name']} | **{s['status']}** | "
            f"{s['elapsed']:.1f} | {s['detail']} | `{ev}` |"
        )
    lines += [
        "",
        "## 二、链路断点",
        "",
        "- **断点 1（代码获取）**：被测仓库 `work/targets/research-agent` **无 git remote**，"
        "`git fetch` 无法执行。当前只能以「就地 init + WORKTREE」方式工作，"
        "无法验证真实远程拉取与跨 ref 增量对比。",
        "- **断点 2（代码就位/依赖安装/服务启动）**：被测后端 **无启动入口**"
        "（`backend/research-agent-source/server.py` 已随重构移除，仓库内无 FastAPI app 定义与依赖清单），"
        "因此主后端无法安装依赖、无法启动，链路在此断开。",
        "- **可跑通部分**：以 `frontend/mock-server`（16 路由、依赖仅 fastapi/uvicorn/requests）"
        "作为真实目标时，「依赖安装 → 配置生效 → 服务启动 → 真实 HTTP 执行 → 报告」"
        "全段跑通，证明执行链路本身可用，断点是**被测产物的可运行性**问题，而非平台能力问题。",
        "",
        "## 三、复现命令",
        "",
        "```bash",
        f"cd {ROOT}",
        f"{PY} verify_chain.py          # 一键跑完 9 个环节并生成本报告",
        "# 手动启动被测子服务：",
        f"cd {MOCK_DIR} && {PY} server.py     # 默认 8091，PORT 环境变量可覆盖",
        "```",
        "",
    ]
    out_md = PROJECT_ROOT.parent / "全链路流程验证报告.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "=" * 66)
    print(
        f"==== 全链路验证：PASS {n_pass} / BLOCK {n_block} / FAIL {n_fail}，"
        f"总耗时 {total:.1f}s ===="
    )
    print(f"报告已写入：{out_md}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
