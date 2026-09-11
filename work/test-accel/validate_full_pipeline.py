"""【结构化测试用例】功能 · 全链路验证脚本

验证范围：
  1) 文件读写权限管控全链路（拉取代码前/中/后），每个阶段均做"真实写入探针"
     —— 调用真实的 pull_code._set_readonly 与 pull()，并以"对已有代码文件申请写权限"
        的方式实测当前是否可写（不修改文件内容）。
  2) 正常 + 边界 范围：真实调用 generate_comprehensive_test_points(ScopeSpec({正常,边界},None))
  3) 接口 范围：真实调用 generate_comprehensive_test_points(ScopeSpec(全四维, {api}))
  4) 结构化测试用例：运行 gen_structured_cases.py，校验 50 条用例的预期结果/源码出处/断言类型。

产物（落于 work/research-agent-test/validation/）：
  validation_summary.json      机读总览
  normal_boundary/test_points.json   正常+边界 测试点
  interface/test_points.json         接口 测试点
本脚本不直接生成 HTML 报告（由 gen_reports 调用本脚本的产出），但会打印关键结论。
"""

import datetime
import json
import os
import subprocess
import sys
import time


ROOT = r"C:/Users/EDY/WorkBuddy/testCodeFast/work/test-accel"
REPO = r"C:/Users/EDY/WorkBuddy/testCodeFast/work/targets/research-agent"
VAL_DIR = r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test/validation"
os.makedirs(VAL_DIR, exist_ok=True)
os.makedirs(os.path.join(VAL_DIR, "normal_boundary"), exist_ok=True)
os.makedirs(os.path.join(VAL_DIR, "interface"), exist_ok=True)

# 导入真实权限模块（qa-code-pull skill）
SKILL_DIR = r"C:/Users/EDY/.workbuddy/skills/qa-code-pull"
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)
import pull_code


# 导入真实代码分析模块（test-accel 平台）
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from backend.modules.code_analyzer import (
    ScopeSpec,
    _kind_of,
    generate_comprehensive_test_points,
)


PY = r"C:/Users/EDY/.workbuddy/binaries/python/versions/3.13.12/python.exe"
PROBE_FILE = os.path.join(REPO, "README.md")  # 已有代码文件，被 _set_readonly 置只读


# ----------------------------------------------------------------------------
# 写入探针（真实写能力测试，不修改文件内容）
# ----------------------------------------------------------------------------
def probe_writability():
    """真实写入能力探针：以读写方式打开"已存在的代码文件"（仅申请写权限、不写入内容）。
    Windows 下，只读文件申请 O_RDWR 会触发 PermissionError；可写则成功且不改动内容。
    返回 (allowed:bool, detail:str)。"""
    try:
        fd = os.open(PROBE_FILE, os.O_RDWR | getattr(os, "O_BINARY", 0))
        os.close(fd)
        return True, "以读写方式打开已有代码文件成功（未修改内容）→ 当前可写"
    except (PermissionError, OSError) as e:
        return False, f"写入被拒绝: {type(e).__name__}: {e} → 当前只读生效"


def probe_real_write():
    """真实内容写测试：在仓库内新建临时文件并写入内容后删除（仅在读写阶段使用）。
    返回 (allowed:bool, detail:str)。"""
    p = os.path.join(REPO, ".val_writetest.tmp")
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write("permission write probe @ " + datetime.datetime.now().isoformat())
        os.remove(p)
        return True, "新建并写入临时文件成功（已清理）→ 真实写入成功"
    except (PermissionError, OSError) as e:
        try:
            os.remove(p)
        except Exception:
            pass
        return False, f"写入被拒绝: {type(e).__name__}: {e}"


def validate_permissions():
    """权限全链路验证：拉取前(置只读)→拉取期间(临时读写)→真实 pull()→拉取后(恢复只读)。"""
    log = []
    # 基线：仓库当前只读位（Windows）
    try:
        import ctypes

        ro = bool(ctypes.windll.kernel32.GetFileAttributesW(PROBE_FILE) & 0x1)
        baseline = "readonly" if ro else "writable"
    except Exception:
        baseline = "unknown"

    # —— 阶段0：拉取代码前（功能约定：置只读，防误改被测代码）——
    pull_code._set_readonly(REPO, True)
    ok, detail = probe_writability()
    log.append(
        {
            "phase": "拉取前（置只读）",
            "expect_blocked": True,
            "write_allowed": ok,
            "passed": (not ok),
            "detail": detail,
        }
    )

    # —— 阶段1：拉取期间（功能约定：临时切读写，供 git 写仓库）——
    pull_code._set_readonly(REPO, False)
    ok2, detail2 = probe_writability()
    ok3, detail3 = probe_real_write()
    log.append(
        {
            "phase": "拉取期间（临时读写）",
            "expect_blocked": False,
            "write_allowed": ok2,
            "passed": (ok2 and ok3),
            "detail": detail2 + " ｜ " + detail3,
        }
    )

    # —— 阶段2：真实执行 pull()（WORKTREE 模式，离线安全，仍跑完整权限生命周期）——
    out_json = os.path.join(VAL_DIR, "pull_result.json")
    res = pull_code.pull(
        url="", local=REPO, base="HEAD", target="WORKTREE", deepen=0, out_json=out_json
    )
    perm = res.get("perm", {})
    log.append(
        {
            "phase": "真实 pull() 执行",
            "expect_blocked": None,
            "pull_status": res.get("status"),
            "perm": perm,
            "passed": (perm.get("restored_after_pull") is True),
            "detail": f"pull status={res.get('status')}；"
            f"changed_count={res.get('changed_count')}；"
            f"perm.readonly_before_pull={perm.get('readonly_before_pull')}；"
            f"perm.restored_after_pull={perm.get('restored_after_pull')}",
        }
    )

    # —— 阶段3：拉取后（功能约定：立即恢复只读）——
    ok4, detail4 = probe_writability()
    log.append(
        {
            "phase": "拉取后（恢复只读）",
            "expect_blocked": True,
            "write_allowed": ok4,
            "passed": (not ok4),
            "detail": detail4,
        }
    )

    # 收尾：确保仓库最终处于只读（功能既定终态）
    pull_code._set_readonly(REPO, True)

    overall = (
        all(x["passed"] for x in log if "passed" in x) and perm.get("restored_after_pull") is True
    )
    return {"baseline": baseline, "phases": log, "overall_passed": overall}


