"""阶段5（P5-②5）：执行批次进度持久化。

把原来仅存于进程内存的 `_BATCH_REGISTRY` 同步落地到 `run_batches` 表，使：
- 进度/终态在「进程重启」后仍可查询（`/execute/status` 优先 registry、回退 DB）；
- webhook 能覆盖「进程重启导致执行中断」场景（启动时 `recover_interrupted` 把
  DB 中仍处 running 的批次标为 `interrupted` 并触发回调）。
"""

import json
import time

from backend.db import get_conn


def ensure_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS run_batches (
            batch_id    TEXT PRIMARY KEY,
            project_id  INTEGER,
            total       INTEGER DEFAULT 0,
            done        INTEGER DEFAULT 0,
            status_counts TEXT DEFAULT '{}',
            state       TEXT DEFAULT 'running',
            started_at  TEXT,
            finished_at TEXT,
            error       TEXT,
            filters     TEXT,
            webhook_url TEXT,
            updated_at  TEXT
        )"""
    )
    conn.commit()
    conn.close()


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def upsert(batch_id, pid, total, filters=None, webhook_url="", state="running"):
    """执行开始即落库（或重置），供跨重启查询。"""
    ensure_table()
    conn = get_conn()
    cur = conn.cursor()
    now = _now()
    cur.execute(
        """INSERT INTO run_batches
           (batch_id, project_id, total, done, status_counts, state,
            started_at, filters, webhook_url, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(batch_id) DO UPDATE SET
             total=excluded.total, status_counts=excluded.status_counts,
             state=excluded.state, started_at=excluded.started_at,
             filters=excluded.filters, webhook_url=excluded.webhook_url,
             updated_at=excluded.updated_at""",
        (
            batch_id,
            pid,
            total,
            0,
            "{}",
            state,
            now,
            json.dumps(filters or {}, ensure_ascii=False),
            webhook_url or "",
            now,
        ),
    )
    conn.commit()
    conn.close()


def inc_progress(batch_id, status):
    """每执行完一条用例推进计数并落库（D-②6 + P5-②5 双写）。"""
    ensure_table()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status_counts, done FROM run_batches WHERE batch_id=?", (batch_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    try:
        sc = json.loads(row["status_counts"] or "{}")
    except Exception:
        sc = {}
    sc[status] = sc.get(status, 0) + 1
    cur.execute(
        "UPDATE run_batches SET done=?, status_counts=?, updated_at=? WHERE batch_id=?",
        (row["done"] + 1, json.dumps(sc, ensure_ascii=False), _now(), batch_id),
    )
    conn.commit()
    conn.close()


def set_state(batch_id, state, error=None):
    """执行结束（正常/中断/异常/被重启）写入终态。"""
    ensure_table()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """UPDATE run_batches SET state=?, finished_at=?, error=?, updated_at=?
           WHERE batch_id=?""",
        (state, _now(), error, _now(), batch_id),
    )
    conn.commit()
    conn.close()


def get(batch_id):
    """读取持久化进度；不存在返回 None。"""
    ensure_table()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM run_batches WHERE batch_id=?", (batch_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["status_counts"] = json.loads(d["status_counts"] or "{}")
    except Exception:
        d["status_counts"] = {}
    try:
        d["filters"] = json.loads(d["filters"] or "{}")
    except Exception:
        d["filters"] = {}
    d["live"] = False
    return d


def list_all(pid=None):
    ensure_table()
    conn = get_conn()
    cur = conn.cursor()
    if pid is None:
        cur.execute("SELECT * FROM run_batches ORDER BY started_at DESC")
    else:
        cur.execute("SELECT * FROM run_batches WHERE project_id=? ORDER BY started_at DESC", (pid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    for d in rows:
        try:
            d["status_counts"] = json.loads(d["status_counts"] or "{}")
        except Exception:
            d["status_counts"] = {}
        try:
            d["filters"] = json.loads(d["filters"] or "{}")
        except Exception:
            d["filters"] = {}
        d["live"] = False
    return rows


def recover_interrupted(fire):
    """进程启动时调用：把 DB 中 state='running' 的批次（上次进程未正常结束）标记为
    'interrupted' 并触发 webhook（若配置）。覆盖「进程重启导致执行中断」场景。

    返回被恢复的 batch_id 列表。
    """
    ensure_table()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT batch_id, project_id, webhook_url FROM run_batches WHERE state='running'")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    recovered = []
    for r in rows:
        set_state(r["batch_id"], "interrupted", error="进程重启/中断，未收到完成信号")
        if r.get("webhook_url"):
            fire(
                r["webhook_url"],
                {
                    "event": "test_execution_finished",
                    "batch_id": r["batch_id"],
                    "project_id": r["project_id"],
                    "state": "interrupted",
                    "summary": {"total": 0, "recover": True},
                    "finished_at": _now(),
                    "note": "进程重启，原执行未正常结束（已自动标记为中断）",
                },
            )
        recovered.append(r["batch_id"])
    return recovered
