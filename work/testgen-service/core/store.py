"""仓储层：数据读写与对账，不感知 HTTP，不承载业务规则。

- 全部走参数化查询；
- 多步写入使用事务（`with conn:` 自动提交/回滚）；
- 用例对账（幂等）在此实现：生成 → 更新 → 复用 → 废弃，键为 `tp_id`。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from core.contracts import CaseSpec, FunctionalPoint, TestPoint
from core.db import connect, init_db
from core.enums import CaseLifecycleStatus
from core.errors import ContractViolation


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


# ============================================================================
# 项目
# ============================================================================
def upsert_project(  # noqa: PLR0913 - 项目注册字段本就多，显式关键字参数比结构体更直观
    name: str,
    local_path: str,
    *,
    git_url: str = "",
    branch: str = "",
    base_url: str = "",
    conn: sqlite3.Connection | None = None,
) -> int:
    """按 name 注册或更新项目，返回 project_id。"""
    own = conn is None
    conn = conn or connect()
    init_db(conn)
    try:
        with conn:
            row = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
            if row:
                pid = int(row["id"])
                conn.execute(
                    "UPDATE projects SET local_path=?, git_url=?, branch=?, base_url=? WHERE id=?",
                    (local_path, git_url, branch, base_url, pid),
                )
                return pid
            cur = conn.execute(
                "INSERT INTO projects(name, local_path, git_url, branch, base_url, created_at)"
                " VALUES(?,?,?,?,?,?)",
                (name, local_path, git_url, branch, base_url, _now()),
            )
            return int(cur.lastrowid or 0)
    finally:
        if own:
            conn.close()


def get_project(pid: int, conn: sqlite3.Connection | None = None) -> dict[str, Any] | None:
    own = conn is None
    conn = conn or connect()
    try:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
        return dict(row) if row else None
    finally:
        if own:
            conn.close()


def list_projects(conn: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY id")]
    finally:
        if own:
            conn.close()


# ============================================================================
# 功能点
# ============================================================================
def replace_functional_points(
    pid: int, fps: list[FunctionalPoint], *, conn: sqlite3.Connection | None = None
) -> dict[str, int]:
    """整批替换某项目的功能点（先删后插，保证与分析结果一致）。"""
    own = conn is None
    conn = conn or connect()
    try:
        with conn:
            conn.execute("DELETE FROM functional_points WHERE project_id = ?", (pid,))
            rows = [
                (
                    pid,
                    fp.commit_ref,
                    fp.file_path,
                    fp.name,
                    fp.description,
                    fp.ftype,
                    fp.review_status,
                    _now(),
                    fp.fp_id,
                    fp.title,
                    fp.module,
                    fp.semantic,
                )
                for fp in fps
            ]
            conn.executemany(
                "INSERT INTO functional_points(project_id, commit_ref, file_path, name,"
                " description, ftype, review_status, created_at, contract_id, title, module,"
                " semantic) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
        return {"functional_points": len(rows)}
    finally:
        if own:
            conn.close()


def list_functional_points(
    pid: int, conn: sqlite3.Connection | None = None
) -> list[dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM functional_points WHERE project_id = ? ORDER BY id", (pid,)
            )
        ]
    finally:
        if own:
            conn.close()


def fp_row_map(pid: int, conn: sqlite3.Connection | None = None) -> dict[str, int]:
    """contract_id(fp_id) → 自增行 id 的映射（用例回填 fp_id 列用）。"""
    return {
        str(r["contract_id"]): int(r["id"])
        for r in list_functional_points(pid, conn)
        if r.get("contract_id")
    }


# ============================================================================
# 测试点
# ============================================================================
def replace_test_points(
    pid: int, tps: list[TestPoint], *, conn: sqlite3.Connection | None = None
) -> dict[str, int]:
    """整批替换某项目的测试点。"""
    own = conn is None
    conn = conn or connect()
    try:
        created = _now()
        rows = [
            (
                pid,
                tp.tp_id,
                tp.fp_contract_id,
                tp.category,
                tp.module,
                tp.semantic,
                tp.title,
                tp.source,
                tp.method,
                tp.area,
                tp.expect,
                tp.dimension,
                tp.tag,
                tp.review_status,
                created,
                _dumps(tp.evidence),
                tp.confidence,
                tp.origin,
                1 if tp.unverified else 0,
            )
            for tp in tps
        ]
        with conn:
            conn.execute("DELETE FROM test_points WHERE project_id = ?", (pid,))
            conn.executemany(
                "INSERT INTO test_points(project_id, tp_id, fp_contract_id, category, module,"
                " semantic, title, source, method, area, expect, dimension, tag, review_status,"
                " created_at, evidence, confidence, origin, unverified)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
        return {"test_points": len(rows)}
    finally:
        if own:
            conn.close()


def list_test_points(pid: int, conn: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM test_points WHERE project_id = ? ORDER BY id", (pid,)
            )
        ]
        for r in rows:
            r["evidence"] = _loads(r.get("evidence"), [])
        return rows
    finally:
        if own:
            conn.close()


# ============================================================================
# 用例（幂等对账）
# ============================================================================
def _duplicate_tp_ids(specs: list[CaseSpec]) -> list[str]:
    """找出重复的 tp_id（保持首次出现顺序）。"""
    seen: set[str] = set()
    dupes: list[str] = []
    for spec in specs:
        key = spec.tp_id
        if key in seen and key not in dupes:
            dupes.append(key)
        seen.add(key)
    return dupes


def reconcile_cases(
    pid: int, specs: list[CaseSpec], *, conn: sqlite3.Connection | None = None
) -> dict[str, int]:
    """按 `tp_id` 对账生成用例，幂等。

    返回统计：created / updated / reused / obsolete。
    - 新出现 → inserted（status=generated）
    - 内容变化 → updated（version+1）
    - 未变 → reused
    - 旧用例的 tp_id 已不在本次集合 → obsolete（保留可见、不进执行）

    传入 `specs` 内部若出现重复 tp_id，说明上游编号算法发生了碰撞，**直接失败**：
    静默插入两行会绕开以 tp_id 为键的对账，重复行将永远无法被更新或作废。
    """
    dupes = _duplicate_tp_ids(specs)
    if dupes:
        raise ContractViolation(
            f"用例编号重复（上游编号碰撞）：{dupes[:5]}，共 {len(dupes)} 个；"
            "请在生成侧修正编号算法，而非在此处去重"
        )

    own = conn is None
    conn = conn or connect()
    try:
        stats = {"created": 0, "updated": 0, "reused": 0, "obsolete": 0}
        with conn:
            existing = {
                str(r["tp_id"]): dict(r)
                for r in conn.execute(
                    "SELECT * FROM cases WHERE project_id = ? AND tp_id IS NOT NULL", (pid,)
                )
            }
            incoming: set[str] = set()
            for spec in specs:
                incoming.add(spec.tp_id)
                old = existing.get(spec.tp_id)
                payload = _case_payload(spec)
                if old is None:
                    conn.execute(
                        "INSERT INTO cases(project_id, fp_id, title, steps, ctype,"
                        " review_status, status, created_at, tp_id, fp_contract_id, tc_no,"
                        " module, case_type, priority, precondition, doc_steps, version,"
                        " test_type) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            pid,
                            spec.fp_row_id,
                            spec.title,
                            _dumps(spec.steps),
                            spec.ctype,
                            "approved",
                            "generated",
                            _now(),
                            spec.tp_id,
                            spec.fp_contract_id,
                            spec.tc_no,
                            spec.module,
                            spec.case_type,
                            spec.priority,
                            spec.precondition,
                            _dumps(spec.doc_steps),
                            1,
                            spec.test_type,
                        ),
                    )
                    stats["created"] += 1
                    continue
                if _case_changed(old, payload):
                    conn.execute(
                        "UPDATE cases SET title=?, steps=?, ctype=?, tc_no=?, module=?,"
                        " case_type=?, priority=?, precondition=?, doc_steps=?, version=?,"
                        " status='updated', fp_id=?, fp_contract_id=?, test_type=?"
                        " WHERE id=?",
                        (
                            spec.title,
                            _dumps(spec.steps),
                            spec.ctype,
                            spec.tc_no,
                            spec.module,
                            spec.case_type,
                            spec.priority,
                            spec.precondition,
                            _dumps(spec.doc_steps),
                            int(old.get("version") or 1) + 1,
                            spec.fp_row_id,
                            spec.fp_contract_id,
                            spec.test_type,
                            old["id"],
                        ),
                    )
                    stats["updated"] += 1
                else:
                    stats["reused"] += 1

            stale = [tid for tid in existing if tid not in incoming]
            for tid in stale:
                conn.execute(
                    "UPDATE cases SET status='obsolete' WHERE id=?", (existing[tid]["id"],)
                )
                stats["obsolete"] += 1
        return stats
    finally:
        if own:
            conn.close()


def _case_payload(spec: CaseSpec) -> dict[str, Any]:
    return {
        "title": spec.title,
        "steps": spec.steps,
        "doc_steps": spec.doc_steps,
        "priority": spec.priority,
        "precondition": spec.precondition,
        "case_type": spec.case_type,
    }


def _case_changed(old: dict[str, Any], payload: dict[str, Any]) -> bool:
    """内容是否变化：比对标题/步骤/文档步骤/优先级/前置/类型（忽略执行结论列）。"""
    for key, want in payload.items():
        have = _loads(old.get(key), old.get(key)) if key in ("steps", "doc_steps") else old.get(key)
        if have != want:
            return True
    return False


def list_cases(
    pid: int,
    *,
    include_obsolete: bool = False,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        sql = "SELECT * FROM cases WHERE project_id = ?"
        params: list[Any] = [pid]
        if not include_obsolete:
            sql += " AND status != ?"
            params.append(CaseLifecycleStatus.OBSOLETE.value)
        sql += " ORDER BY id"
        rows = [dict(r) for r in conn.execute(sql, tuple(params))]
        for r in rows:
            r["steps"] = _loads(r.get("steps"), [])
            r["doc_steps"] = _loads(r.get("doc_steps"), [])
        return rows
    finally:
        if own:
            conn.close()


def case_stats(pid: int, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    own = conn is None
    conn = conn or connect()
    try:
        by_status = {
            str(r["status"]): int(r["n"])
            for r in conn.execute(
                "SELECT status, COUNT(*) AS n FROM cases WHERE project_id = ? GROUP BY status",
                (pid,),
            )
        }
        by_priority = {
            str(r["priority"]): int(r["n"])
            for r in conn.execute(
                "SELECT priority, COUNT(*) AS n FROM cases WHERE project_id = ?"
                " AND status != ? GROUP BY priority",
                (pid, CaseLifecycleStatus.OBSOLETE.value),
            )
        }
        return {"by_status": by_status, "by_priority": by_priority}
    finally:
        if own:
            conn.close()


# ============================================================================
# 追溯与变更日志
# ============================================================================
def traceability(pid: int, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    """追溯体检：孤儿测试点 / 孤儿用例应为 0。"""
    own = conn is None
    conn = conn or connect()
    try:
        fp_ids = {
            str(r["contract_id"])
            for r in conn.execute(
                "SELECT contract_id FROM functional_points WHERE project_id = ?", (pid,)
            )
        }
        tp_rows = list(
            conn.execute(
                "SELECT tp_id, fp_contract_id FROM test_points WHERE project_id = ?", (pid,)
            )
        )
        tp_ids = {str(r["tp_id"]) for r in tp_rows}
        case_rows = list(
            conn.execute(
                "SELECT tp_id FROM cases WHERE project_id = ? AND status != 'obsolete'", (pid,)
            )
        )
        orphan_tp = [str(r["tp_id"]) for r in tp_rows if str(r["fp_contract_id"]) not in fp_ids]
        orphan_case = [str(r["tp_id"]) for r in case_rows if str(r["tp_id"]) not in tp_ids]
        return {
            "fp_count": len(fp_ids),
            "tp_count": len(tp_ids),
            "case_count": len(case_rows),
            "orphan_tp": orphan_tp,
            "orphan_case": orphan_case,
            "orphan_tp_count": len(orphan_tp),
            "orphan_case_count": len(orphan_case),
        }
    finally:
        if own:
            conn.close()


def log_change(pid: int, kind: str, detail: str, *, conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    conn = conn or connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO change_log(project_id, kind, detail, created_at) VALUES(?,?,?,?)",
                (pid, kind, detail, _now()),
            )
    finally:
        if own:
            conn.close()
