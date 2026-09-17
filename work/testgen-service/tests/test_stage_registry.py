"""stage_registry 单元测试（P0-3）。

仅断言注册元数据与契约 dataclass 可实例化，**不触发**真实 LLM / playwright /
git 仓库等重依赖（wired 阶段的 fn 只取引用，不执行）。
"""

from engine.stage_registry import (
    REGISTRY,
    ComparatorStageInput,
    ComparatorStageOutput,
    ExtractStageInput,
    ExtractStageOutput,
    Stage,
    StageKind,
    adaptation_stage_names,
    capability_stage_names,
    get_stage,
    list_stages,
)


CAPABILITY = [
    "extract",
    "tp_expand",
    "case_gen",
    "semantic_enrich",
    "expert_review",
    "llm_design",
    "prd_ingest",
    "comparator",
    "runtime_ui",
    "auth_scan",
    "tag",
]
ADAPTATION = [
    "pull",
    "resolve_sources",
    "register",
    "scan",
    "partition_channels",
    "persist",
]


def test_registry_has_11_capability_stages():
    assert sorted(capability_stage_names()) == sorted(CAPABILITY)


def test_registry_has_6_adaptation_planned_stages():
    assert sorted(adaptation_stage_names()) == sorted(ADAPTATION)


def test_registry_total_17():
    assert len(REGISTRY.list_stages()) == 17


def test_capability_stages_are_wired():
    for name in CAPABILITY:
        stage = get_stage(name)
        assert stage.kind == StageKind.CAPABILITY
        assert stage.fn is not None
        assert stage.input_type is not None
        assert stage.output_type is not None
        assert stage.planned is False


def test_adaptation_stages_are_planned():
    for name in ADAPTATION:
        stage = get_stage(name)
        assert stage.kind == StageKind.ADAPTATION
        assert stage.planned is True
        assert stage.fn is None


def test_get_stage_unknown_raises_keyerror():
    try:
        get_stage("nope")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError for unknown stage")


def test_get_fn_returns_callable_for_wired():
    fn = REGISTRY.get_fn("extract")
    assert callable(fn)


def test_get_fn_raises_for_planned():
    try:
        REGISTRY.get_fn("pull")
    except NotImplementedError:
        pass
    else:
        raise AssertionError("expected NotImplementedError for planned stage get_fn")


def test_stage_run_raises_for_planned():
    stage = get_stage("pull")
    try:
        stage.run()
    except NotImplementedError:
        pass
    else:
        raise AssertionError("expected NotImplementedError when running planned stage")


def test_comparator_contract_aliases():
    from engine.comparator import CompareInput, CompareVerdict

    assert ComparatorStageInput is CompareInput
    assert ComparatorStageOutput is CompareVerdict


def test_contract_dataclasses_instantiate():
    i = ExtractStageInput(files={})
    assert i.include_business is True
    assert i.business_include_dirs is None
    o = ExtractStageOutput(
        functional_points=[],
        screens=[],
        components=[],
        business_absorbed=[],
        business_absorbed_examples=[],
    )
    assert o.functional_points == []


def test_register_duplicate_raises():
    reg = type(REGISTRY)()
    reg.register(Stage(name="x", kind=StageKind.CAPABILITY))
    try:
        reg.register(Stage(name="x", kind=StageKind.CAPABILITY))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on duplicate registration")


def test_list_stages_filter_by_kind():
    caps = list_stages(StageKind.CAPABILITY)
    assert len(caps) == len(CAPABILITY)
    assert all(s.kind == StageKind.CAPABILITY for s in caps)
    adapts = list_stages(StageKind.ADAPTATION)
    assert len(adapts) == len(ADAPTATION)
    assert all(s.kind == StageKind.ADAPTATION for s in adapts)


def test_stagekind_values():
    assert StageKind.CAPABILITY.value == "capability"
    assert StageKind.ADAPTATION.value == "adaptation"
