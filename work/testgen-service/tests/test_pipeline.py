"""编排测试：全量跑通、幂等对账、增量标签、产物落盘、防幻觉校验层。"""

import json
from pathlib import Path

from core import store
from core.contracts import FunctionalPoint
from core.enums import FType, Tag, TPType
from engine import pipeline, semantic_enrich
from output.writer import OutputWriter


def _run(repo, **overrides):
    opts = pipeline.default_options(str(repo), mode=overrides.pop("mode", "full"))
    opts.scopes = {TPType.NORMAL.value, TPType.BOUNDARY.value}
    for k, v in overrides.items():
        setattr(opts, k, v)
    return pipeline.run_pipeline(opts)


def test_full_pipeline_end_to_end(fresh_db, sample_repo):
    result = _run(sample_repo)
    assert result.project_id
    assert result.counts["files"] > 0
    assert result.counts["functional_points"] > 0
    assert result.counts["test_points"] > 0
    assert result.counts["cases"] == result.counts["test_points"]
    assert result.traceability["orphan_tp_count"] == 0
    assert result.traceability["orphan_case_count"] == 0
    assert result.errors == []


def test_pipeline_is_idempotent(fresh_db, sample_repo):
    first = _run(sample_repo)
    assert first.case_stats["created"] > 0
    second = _run(sample_repo)
    assert second.case_stats["created"] == 0, "重复运行不得新增重复用例"
    assert second.case_stats["reused"] == first.case_stats["created"]
    assert second.case_stats["updated"] == 0


def test_removed_function_point_marks_case_obsolete(fresh_db, sample_repo):
    _run(sample_repo)
    api = sample_repo / "billing" / "api.py"
    text = api.read_text(encoding="utf-8")
    # 移除 POST 路由（连同其函数体），模拟「功能点消失」
    lines = text.splitlines()
    kept: list[str] = []
    skipping = False
    for ln in lines:
        if ln.startswith('@router.post("/invoices")'):
            skipping = True
            continue
        if skipping and ln.startswith("def "):
            skipping = False
        elif skipping:
            continue
        kept.append(ln)
    api.write_text("\n".join(kept) + "\n", encoding="utf-8")

    result = _run(sample_repo)
    assert result.case_stats["obsolete"] > 0, "功能点消失后，其用例应转为 obsolete"


def test_incremental_mode_tags_update(fresh_db, git_repo):
    """真仓库增量：变更文件下的测试点必须标『更新』，且不得静默降级。

    回归要点：`refs_available` 曾用 `git rev-parse --verify --quiet A B` 校验两个 ref，
    而该命令一次只接受一个 revision → 永远判定不可用 → 全部静默标『全量』。
    """
    result = _run(git_repo, mode="incremental", base="HEAD~1", target="HEAD")

    assert not any("降级" in n for n in result.notes), f"增量通道被误降级：{result.notes}"
    assert any("增量通道" in n for n in result.notes)
    assert result.tag_summary.get(Tag.UPDATE.value, 0) > 0, "变更文件必须产出『更新』测试点"
    assert result.tag_summary.get(Tag.FULL.value, 0) > 0, "未变更文件仍应保留『全量』测试点"


def test_incremental_bad_ref_degrades_to_full(fresh_db, git_repo):
    result = _run(git_repo, mode="incremental", base="nope", target="nope2")
    assert any("降级为全量" in n for n in result.notes)
    assert result.tag_summary.get(Tag.UPDATE.value, 0) == 0
    assert result.counts["test_points"] > 0


def test_evidence_attached_by_rule_engine(fresh_db, sample_repo):
    result = _run(sample_repo)
    assert all(tp.evidence for tp in result.test_points), "每条测试点都应有证据引用"
    assert all(tp.origin == "rule" for tp in result.test_points)
    assert all(tp.confidence == 1.0 for tp in result.test_points)


def test_outputs_written(fresh_db, sample_repo):
    result = _run(sample_repo)
    files = OutputWriter().write_all(
        result.project_id or 0, result.test_points, result.cases, result.to_dict()
    )
    payload = json.loads(Path(files["test_cases"]).read_text(encoding="utf-8"))
    assert payload["contract_version"] == "1.0"
    assert payload["count"] == len(result.cases)
    assert all(c["expect"] for c in payload["cases"])
    assert Path(files["markdown"]).read_text(encoding="utf-8").startswith("# 测试用例清单")
    assert json.loads(Path(files["summary"]).read_text(encoding="utf-8"))["mode"] == "full"


# ---------------------------------------------------------------- 校验层（防幻觉）
def _fp(name: str) -> FunctionalPoint:
    return FunctionalPoint(
        fp_id="FP-x",
        ftype=FType.API.value,
        file_path="a.py",
        name=name,
        title=name,
    )


def test_validator_rejects_fabricated_endpoint():
    fps = [_fp("GET /api/v1/real")]
    ok, rejected = semantic_enrich.validate_candidates(
        [{"kind": "extra_case", "area": "GET /api/v1/fake", "fp_id": "FP-none"}], fps
    )
    assert ok == []
    assert "疑似臆造" in rejected[0]["reason"]


def test_validator_accepts_real_endpoint():
    fps = [_fp("GET /api/v1/real")]
    ok, rejected = semantic_enrich.validate_candidates(
        [{"kind": "extra_case", "area": "GET /api/v1/real", "fp_id": "FP-x"}], fps
    )
    assert len(ok) == 1
    assert rejected == []


def test_validator_rejects_unknown_kind():
    ok, rejected = semantic_enrich.validate_candidates(
        [{"kind": "made_up", "area": "GET /api/v1/real", "fp_id": "FP-x"}],
        [_fp("GET /api/v1/real")],
    )
    assert ok == []
    assert "kind 非法" in rejected[0]["reason"]


def test_implicit_rule_marked_unverified():
    fps = [_fp("GET /api/v1/real")]
    candidate = {
        "kind": "implicit",
        "area": "GET /api/v1/real",
        "fp_id": "FP-x",
        "title": "疑似需要审批流",
        "category": TPType.NORMAL.value,
    }
    ok, _ = semantic_enrich.validate_candidates([candidate], fps)
    tp = semantic_enrich._to_test_point(ok[0], fps)
    assert tp is not None
    assert tp.unverified is True
    assert tp.origin == "llm_implicit"
    assert "疑似隐性规则" in tp.title


def test_llm_disabled_keeps_rule_output(fresh_db, sample_repo):
    result = _run(sample_repo, llm=semantic_enrich.EnrichOptions(enabled=False))
    assert result.counts["llm_added"] == 0
    assert any("仅规则引擎" in n or "未启用" in n for n in result.notes)


def test_store_traceability_after_persist(fresh_db, sample_repo):
    result = _run(sample_repo)
    trace = store.traceability(result.project_id or 0)
    assert trace["fp_count"] > 0
    assert trace["orphan_tp_count"] == 0
    assert trace["orphan_case_count"] == 0
