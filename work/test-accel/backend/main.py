"""测试加速平台 · 后端入口（FastAPI）。
阶段1骨架：配置 + DB + 项目管理 + 代码分析(读结构→功能点)。
必要任务：Case生成 / 最小执行器 / 报告 / 一键 scan_and_test。
后续阶段：Skill / 增量回归 / 前端 / 真实UI执行。
"""

import json
import os
import subprocess
import threading
import time
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import PROJECT_ROOT, settings
from backend.core.enums import (
    ExecStatus,
    PullStatus,
)
from backend.db import get_conn, init_db
from backend.modules import analytics as analytics_module
from backend.modules import exporters as exporters_module
from backend.modules import full_report as full_report_module
from backend.modules import smoke as smoke_module
from backend.modules import tp_store
from backend.modules.case_generator import case_generator
from backend.modules.code_analyzer import (
    fp_id_of,
    generate_comprehensive_test_points,
)
from backend.modules.diff_analyzer import diff_analyzer
from backend.modules.executor import executor
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


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
            capture_output=True,
            text=True,
            timeout=10,
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
    # 阶段5（P5-②5）：进程重启后，把上次未正常结束（DB 中仍 running）的批次
    # 标记为 interrupted 并触发 webhook（若配置），覆盖「执行中断」闭环。
    try:
        from backend.modules import batch_store as bs_mod

        recovered = bs_mod.recover_interrupted(executor.fire_webhook)
        if recovered:
            print(f"[batch_store] 启动时恢复 {len(recovered)} 个中断批次: {recovered}")
    except Exception as e:
        print(f"[batch_store] 启动恢复跳过：{e}")
    _register_research_agent()


@app.get("/api/health")
def health():
    return {
        "status": PullStatus.OK.value,
        "llm_enhance": settings.LLM_ENHANCE,
        "review_gate": settings.REVIEW_GATE,
        "provider": settings.LLM_PROVIDER,
    }


@app.get("/api/projects")
def list_projects():
    return pm.list()


