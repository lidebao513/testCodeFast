"""依据完整代码重新生成全面测试点，并与「上次生成的测试点（报告第二章 9 模块级）」做对比。

用法：
    python gen_test_points.py
产出（落于 research-agent-test/）：
    TEST_POINTS_COMPARE.md   旧版 vs 新版 分段对比（含差异分析）
    TEST_POINTS_NEW.md       新版全部测试点逐条清单
    TEST_POINTS_COMPARE.html 旧/新并排可视化对比
    test_points_new.json     新版结构化数据
"""

import json
import os
import sys
from pathlib import Path


# 允许以脚本方式直接 import 平台模块
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from backend.core.enums import (
    ALL_TP_TYPES,
    DEFAULT_SCOPE,
    FULL_SCOPE,
    SCOPE_KEY_ALL,
    Tag,
)
from backend.modules.code_analyzer import (
    ScopeSpec,
    compute_diff_changed_files,
    compute_diff_hunks,
    generate_comprehensive_test_points,
)


# 被测仓库路径（可被 qa-code-pull 的产出或环境变量覆盖；默认项目内置路径）
REPO = os.environ.get(
    "TP_REPO_PATH", r"C:/Users/EDY/WorkBuddy/testCodeFast/work/targets/research-agent"
)
OUT = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test")
OUT.mkdir(parents=True, exist_ok=True)

# 本次拉取代码的变更基线：base..target 的 diff 用于识别『更新』测试点
# 可由环境变量覆盖（与 qa-code-pull 的 DIFF_BASE/DIFF_TARGET 是一致的契约值）
DIFF_BASE = os.environ.get("TP_DIFF_BASE", "test-20260906")
DIFF_TARGET = os.environ.get("TP_DIFF_TARGET", "test-20260907")

# 可选：直接消费 qa-code-pull 产出的变更文件集合（解耦！不 import qa-code-pull，
# 仅读其 result JSON 的 changed_files 列表）。为空则内部用 git diff 计算。
CHANGED_FILES_JSON = os.environ.get("CHANGED_FILES_JSON", "")


# ============ 类型标识（全量 / 更新）可视化渲染 ============
# 全量：本次完整测试的内容（代码未变更部分，常规全量回归）
# 更新：本次仅变更 / 增量测试的内容（source 命中 base..target diff）
def _badge_md(tag: str) -> str:
    """Markdown 版徽章：内联样式，支持彩色徽章预览。"""
    if tag == Tag.UPDATE.value:
        return (
            '<span style="color:#ffb454;font-weight:700;'
            "border:1px solid #ffb454;border-radius:4px;padding:1px 7px;"
            'font-size:12px;white-space:nowrap">更新</span>'
        )
    return (
        '<span style="color:#3ecf8e;font-weight:700;'
        "border:1px solid #3ecf8e;border-radius:4px;padding:1px 7px;"
        'font-size:12px;white-space:nowrap">全量</span>'
    )


def _badge_html(tag: str) -> str:
    """HTML 版徽章：CSS 类名。"""
    cls = "b-upd" if tag == Tag.UPDATE.value else "b-full"
    return f'<span class="{cls}">{tag}</span>'


def _trunc(s: str, n: int) -> str:
    """控制台/表格用：超长截断并加省略号。"""
    s = s or ""
    return s if len(s) <= n else s[: n - 1] + "…"


# ============ 测试点范围参数（Scope） ============
# 行为维度（tp_type）可选值：正常 / 异常 / 安全 / 边界（见 backend.core.enums.TPType）
# 默认范围：正常 + 安全 + 边界 + 异常（行为维度），不限来源（与 testgen-service 对齐 · G-14）
# 枚举以 backend.core.enums 为唯一真值源；本文件仅引用，不再硬编码常量。
# 注意：「接口」**不是**范围关键词（历史上曾用作来源筛选）。现改为独立执行层枚举
# VerifyLayer；接口来源筛选可由 verify_layer=接口（=ftype∈{api,business}）等价覆盖。


def resolve_scope(input_text: str):
    """依据输入文本解析本次测试点范围（ScopeSpec）。

    返回 ScopeSpec(tp_types, kinds)：tp_types 为行为维度集合，kinds 为来源过滤
    （None=不限）。generate_comprehensive_test_points(scopes=...) 据此过滤。
    不会返回空集。仅按行为维度过滤；接口/UI 的「执行层」选择由 VerifyLayer 负责。
    """
    text = (input_text or "").strip()
    # 1) 显式「全部/全量」→ 四种行为维度都生成、不限来源
    if text and any(k in text for k in SCOPE_KEY_ALL):
        return ScopeSpec(set(FULL_SCOPE), None)
    mentioned = {s for s in ALL_TP_TYPES if s in text}
    # 2) 仅行为维度（或默认）→ 对应行为维度，不限来源
    if mentioned:
        return ScopeSpec(mentioned, None)
    return ScopeSpec(set(DEFAULT_SCOPE), None)


