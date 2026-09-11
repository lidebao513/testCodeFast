"""引擎测试：扫描 / 功能点提取 / 差异打标 / 测试点展开 / 用例生成。"""

from core.contracts import FunctionalPoint
from core.enums import FULL_SCOPE, HTTP_METHODS, Dimension, FType, Tag, TPType, VerifyLayer
from engine import case_gen, diff_tag, fp_extract, scan, tp_expand


def _extract(repo):
    files = scan.Scanner(repo).index()
    return files, fp_extract.extract_functional_points(files)


# ---------------------------------------------------------------- 扫描
def test_scan_indexes_files(sample_repo):
    files = scan.Scanner(sample_repo).index()
    assert "billing/api.py" in files
    assert "routes.js" in files
    assert files["billing/api.py"].is_python


def test_scan_skips_excluded_dirs(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / "node_modules" / "pkg" / "index.js").write_text("1", encoding="utf-8")
    files = scan.Scanner(tmp_path).index()
    assert "app/main.py" in files
    assert not any(p.startswith("node_modules") for p in files)


def test_scan_marks_noise(sample_repo):
    files = scan.Scanner(sample_repo).index()
    assert files["billing/api.py"].is_noise is False


# ---------------------------------------------------------------- 功能点
def test_extract_routes_and_business(sample_repo):
    _, result = _extract(sample_repo)
    names = {fp.name for fp in result.functional_points}
    assert "GET /api/v1/invoices" in names, "装饰器前缀应被拼回路由"
    assert "GET /api/v1/invoices/{invoice_id}" in names
    assert "POST /api/v1/invoices" in names
    assert "calculate_total" in names
    assert result.errors == []


def test_extract_sets_module_and_type(sample_repo):
    _, result = _extract(sample_repo)
    api = next(fp for fp in result.functional_points if fp.name == "GET /api/v1/invoices")
    assert api.ftype == FType.API.value
    assert api.module == "billing"
    assert api.fp_id.startswith("FP-")
    assert "billing/api.py" in api.description


def _business_names(root) -> list[str]:
    files = scan.Scanner(str(root)).index()
    fps = fp_extract.extract_functional_points(files).functional_points
    return sorted(fp.name for fp in fps if fp.ftype == FType.BUSINESS.value)


def test_same_named_methods_in_different_classes_do_not_collide(tmp_path):
    """不同类的同名方法必须得到不同 fp_id。

    回归要点：业务功能点曾用**裸函数名**做机器键，同一文件里 `A.query` 与 `B.query`
    算出同一个 `fp_id`，落库时被去重静默合并（实测真实仓库上 1034 个功能点被吞掉 11 个）。
    """
    src = tmp_path / "app"
    src.mkdir()
    (src / "models.py").write_text(
        "class A:\n"
        "    def query(self):\n"
        '        """A 的查询。"""\n'
        "        return 1\n"
        "\n"
        "\nclass B:\n"
        "    def query(self):\n"
        '        """B 的查询。"""\n'
        "        return 2\n",
        encoding="utf-8",
    )
    assert _business_names(src) == ["A.query", "B.query"]

    files = scan.Scanner(str(src)).index()
    fps = fp_extract.extract_functional_points(files).functional_points
    assert len({fp.fp_id for fp in fps}) == len(fps), "功能点编号必须两两不同"


def test_module_level_function_keeps_bare_name(tmp_path):
    """模块级函数不应被加上类名前缀（避免过度限定）。"""
    src = tmp_path / "flat_app"
    src.mkdir()
    (src / "flat.py").write_text(
        'def plain_func():\n    """模块级函数。"""\n    return 1\n', encoding="utf-8"
    )
    assert _business_names(src) == ["plain_func"]


def test_extract_pages_from_frontend(sample_repo):
    _, result = _extract(sample_repo)
    pages = [fp for fp in result.functional_points if fp.ftype == FType.PAGE.value]
    assert any(fp.name == "/dashboard" for fp in pages)


def test_scan_covers_all_frontend_extensions(sample_repo):
    """扫描器必须覆盖前端全部扩展名（含 .tsx/.jsx）。

    回归要点：`Scanner.exts` 白名单曾漏掉 `.tsx`，真实仓库上 147 个 `.tsx`
    （整个 React 页面层）**从未进入分析**，表现为「UI 层功能点恒为 0」且无任何报错。
    """
    files = scan.Scanner(str(sample_repo)).index()
    assert "web/App.tsx" in files, "前端 .tsx 文件必须被扫描到"
    for ext in scan.FRONTEND_EXTS:
        assert ext in scan.SOURCE_EXTS, f"{ext} 应包含在扫描扩展名中"


def test_extract_jsx_routes_as_page(sample_repo):
    """JSX 写法 `<Route path="/x" />` 必须被识别为页面功能点（等价于 `path: '/x'`）。"""
    _, result = _extract(sample_repo)
    pages = {fp.name for fp in result.functional_points if fp.ftype == FType.PAGE.value}
    assert "/dashboard" in pages, "对象字面量写法应识别"
    assert {"/pc/chat", "/pc/tasks"} <= pages, "JSX 写法应识别"