def _analyze_project(pid: int):
    """读结构提取功能点（全量扫描语义，含 business 维度），返回 (fps, commit)。

    C-★6 修复：改用 ``generate_comprehensive_test_points()`` 的统一功能点清单，
    而非旧 ``code_analyzer.analyze()``（后者仅 99 个 FP 且缺 business 维度）。
    综合构建器产出的 FP 与阶段2 ``gen_test_points`` 同源同算法，fp_id 完全一致，
    因此 263 条测试点的 fp_contract_id 全部能在 functional_points 行级解析到对应行，
    TP→Case 双向追溯不再有孤儿（此前 138 条无对应行）。
    """
    proj = pm.get(pid)
    local_path = proj["local_path"]
    commit = _commit_ref(local_path)
    data = generate_comprehensive_test_points(
        local_path, project_type=proj.get("type", "pc"), changed_files=None, scopes=None
    )
    fps = data["functional_points"]  # 统一契约 FP 列表（api/page/component/business）
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM functional_points WHERE project_id=?", (pid,))
    for fp in fps:
        cur.execute(
            """INSERT INTO functional_points
               (project_id, commit_ref, file_path, name, description, ftype,
                contract_id, review_status, title, module)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                pid,
                commit,
                fp.get("file_path"),
                fp.get("name"),
                fp.get("description"),
                fp.get("ftype"),
                fp.get("fp_id"),
                "approved" if not settings.REVIEW_GATE else "pending",
                fp.get("title"),
                fp.get("module"),
            ),
        )
    conn.commit()
    conn.close()
    return fps, commit


@app.post("/api/projects/{pid}/analyze")
def analyze(pid: int):
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
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


@app.post("/api/projects/{pid}/diff_analyze")
def diff_analyze(
    pid: int,
    base: str = "master",
    head: str = "HEAD",
    gen_cases: bool = True,
    include_files: bool = False,
    sample: int = 50,
):
    """增量对比：对比 base..head 两个 ref，产出功能点差异（new/updated/removed），
    只针对 new + updated 生成用例（removed 的不生成，应废弃），结果写入 change_log。

    - base / head：分支名、tag 或 commit sha，例：base=master head=test-20260906
    - gen_cases：是否为新增/变更功能点生成用例
    - include_files：是否在返回中带上变更文件明细
    """
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    local_path = proj.get("local_path")
    if not local_path:
        return {"ok": False, ExecStatus.ERROR.value: "project has no local_path"}

    res = diff_analyzer.analyze_diff(
        local_path, base, head, project_type=proj.get("type", "pc"), include_files=include_files
    )
    if not res.get("ok"):
        return res

    conn = get_conn()
    cur = conn.cursor()
    new_ids, upd_ids = [], []
    # 新增/变更的功能点落库（已存在则复用，保证幂等）
    for tag, fps in (("new", res["new_fps"]), ("updated", res["updated_fps"])):
        for fp in fps:
            cur.execute(
                """SELECT id FROM functional_points
                   WHERE project_id=? AND file_path=? AND name=? AND ftype=?""",
                (pid, fp["file_path"], fp["name"], fp["ftype"]),
            )
            row = cur.fetchone()
            if row:
                fid = row["id"]
            else:
                cur.execute(
                    """INSERT INTO functional_points
                       (project_id, commit_ref, file_path, name, description, ftype,
                        contract_id, review_status)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        pid,
                        res["head_commit"],
                        fp["file_path"],
                        fp["name"],
                        fp["description"],
                        fp["ftype"],
                        fp_id_of(fp["ftype"], fp["file_path"], fp["name"]),
                        "approved" if not settings.REVIEW_GATE else "pending",
                    ),
                )
                fid = cur.lastrowid
            (new_ids if tag == "new" else upd_ids).append(fid)

    cases_info = {"created": 0, "reused": 0, "case_ids": []}
    if gen_cases and (new_ids or upd_ids):
        cases_info = case_generator.generate_for_fp_ids(pid, new_ids + upd_ids)

    # 落 change_log（该表建表时就已预留，此前从未被写入）
    removed_keys = [f"{fp['ftype']}|{fp['file_path']}|{fp['name']}" for fp in res["removed_fps"]]
    cur.execute(
        """INSERT INTO change_log
           (project_id, commit_from, commit_to, new_fp_ids, updated_fp_ids, removed_fp_ids)
           VALUES (?,?,?,?,?,?)""",
        (
            pid,
            res["base_commit"],
            res["head_commit"],
            json.dumps(new_ids),
            json.dumps(upd_ids),
            json.dumps(removed_keys),
        ),
    )
    change_log_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "project": proj["name"],
        "base": res["base"],
        "head": res["head"],
        "base_commit": res["base_commit"],
        "head_commit": res["head_commit"],
        "changed_files": res["changed_files"],
        "fp_diff": res["fp_diff"],
        "new_fps": res["new_fps"][:sample],
        "updated_fps": res["updated_fps"][:sample],
        "removed_fps": res["removed_fps"][:sample],
        "cases": cases_info,
        "change_log_id": change_log_id,
        "stats": res["stats"],
        "changed_file_list": res.get("changed_file_list"),
    }


@app.get("/api/projects/{pid}/change_logs")
def change_logs(pid: int):
    """查看该项目的历次增量对比记录。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM change_log WHERE project_id=? ORDER BY id DESC", (pid,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/projects/{pid}/functional_points")
def functional_points(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM functional_points WHERE project_id=? ORDER BY id", (pid,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/projects/{pid}/import_test_points")
def import_test_points(pid: int, json_path: str | None = None):
    """导入阶段2 产出的测试点 JSON（test_points_new.json）到平台 DB。
    这是「测试点 → 用例」主链路的前置步骤。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    return tp_store.import_test_points(pid, json_path)


@app.get("/api/projects/{pid}/test_points")
def list_test_points(pid: int, category: str | None = None):
    return tp_store.get_test_points(pid, category)


