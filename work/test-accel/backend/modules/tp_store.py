"""测试点存储：把阶段2 离线产出的 test_points_new.json 导入平台 DB。

阶段2（qa-test-points 技能 / gen_test_points.py）离线生成测试点（含
正常 / 异常 / 安全 / 边界等多维度），本模块负责把它们落库，供阶段3
case_generator 消费，从而实现「测试点 → 用例」主链路 + 稳定 ID 追溯。
"""

import json
from pathlib import Path

from backend.config import PROJECT_ROOT, settings
from backend.db import get_conn


# 阶段2 默认产物位置：test-accel 与 research-agent-test 同级（均在 work/ 下）
DEFAULT_TP_JSON = PROJECT_ROOT.parent / "research-agent-test" / "test_points_new.json"


def import_test_points(pid: int, json_path: str | None = None) -> dict:
    """读取测试点 JSON，按 (project_id, tp_id) 幂等 upsert 进 test_points 表。

    返回 {"ok", "imported", "tp_json", "by_category"}。
    - 先 DELETE 该项目旧测试点，保证全量刷新幂等；
    - fp_contract_id 直接取 TP 自带的稳定 fp_id（FP-xxxxxxxx），无需二次计算。
    """
    path = Path(json_path) if json_path else DEFAULT_TP_JSON
    if not path.exists():
        return {"ok": False, "error": f"test points json not found: {path}"}
    data = json.loads(path.read_text(encoding="utf-8"))
    tps = data.get("test_points") or []
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM test_points WHERE project_id=?", (pid,))
    by_cat: dict[str, int] = {}
    for tp in tps:
        cat = tp.get("tp_type") or tp.get("category") or "正常"
        cur.execute(
            """INSERT INTO test_points
               (project_id, tp_id, fp_contract_id, category, module, semantic,
                title, source, method, area, expect, dimension, tag, review_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                pid,
                tp.get("id"),
                tp.get("fp_id"),
                cat,
                tp.get("module"),
                tp.get("semantic"),
                tp.get("name"),
                tp.get("source"),
                tp.get("method"),
                tp.get("area"),
                tp.get("expect"),
                tp.get("dimension"),
                tp.get("tag"),
                "approved" if not settings.REVIEW_GATE else "pending",
            ),
        )
        by_cat[cat] = by_cat.get(cat, 0) + 1
    conn.commit()
    conn.close()
    return {"ok": True, "imported": len(tps), "tp_json": str(path), "by_category": by_cat}


def get_test_points(pid: int, category: str | None = None) -> list:
    conn = get_conn()
    cur = conn.cursor()
    if category:
        cur.execute(
            "SELECT * FROM test_points WHERE project_id=? AND category=? ORDER BY id",
            (pid, category),
        )
    else:
        cur.execute("SELECT * FROM test_points WHERE project_id=? ORDER BY id", (pid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
