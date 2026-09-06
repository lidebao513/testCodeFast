"""最小执行器：不依赖被测服务运行也能出测试结果。
- api       → 结构性断言(后端文件确有该路由定义)；被测服务可达时再做 HTTP 探活(附加信息)
- page      → 路由断言(前端 router 文件确有该 path)
- component → 交互断言(组件文件含交互钩子)
status 以结构性断言为准；动态探活仅记录，不覆盖结构性结论。
被动态探测开关(ENABLE_DYNAMIC_PROBE)关闭或服务不可达时，动态探活标记 skipped，不阻塞、不误报。
单次服务探活：每个项目仅做一次 /health 检查并缓存结果，避免逐 case 网络超时。
"""
import json
import re
from pathlib import Path
from backend.db import get_conn
from backend.config import settings
from backend.modules.project_manager import pm


class Executor:
    def run_project(self, pid: int):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM cases WHERE project_id=?", (pid,))
        cases = [dict(r) for r in cur.fetchall()]
        conn.close()
        proj = pm.get(pid) or {}
        # 单次探活（仅当开关开启），缓存结果供所有 case 复用
        service_up = self._service_check(proj) if settings.ENABLE_DYNAMIC_PROBE else False
        results = []
        conn = get_conn()
        cur = conn.cursor()
        for c in cases:
            res = self._run_case(c, proj, service_up)
            res["case_id"] = c["id"]
            res["ctype"] = c["ctype"]
            cur.execute(
                """INSERT INTO runs (project_id, case_id, status, log_path, duration_ms)
                   VALUES (?,?,?,?,?)""",
                (pid, c["id"], res["status"], res.get("log", ""), res.get("duration_ms", 0)),
            )
            cur.execute("UPDATE cases SET status=? WHERE id=?", (res["status"], c["id"]))
            results.append(res)
        conn.commit()
        conn.close()
        return results

    def _service_check(self, proj):
        base = proj.get("base_url")
        if not base:
            return False
        try:
            import requests
            r = requests.get(base.rstrip("/") + "/health", timeout=3)
            return r.status_code < 500
        except Exception:
            return False

    def _run_case(self, c, proj, service_up):
        steps = json.loads(c["steps"]) if c.get("steps") else []
        step = steps[0] if steps else {}
        action = step.get("action")
        if action == "http_probe":
            return self._api_probe(step, proj, service_up)
        if action == "route_assert":
            return self._route_assert(step, proj)
        if action == "component_assert":
            return self._component_assert(step, proj)
        return {"status": "skipped", "reason": "no executable step", "log": ""}

    def _read(self, proj, fpath):
        if not fpath:
            return None
        root = Path(proj.get("local_path", ""))
        full = root / fpath
        if not full.exists():
            return None
        try:
            return full.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    def _api_probe(self, step, proj, service_up):
        text = self._read(proj, step.get("file"))
        method = step.get("method", "GET")
        path = step.get("path", "")
        struct_ok = False
        if text:
            pat = re.compile(
                r'\.' + re.escape(method.lower()) + r'\s*\(\s*["\']'
                + re.escape(path) + r'["\']')
            struct_ok = bool(pat.search(text)) or (path in text)
        if service_up:
            dyn = self._http_probe(proj, method, path)
        else:
            dyn = "skipped:probe_disabled_or_service_down"
        status = "pass" if struct_ok else "fail"
        log = f"structural={'ok' if struct_ok else 'missing'}; dynamic={dyn}"
        return {"status": status, "structural_ok": struct_ok, "dynamic": dyn, "log": log}

    def _http_probe(self, proj, method, path):
        base = proj.get("base_url")
        try:
            import requests
            url = base.rstrip("/") + path
            r = requests.request(method, url, timeout=5)
            return {"status_code": r.status_code}
        except Exception as e:
            return {"error": str(e)[:150]}

    def _route_assert(self, step, proj):
        text = self._read(proj, step.get("file"))
        p = step.get("path", "")
        if text is None:
            return {"status": "fail", "reason": f"file missing: {step.get('file')}",
                    "log": f"file missing {step.get('file')}"}
        ok = (p in text) or (f'path: "{p}"' in text) or (f"path: '{p}'" in text)
        return {"status": "pass" if ok else "fail",
                "reason": ("route defined" if ok else f"route {p} not found"),
                "log": f"route {p} {'found' if ok else 'missing'}"}

    def _component_assert(self, step, proj):
        text = self._read(proj, step.get("file"))
        if text is None:
            return {"status": "fail", "reason": f"file missing: {step.get('file')}",
                    "log": f"file missing {step.get('file')}"}
        ok = bool(re.search(r'(@click|v-on|<button|el-button|upload|<form|input)', text, re.I))
        return {"status": "pass" if ok else "fail",
                "reason": ("interactive element present" if ok else "no interactive element"),
                "log": f"interactive={'yes' if ok else 'no'}"}


executor = Executor()