@app.post("/api/projects/{pid}/generate_cases")
def generate_cases(pid: int):
    """显式生成用例：已导入测试点则按 TP 驱动，否则按功能点回退。
    生成后自动导出 TEST_CASES.md + test_cases.json 交付物（C-★4）。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    stats = case_generator.generate_for_project(pid)
    n = stats.get("active", 0) if isinstance(stats, dict) else stats
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT category, COUNT(*) c FROM test_points WHERE project_id=? GROUP BY category", (pid,)
    )
    tp_by_cat = {r["category"]: r["c"] for r in cur.fetchall()}
    cur.execute("SELECT ctype, COUNT(*) c FROM cases WHERE project_id=? GROUP BY ctype", (pid,))
    case_by_ctype = {r["ctype"]: r["c"] for r in cur.fetchall()}
    # 生命周期状态分布（C-②8：generated/updated/obsolete）
    cur.execute("SELECT status, COUNT(*) c FROM cases WHERE project_id=? GROUP BY status", (pid,))
    case_by_lifecycle = {r["status"]: r["c"] for r in cur.fetchall()}
    conn.close()
    exp = case_generator.export_test_cases(pid)
    return {
        "ok": True,
        "cases": n,
        "reconcile": stats,
        "tp_by_category": tp_by_cat,
        "case_by_ctype": case_by_ctype,
        "case_by_lifecycle": case_by_lifecycle,
        "export": exp,
    }


@app.post("/api/projects/{pid}/export_test_cases")
def export_test_cases(pid: int):
    """单独导出用例清册交付物（TEST_CASES.md + test_cases.json）。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    return case_generator.export_test_cases(pid)


@app.get("/api/projects/{pid}/cases")
def list_cases(pid: int, include_archived: bool = False):
    conn = get_conn()
    cur = conn.cursor()
    # 默认只返回当前生效用例；软删的 archived 需显式 include_archived 才可见
    if include_archived:
        cur.execute("SELECT * FROM cases WHERE project_id=? ORDER BY id", (pid,))
    else:
        cur.execute(
            "SELECT * FROM cases WHERE project_id=? AND status!='archived' ORDER BY id", (pid,)
        )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/projects/{pid}/runs")
