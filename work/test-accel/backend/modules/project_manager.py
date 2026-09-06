"""项目管理：多 git 配置 + 只读克隆 + 本地部署(test env) + 端口池。
MVP 聚焦 CRUD 与本地路径登记；克隆/部署动作后续阶段补全。
平台对目标仓库只读：绝不 push / commit 目标。
"""
import json
import sqlite3
from backend.db import get_conn
from backend.config import settings


class ProjectManager:
    def add(self, name, git_url=None, branch="main", ptype="pc", local_path=None,
            run_command=None, port=None, base_url=None, auth_type="none",
            auth_config=None, fixtures=None, health_url=None):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO projects
               (name, git_url, branch, type, local_path, run_command, port, base_url,
                auth_type, auth_config, fixtures, health_url, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (name, git_url, branch, ptype, local_path, run_command, port, base_url,
             auth_type, json.dumps(auth_config) if auth_config else None,
             json.dumps(fixtures) if fixtures else None, health_url, "active"),
        )
        pid = cur.lastrowid
        conn.commit()
        conn.close()
        return pid

    def get(self, pid):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id=?", (pid,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def list(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def find_by_name(self, name):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE name=?", (name,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None


pm = ProjectManager()
