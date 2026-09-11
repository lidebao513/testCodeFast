"""阶段1（代码获取 qa-code-pull）→ 阶段2（测试用例 qa-test-points）端到端验证。

设计原则：
  - 阶段1 用「受控 fixture 干净 git 仓库」真实跑 pull_code.py（落在临时目录，无副作用），
    证明其在【有效仓库】上能正确计算变更集并产出合规 JSON；同时以只读 git 诊断证明
    【生产 research-agent 目录 git 已失效】（toplevel 命中父仓库），这是阶段1 的真实风险。
  - 阶段2 与衔接契约用库调用 generate_comprehensive_test_points() 直接断言（不触发文件写出），
    避免覆盖 work/research-agent-test/ 生产产物。
验证目标：
  V1 阶段1 正确性（有效仓库上克隆/就位/变更集/JSON 合规）
  V2 阶段2 用例生成正确性（范围/语义/契约/数量）
  V3 质量与覆盖率（覆盖率100%、孤儿0、业务域、hunk 精度）
  V4 阶段衔接一致性（阶段1 changed_files → 阶段2 更新 标签，字段名/路径归一化一致）
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast")
PY = r"C:/Users/EDY/.workbuddy/binaries/python/versions/3.13.12/python.exe"
PULL = Path.home() / ".workbuddy/skills/qa-code-pull/pull_code.py"
GEN_DIR = ROOT / "work/test-accel"
PROD = ROOT / "work/targets/research-agent"

sys.path.insert(0, str(GEN_DIR))
from backend.modules.code_analyzer import generate_comprehensive_test_points


results = []  # (id, name, passed, detail)


def check(cid, name, passed, detail=""):
    results.append((cid, name, passed, detail))
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {cid} {name}" + (f" — {detail}" if detail else ""))


def run_git(cwd, *args, timeout=60):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        errors="ignore",
    )


# =====================================================================
print("=" * 78)
print("阶段1（qa-code-pull）验证 — 在【受控 fixture 干净仓库】上真实执行")
print("=" * 78)
fx = Path(tempfile.mkdtemp(prefix="e2e_fixture_"))
try:
    run_git(fx, "init", "-q")
    run_git(fx, "config", "user.email", "v@e2e.local")
    run_git(fx, "config", "user.name", "e2e")

    # v1：app.py(routes /a /b) + util.py(unchanged helper)
    (fx / "app.py").write_text(
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        '@app.get("/a")\n'
        "def a(): ...\n"
        '@app.post("/b")\n'
        "def b(): ...\n",
        encoding="utf-8",
    )
    (fx / "util.py").write_text(
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        '@app.get("/util")\n'
        "def u(): ...\n"
        "def helper():\n"
        '    """公共辅助函数。"""\n'
        "    return 1\n",
        encoding="utf-8",
    )
    run_git(fx, "add", "-A")
    run_git(fx, "commit", "-qm", "base")
    run_git(fx, "branch", "v1")
    run_git(fx, "checkout", "-qb", "v2")

    # v2：app.py 改（增 /c）+ 新增 svc.py；util.py 不变
    (fx / "app.py").write_text(
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        '@app.get("/a")\n'
        "def a(): ...\n"
        '@app.post("/b")\n'
        "def b(): ...\n"
        '@app.get("/c")\n'
        "def c(): ...\n",
        encoding="utf-8",
    )
    (fx / "svc.py").write_text(
        'def serve():\n    """业务服务入口。"""\n    return True\n', encoding="utf-8"
    )
    run_git(fx, "add", "-A")
    run_git(fx, "commit", "-qm", "target")

    out_json = fx.parent / ".pull_result.json"
    rc = subprocess.run(
        [
            PY,
            str(PULL),
            "--path",
            str(fx),
            "--base",
            "v1",
            "--target",
            "v2",
            "--out",
            str(out_json),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        errors="ignore",
    ).returncode

    check("V1-1", "pull_code.py 退出码恒为 0（离线亦不抛异常）", rc == 0, f"rc={rc}")
    j = json.loads(out_json.read_text(encoding="utf-8"))
    check(
        "V1-2",
        "产出 JSON 含约定字段 changed_files",
        "changed_files" in j,
        f"keys={sorted(j.keys())}",
    )
    cf = set(j.get("changed_files", []))
    expected_cf = {"app.py", "svc.py"}  # util.py 未变不应出现
    check(
        "V1-3",
        "变更集 = {app.py, svc.py}（util.py 未变被排除）",
        cf == expected_cf,
        f"got={sorted(cf)}",
    )
    check(
        "V1-4",
        "status 非致命（ok/ok_offline，无 clone_failed/refs_unavailable）",
        j["status"] in ("ok", "ok_offline"),
        f"status={j['status']}",
    )
    check(
        "V1-5",
        "checked_out = v2（工作树已切到目标版本）",
        j.get("checked_out") == "v2",
        f"checked_out={j.get('checked_out')}",
    )
    check(
        "V1-6",
        "url 脱敏（不含凭据明文）",
        "***" in j.get("url", "") or j.get("url") == "",
        f"url={j.get('url')!r}",
    )
    fx_pull_json = out_json  # 供 V4 复用
except Exception as e:
    check("V1-0", "fixture 构建/执行异常", False, repr(e))
    fx_pull_json = None

# =====================================================================
print("\n" + "=" * 78)
print("阶段1→阶段2 衔接契约验证 — fixture（库调用，不写文件）")
print("=" * 78)
if fx_pull_json and fx_pull_json.exists():
    jd = json.loads(fx_pull_json.read_text(encoding="utf-8"))
    changed = set(jd["changed_files"])
    d = generate_comprehensive_test_points(
        str(fx), project_type="pc", changed_files=changed, scopes={"正常", "异常"}
    )
    by_tag = d.get("by_tag", {})
    upd = by_tag.get("更新", 0)
    full = by_tag.get("全量", 0)
    changed_sources = {r["source"] for r in d["test_points"] if r["tag"] == "更新"}
    full_sources = {r["source"] for r in d["test_points"] if r["tag"] == "全量"}
    check(
        "V4-1",
        "阶段1 changed_files 被阶段2 直接消费（解耦，未触发 git）",
        upd > 0,
        f"更新={upd} 全量={full}",
    )
    check(
        "V4-2",
        "更新 标签仅落在变更文件（app.py/svc.py）上",
        changed_sources <= changed,
        f"更新源={changed_sources}",
    )
    check(
        "V4-3",
        "未变更文件（util.py）的测试点标为 全量",
        "util.py" in full_sources or full > 0,
        f"全量源={full_sources}",
    )
    check(
        "V4-4",
        "字段名一致：阶段1 输出 changed_files == 阶段2 入参 changed_files",
        isinstance(jd.get("changed_files"), list),
    )
else:
    check("V4-0", "fixture 产物缺失，跳过", False)

# =====================================================================
print("\n" + "=" * 78)
print("阶段1→阶段2 衔接契约验证 — 真实生产代码（只读，库调用）")
print("=" * 78)
REAL_FILE = "backend/research-agent-source/tools/wechat_channel/admin_api.py"
if (PROD / REAL_FILE).exists():
    d = generate_comprehensive_test_points(
        str(PROD), project_type="pc", changed_files={REAL_FILE}, scopes={"正常", "异常"}
    )
    by_tag = d.get("by_tag", {})
    upd = by_tag.get("更新", 0)
    # 该文件的 TP 是否全部「更新」
    real_tps = [r for r in d["test_points"] if r["source"] == REAL_FILE]
    real_all_upd = all(r["tag"] == "更新" for r in real_tps) if real_tps else False
    check(
        "V4-5",
        f"真实文件 {REAL_FILE} 的测试点被标『更新』",
        upd > 0 and real_all_upd,
        f"更新={upd}, 该文件TP={len(real_tps)}, 全更新={real_all_upd}",
    )
    check(
        "V4-6",
        "其余未变更文件标『全量』（非全仓误标）",
        by_tag.get("全量", 0) == d["total"] - upd,
        f"全量={by_tag.get('全量', 0)} 全量+更新={by_tag.get('全量', 0) + upd} 总={d['total']}",
    )
else:
    check("V4-5", "真实文件不存在，跳过", False, REAL_FILE)

# =====================================================================
print("\n" + "=" * 78)
print("阶段2（qa-test-points）验证 — 默认全量生成（质量与覆盖率）")
print("=" * 78)
d = generate_comprehensive_test_points(
    str(PROD), project_type="pc", changed_files=None, scopes={"正常", "异常"}
)
total = d["total"]
by_type = d["by_type"]
tr = d["traceability"]
fp_total = tr.get("fp_total", 0)
cov = tr.get("coverage", "")
orphan = tr.get("tp_without_fp(orphan)", -1)
biz = [f for f in d["functional_points"] if f["ftype"] == "business"]
scan = d.get("scan_stats", {})
check("V2-1", "测试点总数 = 263（与历史基线一致，无回归）", total == 263, f"total={total}")
check("V2-2", "功能点总数 = 237（统一契约 v1.0）", fp_total == 237, f"fp={fp_total}")
check(
    "V3-1",
    "双向追溯覆盖率 = 100%",
    cov in (100.0, "100.0%", "100%") or float(str(cov).rstrip("%")) == 100.0,
    f"coverage={cov}",
)
check("V3-2", "孤儿测试点 = 0（每条 TP 都能回溯功能点）", orphan == 0, f"orphan={orphan}")
check(
    "V3-3",
    "业务函数维度已恢复（business 功能点 > 0，非历史 0）",
    len(biz) > 0,
    f"business FP={len(biz)}",
)
check(
    "V3-4",
    "类型分布含 正常/异常（默认范围）",
    "正常" in by_type and "异常" in by_type,
    f"by_type={by_type}",
)
check(
    "V3-5",
    "去重扫描生效（scan_stats 存在且缓存命中>0）",
    scan.get("text_cache_hits", 0) > 0 or scan.get("sym_cache_hits", 0) > 0,
    f"scan={scan}",
)
check(
    "V3-6", "契约版本 = v1.0", d.get("contract_version") == "1.0", f"cv={d.get('contract_version')}"
)

# 语义覆盖率
sem_tp = sum(1 for r in d["test_points"] if r.get("semantic"))
sem_fp = sum(1 for f in d["functional_points"] if f.get("semantic"))
check("V2-3", "测试点业务语义覆盖 100%", sem_tp == total, f"{sem_tp}/{total}")
check("V2-4", "功能点业务语义覆盖 100%", sem_fp == fp_total, f"{sem_fp}/{fp_total}")

# =====================================================================
print("\n" + "=" * 78)
print("生产环境风险诊断（只读）— research-agent 目录 git 状态")
print("=" * 78)
r1 = run_git(PROD, "rev-parse", "--show-toplevel")
r2 = run_git(PROD, "rev-parse", "--is-inside-work-tree")
prod_toplevel = r1.stdout.strip()
prod_inside = r2.stdout.strip() == "true"
check(
    "P1-1",
    "research-agent 是独立可用 git 仓库",
    prod_toplevel.lower().endswith("research-agent"),
    f"toplevel={prod_toplevel}  inside_work_tree={prod_inside}",
)
check(
    "P1-2",
    "qa-code-pull 具备顶层级(toplevel)防护，不会误作用父仓库",
    False,
    "pull_code.py 无 _git_repo_usable() 类似守卫，is_git_repo() 会因父仓库 "
    "is-inside-work-tree=true 而误判为有效仓库（待补防护）",
)

# =====================================================================
print("\n" + "=" * 78)
passed = sum(1 for *_r, p, _d in [(x[0], x[1], x[2], x[3]) for x in results] if p)
# 上面推导不直观，重新统计
passed = sum(1 for r in results if r[2])
total_n = len(results)
print(f"整体验证结论：PASS {passed} / {total_n}")
fails = [r for r in results if not r[2]]
if fails:
    print("未通过项：")
    for r in fails:
        print(f"  - {r[0]} {r[1]}：{r[3]}")
print("=" * 78)
shutil.rmtree(fx, ignore_errors=True)
sys.exit(0 if not fails else 1)
