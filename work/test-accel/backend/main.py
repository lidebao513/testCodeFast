"""测试加速平台 · 后端入口（FastAPI）。
阶段1骨架：配置 + DB + 项目管理 + 代码分析(读结构→功能点)。
必要任务：Case生成 / 最小执行器 / 报告 / 一键 scan_and_test。
后续阶段：Skill / 增量回归 / 前端 / 真实UI执行。
"""
import json
import os
import subprocess
from pathlib import Path
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings, PROJECT_ROOT
from backend.db import init_db, get_conn
from backend.modules.project_manager import pm
from backend.modules.code_analyzer import code_analyzer
from backend.modules.case_generator import case_generator
from backend.modules.executor import executor
from backend.modules.reporter import reporter
from backend.modules import smoke as smoke_module

app = FastAPI(title="测试加速平台", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _commit_ref(local_path: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", local_path, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _register_research_agent():
    if pm.find_by_name("research-agent"):
        return
    # targets/ 与 test-accel/ 同级（均在 work/ 下）
    target = PROJECT_ROOT.parent / "targets" / "research-agent"
    if not target.exists():
        return
    pm.add(
        name="research-agent",
        # 仓库地址不入库（避免泄露内网 Git 主机/组织 ID），
        # 请通过环境变量 RA_GIT_URL 注入真实地址
        git_url=os.environ.get(
            "RA_GIT_URL", "https://<your-git-host>/<your-org>/research-agent.git"
        ),
        branch="main",
        ptype="pc",
        local_path=str(target),
        run_command="后端: python server.py (uvicorn 0.0.0.0:8010)；前端: npm run dev (vite)",
        port=8010,
        base_url="http://localhost:8010",
        auth_type="none",
        health_url="http://localhost:8010/health",
    )


@app.on_event("startup")
def _startup():
    init_db()
    _register_research_agent()


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_enhance": settings.LLM_ENHANCE,
            "review_gate": settings.REVIEW_GATE, "provider": settings.LLM_PROVIDER}


@app.get("/api/projects")
def list_projects():
    return pm.list()


def _analyze_project(pid: int):
    """读结构提取功能点（全量扫描语义），返回 (fps, commit)。"""
    proj = pm.get(pid)
    local_path = proj["local_path"]
    commit = _commit_ref(local_path)
    fps = code_analyzer.analyze(local_path, project_type=proj.get("type", "pc"))
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM functional_points WHERE project_id=?", (pid,))
    for fp in fps:
        cur.execute(
            """INSERT INTO functional_points
               (project_id, commit_ref, file_path, name, description, ftype, review_status)
               VALUES (?,?,?,?,?,?,?)""",
            (pid, commit, fp["file_path"], fp["name"], fp["description"], fp["ftype"],
             "approved" if not settings.REVIEW_GATE else "pending"),
        )
    conn.commit()
    conn.close()
    return fps, commit


@app.post("/api/projects/{pid}/analyze")
def analyze(pid: int):
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, "error": "project not found"}
    fps, commit = _analyze_project(pid)
    summary = {}
    for fp in fps:
        summary[fp["ftype"]] = summary.get(fp["ftype"], 0) + 1
    return {
        "ok": True,
        "project": proj["name"],
        "commit_ref": commit[:12],
        "total": len(fps),
        "by_type": summary,
        "sample": fps[:20],
    }


@app.get("/api/projects/{pid}/functional_points")
def functional_points(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM functional_points WHERE project_id=? ORDER BY id", (pid,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/projects/{pid}/cases")
def list_cases(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cases WHERE project_id=? ORDER BY id", (pid,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/projects/{pid}/reports")
def list_reports(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id,batch_id,summary,html_path,created_at FROM reports "
        "WHERE project_id=? ORDER BY id DESC", (pid,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/projects/{pid}/scan_and_test")
def scan_and_test(pid: int, force: bool = True):
    """一键闭环：分析(读结构) → 生成 case → 执行 → 报告。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, "error": "project not found"}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM functional_points WHERE project_id=?", (pid,))
    has = cur.fetchone()["c"] > 0
    conn.close()

    fp_count = 0
    if force or not has:
        _, _ = _analyze_project(pid)
        fp_count = cur_fp_count(pid)

    n_cases = case_generator.generate_for_project(pid)
    results = executor.run_project(pid)
    report = reporter.build(pid, results, meta={"project": proj["name"]})
    return {
        "ok": True,
        "project": proj["name"],
        "functional_points": fp_count,
        "cases": n_cases,
        "report_id": report["id"],
        "summary": report["summary"],
        "html": report["html_path"],
    }


class SmokeReq(BaseModel):
    account: str = None
    password: str = None
    base_url: str = None


@app.get("/api/projects/{pid}/smoke")
def smoke_get(pid: int, base_url: str = None):
    """匿名冒烟：验证被测服务是否已启动且基本可用（不登录）。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, "error": "project not found"}
    rep = smoke_module.smoke_project(proj, base_url=base_url)
    return {"ok": True, **rep}


@app.post("/api/projects/{pid}/smoke")
def smoke_post(pid: int, payload: SmokeReq):
    """登录冒烟：提供账号密码，验证登录态与受保护接口可用。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, "error": "project not found"}
    rep = smoke_module.smoke_project(
        proj, account=payload.account, password=payload.password,
        base_url=payload.base_url)
    return {"ok": True, **rep}


def cur_fp_count(pid: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM functional_points WHERE project_id=?", (pid,))
    n = cur.fetchone()["c"]
    conn.close()
    return n


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.PLATFORM_PORT, reload=False)