# ----------------------------------------------------------------------------
# 测试点范围生成（真实调用平台核心入口）
# ----------------------------------------------------------------------------
def run_scope(name, scope_spec):
    t0 = time.time()
    data = generate_comprehensive_test_points(
        REPO, project_type="pc", changed_files=set(), scopes=scope_spec
    )
    dt = round(time.time() - t0, 1)
    out = os.path.join(VAL_DIR, name, "test_points.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tr = data.get("traceability", {})
    # 来源种类分布（验证"接口"范围是否全部为 api）
    kind_dist = {}
    for r in data["test_points"]:
        k = _kind_of(r)
        kind_dist[k] = kind_dist.get(k, 0) + 1
    return {
        "name": name,
        "scope": str(scope_spec),
        "elapsed_sec": dt,
        "total": data["total"],
        "by_type": data["by_type"],
        "by_tag": data.get("by_tag", {}),
        "module_count": len(data["module_summary"]),
        "fp_total": tr.get("fp_total", 0),
        "coverage": tr.get("coverage", "-"),
        "orphan": tr.get("tp_without_fp(orphan)", 0),
        "kind_dist": kind_dist,
        "all_api": all(_kind_of(r) == "api" for r in data["test_points"]),
        "out": out,
    }


# ----------------------------------------------------------------------------
# 结构化测试用例校验（运行真实生成器并核对）
# ----------------------------------------------------------------------------
def validate_structured_cases():
    sc_json = os.path.join(ROOT, "..", "research-agent-test", "structured_cases.json")
    sc_json = os.path.abspath(sc_json)
    # 运行真实生成器（产出 structured_cases.json + HTML）
    subprocess.run(
        [PY, os.path.join(ROOT, "gen_structured_cases.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if not os.path.exists(sc_json):
        return {"ok": False, "error": "structured_cases.json 未生成"}
    data = json.load(open(sc_json, encoding="utf-8"))
    cases = data["cases"]
    n = len(cases)
    missing_expect = [c["case_id"] for c in cases if not (c.get("expected_result") or "").strip()]
    missing_ref = [c["case_id"] for c in cases if not (c.get("source_ref") or "").strip()]
    missing_assert = [c["case_id"] for c in cases if not (c.get("assertion_type") or "").strip()]
    bad_kind = [c["case_id"] for c in cases if c.get("kind") != "api"]
    by_scope = {}
    for c in cases:
        by_scope[c["scope"]] = by_scope.get(c["scope"], 0) + 1
    return {
        "ok": (
            n > 0 and not missing_expect and not missing_ref and not missing_assert and not bad_kind
        ),
        "case_count": n,
        "modules": len(data.get("modules", [])),
        "by_scope": by_scope,
        "missing_expect": missing_expect,
        "missing_ref": missing_ref,
        "missing_assert": missing_assert,
        "non_api_cases": bad_kind,
        "all_api": (len(bad_kind) == 0),
    }


def main():
    summary = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "target": "research-agent",
        "repo": REPO,
    }

    print("=" * 70)
    print("[1/4] 权限全链路验证（含真实写入探针）...")
    perm = validate_permissions()
    summary["permission"] = perm
    print(f"      基线状态={perm['baseline']}；整体通过={perm['overall_passed']}")
    for ph in perm["phases"]:
        print(
            f"      - {ph['phase']}: write_allowed={ph.get('write_allowed')} "
            f"passed={ph.get('passed')} | {ph['detail'][:80]}"
        )

    print("[2/4] 正常+边界 范围测试点生成...")
    nb = run_scope("normal_boundary", ScopeSpec({"正常", "边界"}, None))
    summary["normal_boundary"] = nb
    print(
        f"      总数={nb['total']} by_type={nb['by_type']} 模块={nb['module_count']} "
        f"覆盖={nb['coverage']} 孤儿={nb['orphan']}"
    )

    print("[3/4] 接口 范围测试点生成...")
    iface = run_scope("interface", ScopeSpec({"正常", "异常", "安全", "边界"}, {"api"}))
    summary["interface"] = iface
    print(
        f"      总数={iface['total']} by_type={iface['by_type']} 全部api={iface['all_api']} "
        f"kind_dist={iface['kind_dist']}"
    )

    print("[4/4] 结构化测试用例校验...")
    sc = validate_structured_cases()
    summary["structured_cases"] = sc
    print(f"      用例数={sc.get('case_count')} 全部api={sc.get('all_api')} ok={sc.get('ok')}")

    # 总体结论（在落盘前计算，保证摘要完整可复跑）
    overall = (
        perm["overall_passed"]
        and nb["total"] > 0
        and iface["total"] > 0
        and iface["all_api"]
        and sc.get("ok")
    )
    summary["overall_passed"] = overall
    with open(os.path.join(VAL_DIR, "validation_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("DONE. 验证摘要 ->", os.path.join(VAL_DIR, "validation_summary.json"))
    print("整体验证结论：", "通过 ✅" if overall else "存在未通过项 ❌")
    return summary


if __name__ == "__main__":
    main()
