"""SQLite 数据层：建表 + 连接。表结构与设计文档 §5 对齐。"""

import sqlite3

from backend.config import settings


def get_conn():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    # 串行化并发写（执行主事务与 batch_store 进度落库可能同时写），避免 "database is locked"
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _add_column(conn, table: str, column: str, ddl: str):
    """幂等地给表加列（SQLite 不原生支持 IF NOT EXISTS 的 ADD COLUMN）。"""
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    existing = {r["name"] for r in cur.fetchall()}
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            git_url TEXT,
            git_token_ref TEXT,
            branch TEXT DEFAULT 'main',
            type TEXT DEFAULT 'pc',
            status TEXT DEFAULT 'pending',
            run_command TEXT,
            health_url TEXT,
            base_url TEXT,
            auth_type TEXT DEFAULT 'none',
            auth_config TEXT,
            fixtures TEXT,
            port INTEGER,
            local_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS functional_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            commit_ref TEXT,
            file_path TEXT,
            name TEXT NOT NULL,
            description TEXT,
            ftype TEXT,
            review_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            fp_id INTEGER,
            title TEXT,
            steps TEXT,
            ctype TEXT DEFAULT 'e2e',
            script_path TEXT,
            review_status TEXT DEFAULT 'pending',
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            spec_path TEXT,
            scope TEXT DEFAULT 'project',
            version TEXT DEFAULT '1.0.0',
            usage_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            case_id INTEGER,
            status TEXT,
            screenshot_path TEXT,
            log_path TEXT,
            duration_ms INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            batch_id TEXT,
            baseline_report_id INTEGER,
            summary TEXT,
            html_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS change_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            commit_from TEXT,
            commit_to TEXT,
            new_fp_ids TEXT,
            updated_fp_ids TEXT,
            removed_fp_ids TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS test_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            tp_id TEXT NOT NULL,
            fp_contract_id TEXT,
            category TEXT,
            module TEXT,
            semantic TEXT,
            title TEXT,
            source TEXT,
            method TEXT,
            area TEXT,
            expect TEXT,
            dimension TEXT,
            tag TEXT,
            review_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, tp_id)
        );
        """
    )
    # 幂等迁移：已建库的老库补列，不丢数据
    _add_column(conn, "functional_points", "contract_id", "TEXT")
    _add_column(conn, "cases", "tp_id", "TEXT")
    _add_column(conn, "cases", "fp_contract_id", "TEXT")
    # 批次2：用例 8 要素（编号/模块/类型/优先级/前置/步骤-人类可读）
    _add_column(conn, "cases", "tc_no", "TEXT")
    _add_column(conn, "cases", "module", "TEXT")
    _add_column(conn, "cases", "case_type", "TEXT")
    _add_column(conn, "cases", "priority", "TEXT")
    _add_column(conn, "cases", "precondition", "TEXT")
    _add_column(conn, "cases", "doc_steps", "TEXT")
    # 批次3：功能点契约完整化（C1）+ 用例版本号（软删，C-②1）+ 审核意见（C-★5）
    _add_column(conn, "functional_points", "title", "TEXT")
    _add_column(conn, "functional_points", "module", "TEXT")
    _add_column(conn, "cases", "version", "INTEGER DEFAULT 1")
    _add_column(conn, "cases", "review_comment", "TEXT")
    # 全量/新增 测试类型（生成范围维度，区别于 case_type 正常/异常）：
    # 全量扫描生成 → 全量；增量（仅变更功能点）生成 → 新增。默认全量，旧行自动填充。
    _add_column(conn, "cases", "test_type", "TEXT DEFAULT '全量'")
    # 阶段4 批次1（D-★5）：运行批次，一次 run_project 生成一个 batch_id，
    # 贯穿本轮 runs 与 reports，使多轮执行可区分/回溯/对比（趋势与 flaky 识别的基础）。
    _add_column(conn, "runs", "batch_id", "TEXT")
    # 阶段5（P5-②1）：cases.status 仅承载「用例生命周期状态」(generated/updated/
    # obsolete/archived)，与执行结果解耦；执行结论（pass/fail/...）写 runs.status，
    # 并冗余一份到 cases.last_result 供快速查看（不污染 lifecycle 语义）。
    _add_column(conn, "cases", "last_result", "TEXT")
    # 阶段5（P5-★4）：项目级 webhook 回调地址，异步执行结束时通知外部流水线/调用方。
    _add_column(conn, "projects", "webhook_url", "TEXT")
    # 阶段5（P5-②5）：执行批次进度持久化表（跨进程重启可查、可触发中断回调）
    from backend.modules import batch_store as _bs

    _bs.ensure_table()
    conn.commit()
    conn.close()