def test_page_functional_point_yields_ui_layer_case(sample_repo):
    """页面功能点 → UI 层用例（ctype=e2e / 机器步 ui_probe），不得退化成接口层。"""
    _, result = _extract(sample_repo)
    pages = [fp for fp in result.functional_points if fp.ftype == FType.PAGE.value]
    assert pages, "样例仓库应含页面功能点"
    tps = tp_expand.expand_all(pages, tp_expand.ExpandContext(scopes={TPType.NORMAL.value}))
    assert tps
    for tp in tps:
        assert tp.verify_layer == VerifyLayer.UI.value
        case = case_gen.build_case(tp)
        assert case.ctype == "e2e"
        assert case.steps[0]["action"] == "ui_probe"
        assert case.steps[0]["kind"] == FType.PAGE.value
        assert case.missing_elements() == []


def test_execution_layer_follows_verify_layer_not_http_verb(sample_repo):
    """执行层以契约的 verify_layer 为准，不得按「是否 HTTP 动词」判。

    回归要点：后端业务函数（method=FUNC）属**接口层**，早期实现把它派成 `ui_probe`，
    执行器会去拉浏览器「打开一个后端函数」。
    """
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(
        result.functional_points, tp_expand.ExpandContext(scopes={TPType.NORMAL.value})
    )
    cases = [case_gen.build_case(tp) for tp in tps]
    by_kind = {c.steps[0]["kind"]: c for c in cases}
    business, page = by_kind[FType.BUSINESS.value], by_kind[FType.PAGE.value]
    assert business.steps[0]["layer"] == VerifyLayer.INTERFACE.value
    assert business.steps[0]["action"] == "http_probe"
    assert page.steps[0]["layer"] == VerifyLayer.UI.value
    assert page.steps[0]["action"] == "ui_probe"


# ---------------------------------------------------------------- 安全维度
def test_security_dimension_only_for_api(sample_repo):
    """安全维度当前只在接口类功能点上展开（页面/业务函数不产出安全测试点）。

    这条测试把**现状**钉住：若后续要扩到 UI/业务函数，必须同步改本断言，
    避免「以为覆盖了、其实没覆盖」。
    """
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(
        result.functional_points, tp_expand.ExpandContext(scopes={TPType.SECURITY.value})
    )
    assert tps, "接口功能点应展开出安全测试点"
    assert {tp.method for tp in tps} <= set(HTTP_METHODS), "安全测试点全部来自 HTTP 接口"
    assert all(tp.dimension == Dimension.AUTH_MISS.value for tp in tps)


def test_default_scope_excludes_security(sample_repo):
    """默认范围不含「安全」——不显式指定就不会生成安全用例。"""
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(result.functional_points, tp_expand.ExpandContext())
    assert tps
    assert TPType.SECURITY.value not in {tp.category for tp in tps}


# ---------------------------------------------------------------- 编号稳定性（D-9）
def test_test_point_ids_stable_across_scope_changes():
    """扩大范围不得改变已有维度的 tp_id。

    回归要点：序号原用「过滤后的循环下标」，用户这次只要 `正常+异常`、下次加 `安全`，
    同一条『异常』测试点序号就从 1 变 2 → 编号漂移 → 旧用例被判 obsolete 并新建一条，
    人工审核结论与执行历史全部断链（实测真实仓库上 117 条异常用例被误废弃）。
    """
    fp = FunctionalPoint(
        fp_id="FP-scope",
        ftype=FType.API.value,
        file_path="a.py",
        name="GET /x/{id}",
        title="查询详情/x/{id}",
    )
    narrow = tp_expand.expand_all(
        [fp], tp_expand.ExpandContext(scopes={TPType.NORMAL.value, TPType.ABNORMAL.value})
    )
    wide = tp_expand.expand_all([fp], tp_expand.ExpandContext(scopes=set(FULL_SCOPE)))
    narrow_ids = {tp.category: tp.tp_id for tp in narrow}
    wide_ids = {tp.category: tp.tp_id for tp in wide}
    assert narrow_ids[TPType.NORMAL.value] == wide_ids[TPType.NORMAL.value]
    assert narrow_ids[TPType.ABNORMAL.value] == wide_ids[TPType.ABNORMAL.value], (
        "扩大范围后既有维度的编号必须保持不变"
    )


def test_case_title_has_single_category_prefix(sample_repo):
    """用例标题不得出现重复的 `[维度]` 前缀。"""
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(
        result.functional_points, tp_expand.ExpandContext(scopes=set(FULL_SCOPE))
    )
    for tp in tps:
        title = case_gen.build_case(tp).title
        assert title.count(f"[{tp.category}]") == 1, f"标题前缀重复：{title}"