def list_runs(pid: int, batch_id: str | None = None, limit: int = 500):
    """执行历史查询（D-★5 配套）：默认返回最近 limit 条；
    指定 batch_id 可精确回溯某一轮执行的全部结果，支撑多轮对比与 flaky 识别。"""
    conn = get_conn()
    cur = conn.cursor()
    if batch_id:
        cur.execute(
            "SELECT * FROM runs WHERE project_id=? AND batch_id=? ORDER BY id", (pid, batch_id)
        )
    else:
        cur.execute("SELECT * FROM runs WHERE project_id=? ORDER BY id DESC LIMIT ?", (pid, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@app.get("/api/projects/{pid}/batches")
def list_batches(pid: int):
    """历次执行批次概览（D-★5）：每轮 batch_id / 用例数 / 结果分布，用于多轮趋势对比。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT batch_id, COUNT(*) total,
                  SUM(CASE WHEN status=ExecStatus.PASS.value THEN 1 ELSE 0 END) passed,
                  SUM(CASE WHEN status=ExecStatus.FAIL.value THEN 1 ELSE 0 END) failed,
                  SUM(CASE WHEN status=ExecStatus.STRUCTURAL_ONLY.value THEN 1 ELSE 0 END) structural_only,
                  SUM(CASE WHEN status=ExecStatus.BLOCKED_AUTH.value THEN 1 ELSE 0 END) blocked_auth,
                  SUM(CASE WHEN status=ExecStatus.ERROR.value THEN 1 ELSE 0 END) errored,
                  SUM(CASE WHEN status=ExecStatus.SKIPPED.value THEN 1 ELSE 0 END) skipped,
                  SUM(CASE WHEN status=ExecStatus.BLOCKED_REVIEW.value THEN 1 ELSE 0 END) blocked,
                  MIN(created_at) started_at
           FROM runs WHERE project_id=? AND batch_id IS NOT NULL
           GROUP BY batch_id ORDER BY started_at DESC""",
        (pid,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@app.get("/api/projects/{pid}/reports")
def list_reports(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id,batch_id,summary,html_path,created_at FROM reports "
        "WHERE project_id=? ORDER BY id DESC",
        (pid,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/projects/{pid}/coverage")
def project_coverage(pid: int):
    """覆盖率报告（P6-②2）：用例 vs 测试点 vs 功能点 覆盖率与未覆盖缺口。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    return analytics_module.coverage(pid)


# ---- 阶段6 批次2（P6-②1 趋势/flaky + P6-②2 覆盖率）----
# 注意：以下静态路由必须注册在 /reports/{rid} 之前，否则会被 int 路径参数拦截返回 422
@app.get("/api/projects/{pid}/reports/trend")
def reports_trend(pid: int, only_finished: bool = True):
    """多批次执行趋势（P6-②1）：基于 run_batches 序列的通过率/状态分布趋势。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    return analytics_module.trend(pid, only_finished=only_finished)


@app.get("/api/projects/{pid}/reports/flaky")
def reports_flaky(pid: int, min_batches: int = 2):
    """跨批次 flaky 识别（P6-②1）：返回结果不一致的用例。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    return analytics_module.flaky(pid, min_batches=min_batches)


@app.get("/api/projects/{pid}/reports/trend_coverage")
def report_trend_coverage(pid: int, html: bool = True):
    """趋势 + flaky + 覆盖率 合订 HTML 报告（P6-②1/②2 对外可视化）。"""
    from fastapi.responses import FileResponse

    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    html_text = analytics_module.render_trend_coverage_html(pid)
    out_dir = settings.REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    import time as _t

    ts = _t.strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"trend_coverage_{pid}_{ts}.html"
    path.write_text(html_text, encoding="utf-8")
    if html:
        return FileResponse(str(path), media_type="text/html", filename=path.name)
    return {"ok": True, "html_path": str(path)}


@app.get("/api/projects/{pid}/reports/full")
def report_full(pid: int, batch_id: str | None = None, fmt: str = "html"):
    """章节化全功能验证报告（P6-②5 落地）：9 章节（变更摘要→测试点→用例清册→

    明细→统计→结论风险→监控→截图→复用占比），产出 VERIFICATION_REPORT.md/.html。
    fmt=html|md 返回对应文件；fmt=json 返回生成汇总。
    """
    from fastapi.responses import FileResponse

    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    res = full_report_module.generate(pid, batch_id=batch_id)
    if not res.get("ok"):
        return {"ok": False, ExecStatus.ERROR.value: "generate failed"}
    fmt = (fmt or "html").lower()
    if fmt == "md":
        return FileResponse(
            res["md_path"], media_type="text/markdown", filename=Path(res["md_path"]).name
        )
    if fmt == "json":
        return res
    return FileResponse(
        res["html_path"], media_type="text/html", filename=Path(res["html_path"]).name
    )


@app.get("/api/projects/{pid}/reports/{rid}")
def get_report(pid: int, rid: int, inline: bool = False):
    """单条报告详情（P6-★3）：返回该轮执行的 summary / html_path / created_at；

    inline=true 时一并返回 HTML 全文，便于外部系统编程取回最终报告。
    """
    rep = reporter.build_report_detail(pid, rid, inline=inline)
    if rep is None:
        return {"ok": False, ExecStatus.ERROR.value: "report not found"}
    rep["ok"] = True
    return rep


@app.get("/api/projects/{pid}/reports/{rid}/html")
def get_report_html(pid: int, rid: int):
    """直接取回最终 HTML 报告文件（P6-★3）：供浏览器/外部系统打开与分享。"""
    from fastapi.responses import FileResponse

    rep = reporter.build_report_detail(pid, rid, inline=False)
    if rep is None:
        return {"ok": False, ExecStatus.ERROR.value: "report not found"}
    p = rep.get("html_path")
    if not p or not Path(p).exists():
        return {"ok": False, ExecStatus.ERROR.value: "html file missing"}
    return FileResponse(p, media_type="text/html", filename=Path(p).name)


# ---- 阶段6 批次3（P6-④ 执行摘要 + P6-②3 报告导出）----
@app.get("/api/projects/{pid}/reports/{rid}/summary")
def report_summary(pid: int, rid: int):
    """执行摘要（P6-④）：一句话结论 + 关键指标 + 建议，供 PM/领导快速决策。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    s = reporter.build_exec_summary(pid, rid)
    if s is None:
        return {"ok": False, ExecStatus.ERROR.value: "report not found"}
    return {"ok": True, **s}


@app.get("/api/projects/{pid}/exec_summary")
def project_exec_summary(pid: int):
    """项目最新一份报告的执行摘要（P6-④ 便捷端点）。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    s = reporter.build_exec_summary(pid)
    if s is None:
        return {"ok": False, ExecStatus.ERROR.value: "no report yet"}
    return {"ok": True, **s}


@app.get("/api/projects/{pid}/reports/{rid}/export")
def report_export(pid: int, rid: int, fmt: str = "xlsx"):
    """报告导出（P6-②3）：fmt=xlsx|docx|pdf，返回对应格式文件供下载/分发。"""
    from fastapi.responses import FileResponse

    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    path = exporters_module.export_report(pid, rid, fmt)
    if not path or not Path(path).exists():
        return {
            "ok": False,
            ExecStatus.ERROR.value: "export failed (report not found or unsupported fmt)",
        }
    ctype = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
    }.get(fmt, "application/octet-stream")
    return FileResponse(str(path), media_type=ctype, filename=Path(path).name)


@app.post("/api/projects/{pid}/scan_and_test")
def scan_and_test(pid: int, force: bool = True):
    """一键闭环：分析(读结构) → 生成 case → 执行 → 报告。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM functional_points WHERE project_id=?", (pid,))
    has = cur.fetchone()["c"] > 0
    conn.close()

    fp_count = 0
    if force or not has:
        _, _ = _analyze_project(pid)
        fp_count = cur_fp_count(pid)

    # 尝试导入阶段2 测试点（不存在则跳过，回退功能点驱动）
    tp_store.import_test_points(pid)
    reconcile = case_generator.generate_for_project(pid)
    n_cases = reconcile.get("active", 0) if isinstance(reconcile, dict) else reconcile
    case_generator.export_test_cases(pid)
    results = executor.run_project(pid)
    # D-★5：把执行批次号透传给报告，使本轮 runs 与 reports 可按 batch_id 关联
    batch_id = getattr(executor, "last_batch_id", None)
    report = reporter.build(pid, results, meta={"project": proj["name"], "batch_id": batch_id})
    return {
        "ok": True,
        "project": proj["name"],
        "functional_points": fp_count,
        "cases": n_cases,
        "reconcile": reconcile,
        "batch_id": batch_id,
        "report_id": report["id"],
        "summary": report["summary"],
        "html": report["html_path"],
    }


class ExecuteReq(BaseModel):
    """阶段4 批次3（D-★6）：执行子集筛选。

    filters 支持字段（均可选，值可为字符串或数组）：
      priority / module / case_type(正常|异常) / test_type(全量|新增) / ctype /
      ids / fp_contract_id / tp_id / review_status
    例：只跑新增的 P1 用例 → {"test_type": "新增", "priority": ["P1"]}
    """

    filters: dict = None
    max_workers: int = None  # 并发度（D-②2），None → 取 settings.EXEC_MAX_WORKERS
    use_browser: bool = None  # 是否启用真实浏览器（D-★3），None → settings.ENABLE_BROWSER
    include_archived: bool = False
    limit: int = 0
    with_report: bool = True
    async_mode: bool = False  # 阶段5（D-②6）：后台执行并立即返回 batch_id，可轮询进度/取消
    webhook_url: str = None  # 阶段5（P5-★4）：执行结束回调地址；缺省回退项目级 projects.webhook_url


@app.post("/api/projects/{pid}/execute")
def execute_project(pid: int, payload: ExecuteReq):
    """按筛选条件执行用例（D-★6）。不传 filters 即全量执行。

    async_mode=True 时：在后台线程启动执行，立即返回 batch_id 与进度/取消 URL，
    便于长时间执行期间监控进度与中断（D-②6）；False 保持同步阻塞返回结果。
    """
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    if payload.async_mode:
        bid = executor._new_batch_id(pid)
        wh_url = payload.webhook_url or (proj.get("webhook_url") or "")

        def _bg():
            try:
                results = executor.run_project(
                    pid,
                    filters=payload.filters,
                    max_workers=payload.max_workers,
                    use_browser=payload.use_browser,
                    include_archived=payload.include_archived,
                    limit=payload.limit,
                    batch_id=bid,
                    webhook_url=wh_url,
                )
                st = executor.get_batch_status(bid)
                state = st["state"] if st else "done"
            except Exception:
                # 顶层异常已在 run_project 内写入 state=error，这里仅避免线程崩溃
                state, results = ExecStatus.ERROR.value, []
            # P5-★4：异步任务结束后回调外部（流水线/调用方），best-effort 不阻塞
            executor.fire_webhook(
                wh_url,
                {
                    "event": "test_execution_finished",
                    "project_id": pid,
                    "project": proj.get("name"),
                    "batch_id": bid,
                    "state": state,
                    "summary": _mini_summary(results),
                    "status_url": f"/api/projects/{pid}/execute/status?batch_id={bid}",
                    "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

        threading.Thread(target=_bg, daemon=True).start()
        return {
            "ok": True,
            "async": True,
            "project": proj["name"],
            "batch_id": bid,
            "status_url": f"/api/projects/{pid}/execute/status?batch_id={bid}",
            "cancel_url": f"/api/projects/{pid}/execute/cancel",
            "active_url": f"/api/projects/{pid}/execute/active",
            "tasks_url": f"/api/projects/{pid}/execute/tasks",
            "webhook": bool(wh_url),
            "note": "执行已在后台启动；轮询 status_url 查看实时进度，POST cancel_url 可中断；"
            "结束时会回调 webhook_url（若配置）",
        }
    try:
        results = executor.run_project(
            pid,
            filters=payload.filters,
            max_workers=payload.max_workers,
            use_browser=payload.use_browser,
            include_archived=payload.include_archived,
            limit=payload.limit,
        )
    except ValueError as e:
        return {"ok": False, ExecStatus.ERROR.value: str(e)}
    meta = dict(getattr(executor, "last_meta", {}))
    out = {
        "ok": True,
        "project": proj["name"],
        "executed": len(results),
        "batch_id": meta.get("batch_id"),
        "meta": meta,
    }
    if payload.with_report:
        rep = reporter.build(
            pid,
            results,
            meta={
                "project": proj["name"],
                "batch_id": meta.get("batch_id"),
                "filters": payload.filters or {},
            },
        )
        out.update(report_id=rep["id"], summary=rep["summary"], html=rep["html_path"])
    return out


def _mini_summary(results):
    """P5-★4 回调用的轻量摘要：从执行结果聚合状态分布（与 reporter 口径一致）。"""
    if not results:
        return {"total": 0}

    def c(s):
        return sum(1 for r in results if r.get("status") == s)

    return {
        "total": len(results),
        ExecStatus.PASS.value: c(ExecStatus.PASS.value),
        ExecStatus.FAIL.value: c(ExecStatus.FAIL.value),
        ExecStatus.STRUCTURAL_ONLY.value: c(ExecStatus.STRUCTURAL_ONLY.value),
        ExecStatus.BLOCKED_AUTH.value: c(ExecStatus.BLOCKED_AUTH.value),
        ExecStatus.ERROR.value: c(ExecStatus.ERROR.value),
        ExecStatus.SKIPPED.value: c(ExecStatus.SKIPPED.value),
        ExecStatus.BLOCKED_REVIEW.value: c(ExecStatus.BLOCKED_REVIEW.value),
    }


@app.get("/api/projects/{pid}/execute/status")
def execute_status(pid: int, batch_id: str | None = None):
    """实时进度查询（D-②6）。

    - 指定 batch_id：返回该轮实时进度（registry 来源）；若已不在注册表（结束/重启），
      则从 runs 表重建终态分布（来源 runs），历史仍可查。
    - 不指定 batch_id：返回当前所有进行中的批次（等价于 /execute/active）。
    """
    if not batch_id:
        return {"ok": True, "active": executor.active_batches()}
    st = executor.get_batch_status(batch_id)
    if st:
        st["percent"] = round(100.0 * st["done"] / st["total"], 1) if st["total"] else 0.0
        # live=True → 来自进程内注册表（进行中/刚结束）；否则来自 run_batches 持久化表
        source = "registry" if st.get("live") else "run_batches"
        return {"ok": True, "status": st, "source": source}
    # 注册表与持久化表均无记录
    return {
        "ok": False,
        ExecStatus.ERROR.value: "batch not found（注册表无记录且 run_batches 表无该 batch_id）",
    }


@app.post("/api/projects/{pid}/execute/cancel")
def execute_cancel(pid: int, batch_id: str = Body(..., embed=True)):
    """中断某一轮正在执行的测试（D-②6）。

    执行循环会在下一条用例 / 下一个分块（最多 COMMIT_EVERY=50 条）边界停止，
    已执行结果已全部落库，不会丢失。
    """
    executor.cancel_batch(batch_id)
    return {
        "ok": True,
        "batch_id": batch_id,
        "cancelled": True,
        "note": "已请求中断；本轮将在下一条用例/下个分块边界停止，已执行结果已落库",
    }


@app.get("/api/projects/{pid}/execute/active")
def execute_active(pid: int):
    """进行中的执行批次列表（D-②6）。"""
    return {"ok": True, "active": executor.active_batches()}


@app.get("/api/projects/{pid}/execute/tasks")
def execute_tasks(pid: int):
    """异步任务清单（P5-★4）：含进行中与已结束的全部任务，供流水线/调用方查看执行履历。"""
    return {"ok": True, "tasks": executor.all_tasks(pid)}


@app.get("/api/projects/{pid}/filter_options")
def filter_options(pid: int):
    """可用筛选维度与取值分布（D-★6 配套）：告诉调用方能按什么筛、每档有多少条。"""
    conn = get_conn()
    cur = conn.cursor()
    dims = {}
    for col in ("priority", "module", "case_type", "test_type", "ctype", "review_status"):
        cur.execute(
            f"SELECT {col} k, COUNT(*) c FROM cases "
            f"WHERE project_id=? AND status!='archived' GROUP BY {col} ORDER BY c DESC",
            (pid,),
        )
        dims[col] = [{"value": r["k"], "count": r["c"]} for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND status!='archived'", (pid,))
    total = cur.fetchone()["c"]
    conn.close()
    return {
        "ok": True,
        "total": total,
        "dimensions": dims,
        "supported_fields": sorted(executor.FILTER_FIELDS),
    }


class SmokeReq(BaseModel):
    account: str = None
    password: str = None
    base_url: str = None


class ReviewReq(BaseModel):
    action: str  # approve | reject
    comment: str = None


class BulkReviewReq(BaseModel):
    action: str  # approve | reject
    comment: str = None
    ids: list = None  # 为空 → 审核当前全部非归档用例


@app.post("/api/projects/{pid}/cases/{cid}/review")
def review_case(pid: int, cid: int, payload: ReviewReq):
    """单条用例审核：approve / reject + 审核意见（C-★5）。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    if payload.action not in ("approve", "reject"):
        return {"ok": False, ExecStatus.ERROR.value: "action must be approve|reject"}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM cases WHERE id=? AND project_id=? AND status!='archived'", (cid, pid)
    )
    if not cur.fetchone():
        conn.close()
        return {"ok": False, ExecStatus.ERROR.value: "case not found or archived"}
    status = "approved" if payload.action == "approve" else "rejected"
    cur.execute(
        "UPDATE cases SET review_status=?, review_comment=? WHERE id=?",
        (status, payload.comment or "", cid),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "case_id": cid, "review_status": status}


@app.post("/api/projects/{pid}/cases/bulk_review")
def bulk_review(pid: int, payload: BulkReviewReq):
    """批量审核（C-★5）：ids 为空 → 审核当前全部非归档用例。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    if payload.action not in ("approve", "reject"):
        return {"ok": False, ExecStatus.ERROR.value: "action must be approve|reject"}
    status = "approved" if payload.action == "approve" else "rejected"
    conn = get_conn()
    cur = conn.cursor()
    params = [status, payload.comment or "", pid]
    if payload.ids:
        placeholders = ",".join("?" * len(payload.ids))
        cur.execute(
            f"UPDATE cases SET review_status=?, review_comment=? "
            f"WHERE project_id=? AND id IN ({placeholders}) AND status!='archived'",
            params + list(payload.ids),
        )
    else:
        cur.execute(
            "UPDATE cases SET review_status=?, review_comment=? "
            "WHERE project_id=? AND status!='archived'",
            (status, payload.comment or "", pid),
        )
    n = cur.rowcount
    conn.commit()
    conn.close()
    return {"ok": True, "updated": n, "review_status": status}


@app.get("/api/projects/{pid}/smoke")
def smoke_get(pid: int, base_url: str | None = None):
    """匿名冒烟：验证被测服务是否已启动且基本可用（不登录）。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    rep = smoke_module.smoke_project(proj, base_url=base_url)
    return {"ok": True, **rep}


@app.post("/api/projects/{pid}/smoke")
def smoke_post(pid: int, payload: SmokeReq):
    """登录冒烟：提供账号密码，验证登录态与受保护接口可用。"""
    proj = pm.get(pid)
    if not proj:
        return {"ok": False, ExecStatus.ERROR.value: "project not found"}
    rep = smoke_module.smoke_project(
        proj, account=payload.account, password=payload.password, base_url=payload.base_url
    )
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

    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.PLATFORM_PORT, reload=False)  # nosec B104  # 演示/局域网访问需绑定全部网卡
