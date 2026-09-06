"""SQLite 数据层：建表 + 连接。表结构与设计文档 §5 对齐。"""
import sqlite3
from backend.config import settings


def get_conn():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
        """
    )
    conn.commit()
    conn.close()