def _scope_str(scopes) -> str:
    """把 ScopeSpec / 旧式集合 / None 渲染成可读的「范围」字符串。"""
    if scopes is None:
        return "全部"
    if isinstance(scopes, ScopeSpec):
        parts = sorted(scopes.tp_types)
        return "、".join(parts) if parts else "全部"
    return "、".join(sorted(scopes)) if scopes else "全部"


# 范围来源：优先命令行参数，其次环境变量 TP_SCOPE，再次本常量（空=按默认解析）
SCOPE_INPUT = os.environ.get("TP_SCOPE", "")
if len(sys.argv) > 1:
    SCOPE_INPUT = sys.argv[1]


def _load_changed_files(json_path: str, repo: str, base: str, target: str):
    """获取变更文件集合（用于『更新』标签）。

    解耦设计：若提供了 qa-code-pull 产出的 result JSON（CHANGED_FILES_JSON），
    直接读取其中的 changed_files 列表，**不调用任何 qa-code-pull 代码、不发 git**；
    否则回退到内部 read-only `git diff --name-only base..target` 计算。
    """
    if json_path and Path(json_path).exists():
        try:
            data = json.loads(Path(json_path).read_text(encoding="utf-8"))
            cf = data["changed_files"] if isinstance(data, dict) else data
            if isinstance(cf, list) and cf:
                print(f"      直接消费 qa-code-pull 产物 {json_path}（解耦，不调用 git）")
                return set(cf)
        except Exception:
            pass
    print(f"      内部 git diff --name-only {base}..{target} 计算（read-only）")
    return compute_diff_changed_files(repo, base, target)


# ===================== 旧版基线（上次生成：报告第二章） =====================
OLD = [
    {
        "module": "对话核心",
        "points": "自我介绍 / 天气 / 股票",
        "type": "正常",
        "scenes": "F-A1~A3",
        "expect": "正常返回并命中业务关键词",
    },
    {
        "module": "请假休假（核心业务）",
        "points": "年假申请 / 加班申请 / 余额 / 规则",
        "type": "正常+边界",
        "scenes": "F-B1~B4",
        "expect": "提交成功/返回余额与取整规则",
    },
    {
        "module": "待办审批流",
        "points": "我的待办 / 已办(按状态) / 取消申请",
        "type": "正常+异常",
        "scenes": "F-C1~C3",
        "expect": "列表返回 / 取消回滚(测试数据)",
    },
    {
        "module": "邮件日程",
        "points": "邮件会议整理成日程",
        "type": "正常",
        "scenes": "F-D1",
        "expect": "日程项生成",
    },
    {
        "module": "知识库/监管",
        "points": "审计知识库检索 / 监管政策自动化",
        "type": "正常",
        "scenes": "F-E1~E2",
        "expect": "命中知识库制度 / 定时任务配置说明",
    },
    {
        "module": "经营分析/数据",
        "points": "机构经营 / 缴费达成率 / 大额未审批 / 人员数据",
        "type": "正常+空态边界",
        "scenes": "F-F1~F4",
        "expect": "数据返回 / 空态友好提示",
    },
    {
        "module": "多智能体",
        "points": "反洗钱 SQL 子 agent",
        "type": "正常",
        "scenes": "F-G1",
        "expect": "自然语言→SQL 生成",
    },
    {
        "module": "汇报文档",
        "points": "长文报告(≥800字)",
        "type": "长度边界",
        "scenes": "F-H1",
        "expect": "以文档产物(下载/导出)形式完整交付",
    },
    {
        "module": "异常/安全/健壮",
        "points": "@mention熔断 / 工具终止 / 注入防护 / 历史重建 / 长输入",
        "type": "异常",
        "scenes": "F-I1~I5",
        "expect": "不挂起 / 拒绝注入 / 不崩溃",
    },
]