# ---------------------------------------------------------------- 差异打标
def test_full_channel_tags_everything_full(sample_repo):
    ctx = diff_tag.DiffContext()
    assert diff_tag.tag_of_rel("billing/api.py", ctx) == Tag.FULL.value


def test_incremental_channel_tags_changed_files(sample_repo):
    ctx = diff_tag.DiffContext(changed_files={"billing/api.py"})
    assert diff_tag.tag_of_rel("billing/api.py", ctx) == Tag.UPDATE.value
    assert diff_tag.tag_of_rel("routes.js", ctx) == Tag.FULL.value


def test_symbol_level_hunk_hit():
    ctx = diff_tag.DiffContext(changed_files={"a.py"}, hunks={"a.py": [(10, 3)]}, aligned=True)
    assert diff_tag.tag_of_symbol("a.py", 12, 20, ctx) == Tag.UPDATE.value
    assert diff_tag.tag_of_symbol("a.py", 30, 40, ctx) == Tag.FULL.value


def test_no_repo_means_no_escape(sample_repo):
    assert diff_tag.repo_escape_blocked(sample_repo) is False


# ---------------------------------------------------------------- 测试点
def test_expand_covers_four_dimensions(sample_repo):
    _, result = _extract(sample_repo)
    detail = next(
        fp for fp in result.functional_points if fp.name == "GET /api/v1/invoices/{invoice_id}"
    )
    ctx = tp_expand.ExpandContext(scopes=set(FULL_SCOPE))
    tps = tp_expand.expand_functional_point(detail, ctx)
    cats = {tp.category for tp in tps}
    assert TPType.NORMAL.value in cats
    assert TPType.SECURITY.value in cats
    assert TPType.ABNORMAL.value in cats
    assert TPType.BOUNDARY.value in cats


def test_expand_respects_scope_filter(sample_repo):
    _, result = _extract(sample_repo)
    ctx = tp_expand.ExpandContext(scopes={TPType.NORMAL.value})
    tps = tp_expand.expand_all(result.functional_points, ctx)
    assert tps
    assert {tp.category for tp in tps} == {TPType.NORMAL.value}


def test_expand_keeps_traceability(sample_repo):
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(result.functional_points)
    known = {fp.fp_id for fp in result.functional_points}
    assert tps
    assert all(tp.fp_contract_id in known for tp in tps), "不得出现孤儿测试点"
    assert all(tp.evidence == [] for tp in tps)


def test_verify_layer_derived(sample_repo):
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(result.functional_points)
    api_tp = next(tp for tp in tps if tp.verify_layer)
    assert api_tp.verify_layer in ("接口", "UI")


# ---------------------------------------------------------------- 用例
def test_case_has_all_eight_elements(sample_repo):
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(result.functional_points)
    cases = case_gen.generate_cases(tps)
    assert cases
    for case in cases:
        assert case.missing_elements() == [], f"{case.tc_no} 八要素不全"


def test_case_machine_step_in_first_position(sample_repo):
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(result.functional_points)
    cases = case_gen.generate_cases(tps)
    for case in cases:
        step = case.steps[0]
        assert step["action"] in ("http_probe", "ui_probe")
        assert step["tp_id"] == case.tp_id
        assert "expect" in step


def test_case_generation_is_deterministic(sample_repo):
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(result.functional_points)
    first = [c.to_dict() for c in case_gen.generate_cases(tps)]
    second = [c.to_dict() for c in case_gen.generate_cases(tps)]
    assert first == second


def test_case_coverage_no_orphan(sample_repo):
    _, result = _extract(sample_repo)
    tps = tp_expand.expand_all(result.functional_points)
    cases = case_gen.generate_cases(tps)
    cov = case_gen.coverage_of(cases, tps)
    assert cov["orphan_count"] == 0
    assert cov["uncovered_count"] == 0


def test_business_case_uses_interface_layer(sample_repo):
    """业务函数用例：ctype 仍为 e2e（执行家族不变），但执行层必须是接口层。

    说明：`ctype`（api/e2e）是**执行家族**，与 `layer`（接口/UI）是两个维度。
    业务函数不是 HTTP 接口，故 ctype=e2e；但它属接口层，机器步走 http_probe。
    旧断言曾把它钉成 `ui_probe`，等于把「给后端函数拉浏览器」这个缺陷写进了契约。
    """
    _, result = _extract(sample_repo)
    biz = next(fp for fp in result.functional_points if fp.ftype == FType.BUSINESS.value)
    ctx = tp_expand.ExpandContext(scopes={TPType.NORMAL.value})
    tps = tp_expand.expand_functional_point(biz, ctx)
    case = case_gen.build_case(tps[0])
    assert case.ctype == "e2e"
    assert case.steps[0]["layer"] == VerifyLayer.INTERFACE.value
    assert case.steps[0]["action"] == "http_probe"
    assert case.steps[0]["func"] == biz.name
    assert case.steps[0]["kind"] == FType.BUSINESS.value
