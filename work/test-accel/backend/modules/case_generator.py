"""Case 生成器：功能点(读结构得到) → 可执行 case 规格。
最小闭环：确定性生成，不依赖 LLM。
- api       → http 探测 case（方法/路径/期望路由定义存在）
- page      → 路由可达断言 case（前端 router 文件确有该 path）
- component → 交互元素断言 case（组件含交互钩子）
每个 case 的 steps 为结构化 JSON，供 executor 解析执行。
file 字段指向功能点所在文件，executor 据此做结构性断言。
"""
import json
from backend.db import get_conn
from backend.config import settings


class CaseGenerator:
    def generate_for_project(self, pid: int) -> int:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM functional_points WHERE project_id=?", (pid,))
        fps = [dict(r) for r in cur.fetchall()]
        cur.execute("DELETE FROM cases WHERE project_id=?", (pid,))
        count = 0
        for fp in fps:
            case = self._build(fp)
            cur.execute(
                """INSERT INTO cases
                   (project_id, fp_id, title, steps, ctype, review_status, status)
                   VALUES (?,?,?,?,?,?,?)""",
                (pid, fp["id"], case["title"],
                 json.dumps(case["steps"], ensure_ascii=False),
                 case["ctype"],
                 "approved" if not settings.REVIEW_GATE else "pending",
                 "generated"),
            )
            count += 1
        conn.commit()
        conn.close()
        return count

    def _build(self, fp):
        ftype = fp["ftype"]
        name = fp["name"]
        fpath = fp["file_path"]
        if ftype == "api":
            parts = name.split(" ", 1)
            method = parts[0] if len(parts) == 2 else "GET"
            path = parts[1] if len(parts) == 2 else name
            return {
                "title": f"接口测试 {name}",
                "ctype": "api",
                "steps": [{"action": "http_probe", "file": fpath,
                           "method": method, "path": path,
                           "expect": "route_defined"}],
            }
        if ftype == "page":
            p = name.replace("页面路由", "").strip()
            return {
                "title": f"页面可达测试 {p}",
                "ctype": "e2e",
                "steps": [{"action": "route_assert", "file": fpath,
                           "path": p, "expect": "route_defined"}],
            }
        # component
        return {
            "title": f"组件交互测试 {name}",
            "ctype": "e2e",
            "steps": [{"action": "component_assert", "file": fpath,
                       "expect": "interactive_present"}],
        }


case_generator = CaseGenerator()