def main():
    # 解析本次测试点范围（Scope）
    scopes = resolve_scope(SCOPE_INPUT)
    scope_src = (SCOPE_INPUT or "(未指定 → 默认)").strip()
    print(f"[scope] 范围输入 = {scope_src}  →  生效范围 = {_scope_str(scopes)}（{scopes!r}）")

    # 本次变更文件集合（用于打『更新』标签）—— 优先消费 qa-code-pull 产物，否则内部计算
    src = CHANGED_FILES_JSON or f"内部 git diff {DIFF_BASE}..{DIFF_TARGET}"
    print(f"[0/5] 获取变更文件集合（来源：{src}）...")
    changed = _load_changed_files(CHANGED_FILES_JSON, REPO, DIFF_BASE, DIFF_TARGET)
    print(f"      变更文件数 = {len(changed)}")
    if not changed:
        print("      ⚠ 警告：变更文件数为 0 → 本次不会有任何『更新』测试点（全部标『全量』）。")
        print(
            f"         常见原因：base/target ref 不存在或不可解析。请用 "
            f"`git -C {REPO} rev-parse {DIFF_BASE} {DIFF_TARGET}` 核对，"
            f"或通过 TP_DIFF_BASE / TP_DIFF_TARGET 指定有效提交。"
        )

    # 解析本次 diff 的 base/target（用于 hunk 级精准打标 B1）
    diff_base, diff_target = DIFF_BASE, DIFF_TARGET
    if CHANGED_FILES_JSON and Path(CHANGED_FILES_JSON).exists():
        try:
            _jd = json.loads(Path(CHANGED_FILES_JSON).read_text(encoding="utf-8"))
            if isinstance(_jd, dict):
                diff_base = _jd.get("base", diff_base) or diff_base
                diff_target = _jd.get("target", diff_target) or diff_target
        except Exception:
            pass
    print(f"      计算 hunk 行范围（git diff -U0 {diff_base}..{diff_target}）...")
    hunks = compute_diff_hunks(REPO, diff_base, diff_target)
    n_hunk_files = len(hunks)
    n_hunk_segs = sum(len(v) for v in hunks.values())
    print(
        f"      hunk 级打标可用：{n_hunk_files} 个变更文件 / {n_hunk_segs} 段 hunk"
        f"（无 hunk 时自动降级为文件级）"
    )

    print(f"[1/5] 扫描完整代码（{REPO}）并生成全面测试点 ...")
    data = generate_comprehensive_test_points(
        REPO,
        project_type="pc",
        changed_files=changed,
        scopes=scopes,
        diff_hunks=hunks,
        diff_target=diff_target,
    )
    total = data["total"]
    by_type = data["by_type"]
    by_tag = data.get("by_tag", {})
    modules = data["module_summary"]
    print(f"      新版测试点总数 = {total}（按类型: {by_type}）")
    print(f"      标签分布 = 全量 {by_tag.get('全量', 0)} / 更新 {by_tag.get('更新', 0)}")
    print(f"      覆盖模块数 = {len(modules)}")

    # A2 双向追溯 + C1 去重扫描
    tr = data.get("traceability", {})
    ss = data.get("scan_stats", {})
    print(
        f"      功能点数 = {tr.get('fp_total', 0)}（统一契约 v{data.get('contract_version', '-')}）"
        f"  派生覆盖 = {tr.get('fp_with_tp', 0)}/{tr.get('fp_total', 0)}"
        f"（{tr.get('coverage', '-')}）  孤儿测试点 = {tr.get('tp_without_fp(orphan)', 0)}"
    )
    print(
        f"      去重扫描 = 读取文件 {ss.get('files_read', 0)} 个 / AST 解析 {ss.get('ast_parses', 0)} 次"
        f" / 缓存命中 文本 {ss.get('text_cache_hits', 0)} + 符号 {ss.get('sym_cache_hits', 0)}"
    )

    # ---- JSON ----
    (OUT / "test_points_new.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---- 功能点清单（A1 业务语义 + A2 追溯）----
    print("[1.5/5] 写出功能点清单 FUNCTIONAL_POINTS.md ...")
    _write_fp_md(data)

    # ---- 新版完整清单 MD ----
    print("[2/5] 写出新版完整清单 TEST_POINTS_NEW.md ...")
    _write_new_md(data, changed, scopes)

    # ---- 旧/新对比 MD ----
    print("[3/5] 写出对比报告 TEST_POINTS_COMPARE.md ...")
    _write_compare_md(data, scopes)

    # ---- 旧/新并排 HTML ----
    print("[4/5] 写出并排可视化 TEST_POINTS_COMPARE.html ...")
    _write_compare_html(data, scopes)

    # ---- 重新打印最新测试点内容（含标签）----
    print("[5/5] 打印最新测试点内容（含 全量/更新 标签）...")
    _print_latest(data, scopes)

    print("DONE. 产物位于:", OUT)


def _print_latest(data, scopes=None):
    """在控制台重新打印最新测试点内容，清晰标识 全量 / 更新 两类。"""
    by_tag = data.get("by_tag", {})
    n_full = by_tag.get("全量", 0)
    n_upd = by_tag.get("更新", 0)
    scope_str = _scope_str(scopes)
    print("\n" + "=" * 72)
    print(f"最新测试点内容（v2 全面覆盖）  总数={data['total']}  [全量]={n_full}  [更新]={n_upd}")
    print(f"本轮范围（Scope）= {scope_str}")
    print("=" * 72)
    print("类型标识图例： [全量] = 本次完整测试内容 | [更新] = 本次仅变更/增量测试内容")
    print(
        f"             （『更新』= 其底层路由/函数源码行区间被 {DIFF_BASE}..{DIFF_TARGET} 的"
        f" hunk 覆盖；hunk 级精准打标，非整文件误标）\n"
    )

    print("【模块汇总（含『更新』命中数，可按此筛选变更测试点）】")
    print(f"{'模块':<26}{'总数':>5}{'更新':>5}{'API':>5}{'业务':>5}{'前端':>5}")
    print("-" * 60)
    for m in data["module_summary"]:
        print(
            f"{m['module']:<26}{m['total']:>5}{m.get('updated', 0):>5}"
            f"{m['api']:>5}{m['business']:>5}{m['frontend']:>5}"
        )

    updated = [r for r in data["test_points"] if r["tag"] == Tag.UPDATE.value]
    print(f"\n【[更新] 测试点（本次代码对比识别出的变更测试点，共 {len(updated)} 条）】")
    print(
        f"{'ID':<8}{'标识':<6}{'业务语义':<24}{'模块':<18}{'区域/路由/函数':<30}{'方法':<8}{'类型'}"
    )
    print("-" * 110)
    for r in updated:
        print(
            f"{r['id']:<8}{('[' + r['tag'] + ']'):<6}{_trunc(r.get('semantic', ''), 23):<24}"
            f"{_trunc(r['module'], 17):<18}{_trunc(r['area'], 29):<30}"
            f"{r['method']:<8}{r['tp_type']}"
        )

    full = [r for r in data["test_points"] if r["tag"] == Tag.FULL.value]
    print(f"\n【[全量] 测试点：{len(full)} 条（完整回归集，逐条见 TEST_POINTS_NEW.md）】")
    print("前 12 条示例：")
    for r in full[:12]:
        print(
            f"  {r['id']:<8}{('[' + r['tag'] + ']'):<6}{_trunc(r.get('semantic', ''), 23):<24}"
            f"{_trunc(r['module'], 17):<18}{_trunc(r['area'], 29):<30}"
            f"{r['method']:<8}{r['tp_type']}"
        )

    # A2 双向追溯：派生测试点最多的功能点（Top 8）
    fps = data.get("functional_points", [])
    if fps:
        tr = data.get("traceability", {})
        print(
            f"\n【功能点 → 测试点 追溯（A2）】功能点 {tr.get('fp_total', 0)} 个，"
            f"覆盖率 {tr.get('coverage', '-')}，孤儿测试点 "
            f"{tr.get('tp_without_fp(orphan)', 0)} 条"
        )
        print(f"{'fp_id':<13}{'类型':<11}{'业务语义':<24}{'功能点':<34}{'测试点':>6}")
        print("-" * 100)
        for f in fps[:8]:
            print(
                f"{f['fp_id']:<13}{f['ftype']:<11}{_trunc(f.get('semantic', ''), 23):<24}"
                f"{_trunc(f.get('title') or f['name'], 33):<34}"
                f"{len(f.get('test_points', [])):>6}"
            )
        print("（完整矩阵见 FUNCTIONAL_POINTS.md / TEST_POINTS_COMPARE.html 第五节）")
    print("=" * 72)


def _write_fp_md(data):
    """功能点清单（A1 业务语义 + A2 双向追溯）：每个功能点 → 其派生的测试点。"""
    fps = data.get("functional_points", [])
    tr = data.get("traceability", {})
    L = [
        "# 功能点清单（统一契约 v%s · A1 业务语义 + A2 双向追溯）\n"
        % data.get("contract_version", "1.0"),
        "> 由 `code_analyzer` 单次扫描（C1 去重）产出：功能点与测试点**同源同一次 AST**，"
        "测试点通过 `fp_id` 指回功能点，功能点反查其派生测试点。\n",
        f"> 功能点总数 **{tr.get('fp_total', 0)}**；"
        f"本轮范围内有派生测试点的功能点 **{tr.get('fp_with_tp', 0)}**"
        f"（覆盖率 {tr.get('coverage', '-')}）；"
        f"派生测试点最多的功能点含 **{tr.get('max_tp_per_fp', 0)}** 条测试点；"
        f"孤儿测试点（无来源功能点）**{tr.get('tp_without_fp(orphan)', 0)}** 条。\n",
        f"> 说明：{tr.get('note', '')}\n",
        "\n## 功能点 → 测试点（双向追溯矩阵）\n",
        "| # | fp_id | 类型 | 业务语义 | 功能点 | 文件 | 派生测试点 | 测试点 ID |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, fp in enumerate(fps, 1):
        tps = fp.get("test_points", [])
        ids = "、".join(tps[:8]) + (" …" if len(tps) > 8 else "")
        L.append(
            f"| {i} | `{fp['fp_id']}` | {fp['ftype']} | {fp.get('semantic', '')} | "
            f"{fp.get('title') or fp['name']} | `{fp['file_path']}` | "
            f"**{len(tps)}** | {ids or '—（本轮 Scope 未覆盖）'} |"
        )
    if not fps:
        L.append("| — | — | — | — | 无功能点 | — | 0 | — |")
    (OUT / "FUNCTIONAL_POINTS.md").write_text("\n".join(L), encoding="utf-8")


def _write_new_md(data, changed=None, scopes=None):
    by_tag = data.get("by_tag", {})
    total_full = by_tag.get("全量", 0)
    total_upd = by_tag.get("更新", 0)
    scope_str = _scope_str(scopes)
    lines = [
        "# 新版测试点清单（依据完整代码生成 · v2 全面覆盖）\n",
        "> 生成方式：`code_analyzer.generate_comprehensive_test_points()` "
        "对完整仓库静态扫描派生。\n",
        f"> **测试点范围（Scope）**：{scope_str}（可选项：正常 / 异常 / 安全 / 边界；"
        f"默认 正常+安全+边界+异常）。\n",
        f"> 总计 **{data['total']}** 条测试点；按类型："
        + "、".join(f"{k} {v}" for k, v in data["by_type"].items())
        + "\n",
    ]

    # 测试点范围（一眼区分本次测试的具体范围）
    bt = data.get("by_tag", {})
    lines.append("\n> ## 本次测试范围概览\n")
    lines.append(
        f"> - {_badge_md('全量')} **全量（本次完整测试内容）**：**{total_full}** 条 —— "
        f"代码未变更部分，常规全量回归执行。\n"
    )
    lines.append(
        f"> - {_badge_md('更新')} **更新（本次仅变更/增量测试内容）**：**{total_upd}** 条 —— "
        f"其底层路由/函数的源码行区间被 `{DIFF_BASE}..{DIFF_TARGET}` 的 hunk 覆盖"
        f"（hunk 级精准打标，避免整文件误标），优先回归 / 变更影响面验证。\n"
    )
    if changed is not None:
        lines.append(f"> - 本次 diff 变更文件数：**{len(changed)}**（命中即标『更新』）。\n")

    # 类型标识图例
    lines.append("\n> ## 类型标识图例（每一项测试点旁均带此标识）\n")
    lines.append(f"> - {_badge_md('全量')} ＝ **全量**：本次完整测试的内容。\n")
    lines.append(f"> - {_badge_md('更新')} ＝ **更新**：本次仅变更或增量测试的内容。\n")
    lines.append(
        "> 在下方「逐条测试点」表的 **类型标识** 列，可一眼区分每条的归属；"
        "也可按该列筛选「全量 / 更新」两类。\n"
    )
    lines.append("\n> ## 业务语义说明（B2）\n")
    lines.append(
        "> 每条测试点的 **业务语义** 列 ＝ **业务域 · 业务动作**"
        "（如 `对话/会话 · 提交/创建`），由接口路径关键词与 HTTP 方法推导；"
        "**预期** 列同时给出「实现函数名 + docstring」参考，"
        "便于阶段3用例生成与阶段6报告锚定真实业务场景。\n"
    )

    lines.append("\n## 模块汇总\n")
    lines.append(
        "| 模块 | 测试点总数 | 更新数 | API维 | 业务函数维 | 前端维 | 覆盖面积(路由/函数) |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for m in data["module_summary"]:
        areas = "、".join(m["areas"][:8]) + (" …" if len(m["areas"]) > 8 else "")
        lines.append(
            f"| {m['module']} | {m['total']} | {m.get('updated', 0)} | "
            f"{m['api']} | {m['business']} | {m['frontend']} | {areas} |"
        )

    lines.append("\n## 逐条测试点（每项旁带类型标识 + 业务语义 + 来源功能点）\n")
    lines.append(
        "| ID | 来源功能点 | 类型标识 | 业务语义 | 模块 | 区域/路由/函数 | 方法 | 类型 | 维度 | 预期 |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in data["test_points"]:
        tag = r.get("tag", Tag.FULL.value)
        sem = r.get("semantic", "")
        fp = f"`{r.get('fp_id', '—')}` {r.get('fp_title', '')}"
        lines.append(
            f"| {r['id']} | {fp} | {_badge_md(tag)} | {sem} | {r['module']} | `{r['area']}` | "
            f"{r['method']} | {r['tp_type']} | {r['dimension']} | {r['expect']} |"
        )
    tr = data.get("traceability", {})
    lines.append(
        f"\n> **双向追溯（A2）**：功能点 {tr.get('fp_total', 0)} 个，"
        f"本轮范围内派生出测试点的 {tr.get('fp_with_tp', 0)} 个"
        f"（{tr.get('coverage', '-')}），孤儿测试点 "
        f"{tr.get('tp_without_fp(orphan)', 0)} 条；"
        f"完整「功能点 → 测试点」矩阵见 **FUNCTIONAL_POINTS.md**。\n"
    )
    (OUT / "TEST_POINTS_NEW.md").write_text("\n".join(lines), encoding="utf-8")


def _write_compare_md(data, scopes=None):
    scope_str = _scope_str(scopes)
    L = []
    L.append("# 测试点生成 · 旧版 vs 新版 对比报告\n")
    L.append(
        "> 目的：审阅发现上次生成的测试点「数量偏少、基于全部代码的覆盖不充分」。"
        "本次优化 `code_analyzer` 的测试点生成逻辑（新增 v2 全面生成），"
        "**依据完整代码重新生成**一套更全面、覆盖更充分的测试点，并与上次结果并排对比。\n"
    )
    L.append(
        f"> **本轮测试点范围（Scope）**：{scope_str}"
        f"（可选项：正常 / 异常 / 安全 / 边界；默认 正常+安全+边界+异常）。\n"
    )

    # 旧版
    L.append("\n## 一、旧版（上次生成 · 报告第二章 · 9 模块级测试点）\n")
    L.append("| 功能模块 | 测试点 | 类型 | 场景 | 预期 |")
    L.append("|---|---|---|---|---|")
    for o in OLD:
        L.append(f"| {o['module']} | {o['points']} | {o['type']} | {o['scenes']} | {o['expect']} |")
    L.append(
        f"\n> 旧版合计：**{len(OLD)} 条模块级聚合点**，且每条仅 1 个笼统预期，"
        "未按接口/函数/前端逐条展开，属「模块级抽样」而非「代码级覆盖」。\n"
    )

    # 新版
    L.append("\n## 二、新版（本次依据完整代码生成 · v2 全面覆盖）\n")
    L.append(
        f"**总量 {data['total']} 条测试点**，按类型："
        + "、".join(f"{k} {v}" for k, v in data["by_type"].items())
        + "\n"
    )
    L.append("\n### 2.1 模块汇总（覆盖深度）\n")
    L.append("| 模块 | 测试点总数 | API维 | 业务函数维 | 前端维 | 覆盖面积 |")
    L.append("|---|---|---|---|---|---|")
    for m in data["module_summary"]:
        areas = "、".join(m["areas"][:6]) + (" …" if len(m["areas"]) > 6 else "")
        L.append(
            f"| {m['module']} | {m['total']} | {m['api']} | "
            f"{m['business']} | {m['frontend']} | {areas} |"
        )

    L.append("\n### 2.2 各模块代表测试点（节选，完整见 TEST_POINTS_NEW.md）\n")
    L.append("| ID | 业务语义 | 模块 | 区域 | 方法 | 类型 | 维度 | 预期 |")
    L.append("|---|---|---|---|---|---|---|---|")
    # 每模块取前 2 条作代表
    seen = {}
    for r in data["test_points"]:
        mod = r["module"]
        if seen.get(mod, 0) >= 2:
            continue
        seen[mod] = seen.get(mod, 0) + 1
        L.append(
            f"| {r['id']} | {r.get('semantic', '')} | {mod} | `{r['area']}` | "
            f"{r['method']} | {r['tp_type']} | {r['dimension']} | {r['expect']} |"
        )

    # 差异分析
    L.append("\n## 三、新旧差异对比\n")
    L.append("| 维度 | 旧版（上次） | 新版（本次） | 变化 |")
    L.append("|---|---|---|---|")
    L.append(
        f"| 测试点数量 | {len(OLD)} 条模块级 | {data['total']} 条逐项 | "
        f"+{data['total'] - len(OLD)}（约 {data['total'] // len(OLD)}×） |"
    )
    L.append("| 覆盖粒度 | 模块级抽样（9 模块） | 代码级（API路由+业务函数+前端） | 由粗到细 |")
    L.append("| 测试维度 | 单一笼统预期 | 正常/边界/异常/安全 四维展开 | 维度补齐 |")
    L.append("| 来源 | 手工归纳业务场景 | 完整代码静态扫描派生 | 可复现、随代码演进 |")
    L.append("| 路由覆盖 | 仅线上对话可见业务（~24 场景） | 全仓 125 路由 × 多维 | 全 API 面 |")
    L.append("| 业务函数 | 未覆盖 | 抽取 14 个核心模块顶层函数 | 逻辑面补齐 |")
    L.append("| 前端 | 未覆盖 | 页面可达 + 组件交互 | UI 面补齐 |")
    L.append(
        "\n> 结论：新版测试点从「9 个模块级抽样」升级为「"
        f"{data['total']} 条代码级逐项 + 四维维度 + 全 API/业务/前端覆盖」，"
        "覆盖充分性与可复现性显著提升，且与代码变更同步。\n"
    )
    L.append(
        f"> 附：**标签属性**已加入每条测试点——「全量」"
        f"{data.get('by_tag', {}).get('全量', 0)} 条 / 「更新」"
        f"{data.get('by_tag', {}).get('更新', 0)} 条"
        f"（本次 {DIFF_BASE}..{DIFF_TARGET} diff 覆盖其底层路由/函数 hunk 才标『更新』），"
        "可在测试列表/JSON 中按标签筛选本次变更测试点。\n"
    )

    (OUT / "TEST_POINTS_COMPARE.md").write_text("\n".join(L), encoding="utf-8")


def _write_compare_html(data, scopes=None):
    scope_str = _scope_str(scopes)
    # 旧版表
    old_rows = "".join(
        f"<tr><td>{o['module']}</td><td>{o['points']}</td><td>{o['type']}</td>"
        f"<td>{o['scenes']}</td><td>{o['expect']}</td></tr>"
        for o in OLD
    )
    # 新版模块汇总
    new_mod = "".join(
        f"<tr><td>{m['module']}</td><td>{m['total']}</td><td>{m['api']}</td>"
        f"<td>{m['business']}</td><td>{m['frontend']}</td>"
        f"<td>{'、'.join(m['areas'][:6])}{' …' if len(m['areas']) > 6 else ''}</td></tr>"
        for m in data["module_summary"]
    )
    # 差异表
    diff_rows = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>"
        for r in [
            (
                "测试点数量",
                f"{len(OLD)} 条模块级",
                f"{data['total']} 条逐项",
                f"+{data['total'] - len(OLD)}（约 {data['total'] // len(OLD)}×）",
            ),
            ("覆盖粒度", "模块级抽样（9 模块）", "代码级（API路由+业务函数+前端）", "由粗到细"),
            ("测试维度", "单一笼统预期", "正常/边界/异常/安全 四维", "维度补齐"),
            ("来源", "手工归纳业务场景", "完整代码静态扫描派生", "可复现/随代码演进"),
            ("路由覆盖", "线上可见业务 ~24 场景", "全仓 125 路由 × 多维", "全 API 面"),
            ("业务函数", "未覆盖", "14 个核心模块顶层函数", "逻辑面补齐"),
            ("前端", "未覆盖", "页面可达 + 组件交互", "UI 面补齐"),
        ]
    )

    # 逐条测试点（带类型标识徽章）行数据
    bt = data.get("by_tag", {})
    tp_rows = "".join(
        f"<tr><td>{r['id']}</td>"
        f"<td><code>{r.get('fp_id', '—')}</code> {r.get('fp_title', '')}</td>"
        f"<td>{_badge_html(r.get('tag', Tag.FULL.value))}</td>"
        f"<td>{r.get('semantic', '')}</td><td>{r['module']}</td>"
        f"<td><code>{r['area']}</code></td>"
        f"<td>{r['method']}</td><td>{r['tp_type']}</td>"
        f"<td>{r['dimension']}</td><td>{r['expect']}</td></tr>"
        for r in data["test_points"]
    )

    # A1 + A2：功能点（含业务语义）→ 派生测试点 追溯矩阵
    tr = data.get("traceability", {})
    fp_rows = "".join(
        f"<tr><td><code>{f['fp_id']}</code></td><td>{f['ftype']}</td>"
        f"<td>{f.get('semantic', '')}</td>"
        f"<td>{f.get('title') or f['name']}</td>"
        f"<td><code>{f['file_path']}</code></td>"
        f"<td><b>{len(f.get('test_points', []))}</b></td>"
        f"<td>{'、'.join(f.get('test_points', [])[:8]) or '—'}</td></tr>"
        for f in data.get("functional_points", [])
    )
    ss = data.get("scan_stats", {})

    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>测试点 旧版 vs 新版 对比</title>
<style>
:root{{--bg:#0f1216;--card:#171b22;--fg:#e6e6e6;--mut:#9aa4b2;--bd:#2a313c;
--acc:#4ea1ff;--ok:#3ecf8e;--warn:#ffb454;--bad:#ff6b6b;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);
font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;padding:28px;line-height:1.6}}
h1{{font-size:22px;margin:0 0 6px}}
h2{{font-size:17px;margin:26px 0 10px;color:var(--acc);border-left:3px solid var(--acc);padding-left:10px}}
.sub{{color:var(--mut);font-size:13px;margin-bottom:8px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px}}
.tag{{display:inline-block;font-size:12px;padding:2px 8px;border-radius:999px;margin-bottom:10px}}
.old{{background:rgba(255,107,107,.15);color:var(--bad);border:1px solid rgba(255,107,107,.4)}}
.new{{background:rgba(62,207,142,.15);color:var(--ok);border:1px solid rgba(62,207,142,.4)}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th,td{{border:1px solid var(--bd);padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#1d2330;color:var(--mut);font-weight:600}}
tr:nth-child(even) td{{background:#13171e}}
.big{{font-size:30px;font-weight:700;color:var(--ok)}}
.mut{{color:var(--mut)}}
.kpi{{display:flex;gap:22px;margin:8px 0 4px;flex-wrap:wrap}}
.kpi div{{background:#1d2330;border:1px solid var(--bd);border-radius:8px;padding:10px 16px}}
.kpi b{{font-size:20px;color:var(--acc)}}
.badge,.b-full,.b-upd{{display:inline-block;font-size:11px;padding:2px 9px;border-radius:999px;font-weight:700;white-space:nowrap;line-height:1.6}}
.b-full{{background:rgba(62,207,142,.15);color:#3ecf8e;border:1px solid rgba(62,207,142,.5)}}
.b-upd{{background:rgba(255,180,84,.15);color:#ffb454;border:1px solid rgba(255,180,84,.5)}}
.legend{{display:flex;gap:18px;margin:6px 0 14px;flex-wrap:wrap;align-items:center}}
.legend span{{font-size:13px}}
.scroll{{max-height:540px;overflow:auto;border:1px solid var(--bd);border-radius:10px;margin-top:8px}}
</style></head><body>
<h1>测试点生成 · 旧版 vs 新版 对比</h1>
<div class="sub">优化 code_analyzer 的测试点生成逻辑（v2 全面生成），依据完整代码重新生成，覆盖更充分。<br>
本轮测试点范围（Scope）：<b style="color:var(--acc)">{scope_str}</b>（可选：正常 / 异常 / 安全 / 边界；默认 正常+安全+边界+异常）。</div>

<div class="kpi">
  <div>旧版合计<b>{len(OLD)}</b>条模块级</div>
  <div>新版合计<b>{data["total"]}</b>条逐项</div>
  <div>覆盖模块<b>{len(data["module_summary"])}</b>个</div>
  <div>提升倍率<b>≈{data["total"] // len(OLD)}×</b></div>
  <div>本次更新<b>{data.get("by_tag", {}).get("更新", 0)}</b>条变更点</div>
</div>

<div class="grid">
  <div class="card">
    <table><thead><tr><th>功能模块</th><th>测试点</th><th>类型</th><th>场景</th><th>预期</th></tr></thead>
    <tbody>{old_rows}</tbody></table>
  </div>
  <div class="card">
    <table><thead><tr><th>模块</th><th>总数</th><th>API维</th><th>业务维</th><th>前端维</th><th>覆盖面积</th></tr></thead>
    <tbody>{new_mod}</tbody></table>
    <p class="mut" style="font-size:12px;margin-top:8px">按类型：
    {"".join(f"<b style='color:var(--acc)'>{k} {v}</b> &nbsp; " for k, v in data["by_type"].items())}</p>
  </div>
</div>

<h2>三、新旧差异对比</h2>
<table><thead><tr><th>维度</th><th>旧版（上次）</th><th>新版（本次）</th><th>变化</th></tr></thead>
<tbody>{diff_rows}</tbody></table>

<h2>四、逐条测试点（每项旁带类型标识 + 来源功能点）</h2>
<div class="legend">
  <span><span class="b-full">全量</span> ＝ 本次完整测试内容</span>
  <span><span class="b-upd">更新</span> ＝ 本次仅变更/增量测试内容</span>
  <span class="mut">「来源功能点」列 ＝ 该测试点由哪个功能点派生（A2 追溯，点击 fp_id 可在下方矩阵反查）</span>
</div>
<div class="kpi">
  <div>全量<b>{bt.get("全量", 0)}</b>条</div>
  <div>更新<b>{bt.get("更新", 0)}</b>条</div>
  <div>合计<b>{data["total"]}</b>条</div>
  <div>功能点<b>{tr.get("fp_total", 0)}</b>个</div>
  <div>追溯覆盖<b>{tr.get("coverage", "-")}</b></div>
  <div>孤儿测试点<b>{tr.get("tp_without_fp(orphan)", 0)}</b>条</div>
</div>
<p class="sub">绿徽＝全量（代码未变更部分，常规全量回归）；橙徽＝更新（其底层路由/函数源码行被 {DIFF_BASE}..{DIFF_TARGET} 的 hunk 覆盖，hunk 级精准打标，优先回归）。</p>
<div class="scroll">
<table><thead><tr><th>ID</th><th>来源功能点</th><th>类型标识</th><th>业务语义</th><th>模块</th><th>区域/路由/函数</th><th>方法</th><th>类型</th><th>维度</th><th>预期</th></tr></thead>
<tbody>{tp_rows}</tbody></table>
</div>

<h2>五、功能点 → 测试点 追溯矩阵（A1 业务语义 + A2 双向追溯）</h2>
<div class="kpi">
  <div>功能点<b>{tr.get("fp_total", 0)}</b>个</div>
  <div>本轮有派生测试点<b>{tr.get("fp_with_tp", 0)}</b>个</div>
  <div>单功能点最多派生<b>{tr.get("max_tp_per_fp", 0)}</b>条</div>
  <div>去重扫描读文件<b>{ss.get("files_read", 0)}</b>个</div>
  <div>AST 解析<b>{ss.get("ast_parses", 0)}</b>次</div>
</div>
<p class="sub">同一份源码「只读一次、只解析一次 AST」（C1）：功能点提取、业务语义、测试点派生、
hunk 级打标共用 <code>_SourceIndex</code>，缓存命中 文本 {ss.get("text_cache_hits", 0)} 次 /
符号 {ss.get("sym_cache_hits", 0)} 次。{tr.get("note", "")}</p>
<div class="scroll">
<table><thead><tr><th>fp_id</th><th>类型</th><th>业务语义</th><th>功能点</th><th>文件</th><th>派生测试点</th><th>测试点 ID</th></tr></thead>
<tbody>{fp_rows}</tbody></table>
</div>

<p class="sub" style="margin-top:18px">完整逐条清单见 <code>TEST_POINTS_NEW.md</code>（{data["total"]} 条，
含彩色徽章「类型标识」列），结构化数据见 <code>test_points_new.json</code>（每条含 <code>tag</code> 字段，可按标签筛选）。</p>
</body></html>"""
    (OUT / "TEST_POINTS_COMPARE.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
