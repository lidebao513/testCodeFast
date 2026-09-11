"""引擎测试：扫描 / 功能点提取 / 差异打标 / 测试点展开 / 用例生成。"""

from core.enums import FULL_SCOPE, FType, Tag, TPType
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


def test_business_case_is_ui_probe(sample_repo):
    _, result = _extract(sample_repo)
    biz = next(fp for fp in result.functional_points if fp.ftype == FType.BUSINESS.value)
    ctx = tp_expand.ExpandContext(scopes={TPType.NORMAL.value})
    tps = tp_expand.expand_functional_point(biz, ctx)
    case = case_gen.build_case(tps[0])
    assert case.ctype == "e2e"
    assert case.steps[0]["action"] == "ui_probe"
    assert case.steps[0]["func"] == biz.name
