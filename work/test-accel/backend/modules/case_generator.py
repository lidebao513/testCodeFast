"""Case 生成器：测试点 → 可执行 + 可交付的用例规格。

批次1：主链路由「功能点驱动」改为「测试点驱动」（TP→Case），用例携带
        稳定 tp_id / fp_contract_id。
批次2：每条用例补齐 8 要素（编号/模块/标题/类型/优先级/前置/步骤/预期），
        并导出 TEST_CASES.md + test_cases.json 交付物（C-★2 + C-★4）。

mixin：确定性生成，不依赖 LLM。
- api       → http 探测 case（方法/路径）
- page      → 路由可达断言 case
- component → 交互元素断言 case
机器可执行步留在 steps[0]（executor 仅读 steps[0]）；人类可读多步写入 doc_steps。
"""

import json
from collections import Counter

from backend.config import PROJECT_ROOT, settings
from backend.core.enums import (
    FType,
    MethodMarker,
    Tag,
    TPType,
)
from backend.db import get_conn
from backend.modules.project_manager import pm


# —— 8 要素派生规则（确定性、可解释） ——


def _priority(tp) -> str:
    """优先级：异常/安全/边界 → P1；鉴权/登录/支付/交易/权限/审批类正常 → P1；其余 P2。"""
    cat = tp.get("category") or TPType.NORMAL.value
    module = tp.get("module") or ""
    if cat in (TPType.ABNORMAL.value, TPType.SECURITY.value, TPType.BOUNDARY.value):
        return "P1"
    if any(k in module for k in ("鉴权", "登录", "支付", "交易", "权限", "审批")):
        return "P1"
    return "P2"


def _precondition(tp) -> str:
    cat = tp.get("category") or TPType.NORMAL.value
    if cat == TPType.ABNORMAL.value:
        return "被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式"
    return "被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）"


def _build_doc_steps(tp, precondition: str) -> list:
    """人类可读多步（前置→准备→执行→断言），供 TEST_CASES.md 与人工评审。"""
    method = tp.get("method") or ""
    area = tp.get("area") or ""
    source = tp.get("source") or ""
    cat = tp.get("category") or TPType.NORMAL.value
    expect = tp.get("expect") or ""
    if cat == TPType.ABNORMAL.value:
        assert_desc = (
            "校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏"
        )
    else:
        assert_desc = "校验：响应状态码符合预期，关键业务字段完整"
    return [
        {"seq": 1, "type": "前置", "desc": precondition},
        {
            "seq": 2,
            "type": "准备",
            "desc": f"构造请求：{method} {area}" + (f"，来源文件 {source}" if source else ""),
        },
        {"seq": 3, "type": "执行", "desc": f"发送 {method} {area} 请求并捕获响应"},
        {"seq": 4, "type": "断言", "desc": assert_desc, "expect": expect},
    ]


class CaseGenerator:
    def generate_for_project(self, pid: int) -> dict:
        """生成用例（含增量对账，C-②8）。

        优先「测试点驱动」：每个 TP → 1 条用例，写入稳定 tp_id / fp_contract_id
        及 8 要素；否则回退旧逻辑（按功能点 1:1），保证其他项目/旧流程不破。

        **C-②8 用例状态与代码变更一致性对账**：
        每轮重生成不再简单「全量软删再重插」，而是按稳定键
        （tp_id 优先，否则 (fp_contract_id, title)）与既有用例对账：
          - 键仍存在且内容未变 → reused（status 保持 generated）
          - 键仍存在但内容变化 → updated（重写内容并标 updated）
          - 键不再出现（对应功能点被移除/不再需要）→ obsolete（**不再** archived，
            保留可见以反映「已废弃」，且执行器不会跑它）
        从而实现「用例状态与实际代码变更保持一致」。

        返回统计 dict：created / updated / reused / obsolete / active。
        """
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c FROM test_points WHERE project_id=?", (pid,))
        has_tp = cur.fetchone()["c"] > 0
        # 计算新版本号（用于新生成/更新的用例）
        cur.execute("SELECT COALESCE(MAX(version),0) v FROM cases WHERE project_id=?", (pid,))
        new_version = cur.fetchone()["v"] + 1

        # 构建本轮「应有」的用例规格
        specs = []
        if has_tp:
            cur.execute("SELECT id, contract_id FROM functional_points WHERE project_id=?", (pid,))
            fp_map = {r["contract_id"]: r["id"] for r in cur.fetchall() if r["contract_id"]}
            cur.execute("SELECT * FROM test_points WHERE project_id=? ORDER BY id", (pid,))
            tps = [dict(r) for r in cur.fetchall()]
            # 用例:测试点 映射策略（可配置）
            mode = (settings.CASE_PER_TP or "one").lower()
            split_dims = [
                s.strip() for s in (settings.CASE_SPLIT_DIMENSIONS or "").split(",") if s.strip()
            ]
            for tp in tps:
                if mode == "split":
                    # 1 个测试点 → 按维度拆多条用例（测试点数 < 用例数）
                    for sk in split_dims:
                        specs.append(self._build_from_tp(tp, fp_map, split_key=sk))
                elif mode == "merge":
                    # 多个同功能点测试点 → 合并为 1 条用例（测试点数 > 用例数）
                    specs.append(self._build_from_tp(tp, fp_map))
                else:
                    specs.append(self._build_from_tp(tp, fp_map))
        else:
            cur.execute("SELECT * FROM functional_points WHERE project_id=?", (pid,))
            fps = [dict(r) for r in cur.fetchall()]
            for fp in fps:
                specs.append(self._build_legacy(fp))

        # merge 模式：按 fp_contract_id 去重（同一功能点的多个测试点合并为 1 条）
        if has_tp and (settings.CASE_PER_TP or "one").lower() == "merge":
            merged, seen_fp = [], set()
            for spec in specs:
                fk = spec.get("fp_contract_id")
                if fk and fk in seen_fp:
                    continue
                if fk:
                    seen_fp.add(fk)
                merged.append(spec)
            specs = merged

        stats = self._reconcile(cur, pid, specs, new_version, test_type=Tag.FULL.value)
        conn.commit()
        conn.close()
        return stats

    def generate_for_fp_ids(self, pid: int, fp_ids) -> dict:
        """只为指定功能点生成用例（增量追加，不 DELETE 既有；含 C-②8 对账）。"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(version),0) v FROM cases WHERE project_id=?", (pid,))
        new_version = cur.fetchone()["v"] + 1
        created, reused, updated, case_ids = 0, 0, 0, []
        for fid in fp_ids:
            cur.execute("SELECT * FROM functional_points WHERE id=? AND project_id=?", (fid, pid))
            row = cur.fetchone()
            if not row:
                continue
            fp = dict(row)
            spec = self._build_legacy(fp)
            key = self._case_key(spec)
            cur.execute("SELECT * FROM cases WHERE project_id=? AND status!='archived'", (pid,))
            # 在既有用例里按键找匹配（含 obsolete，便于复活/更新）
            match = None
            for c in (dict(r) for r in cur.fetchall()):
                if self._case_key(c) == key:
                    match = c
                    break
            if match is None:
                self._insert_case(cur, pid, spec, new_version, test_type="新增")
                created += 1
                case_ids.append(cur.lastrowid)
            elif self._content_changed(match, spec):
                self._update_case(
                    cur, pid, match["id"], spec, new_version, test_type="新增", status="updated"
                )
                updated += 1
                case_ids.append(match["id"])
            else:
                # 既存且未变 → 复用（置为 generated，确保增量生成后状态干净）
                cur.execute("UPDATE cases SET status='generated' WHERE id=?", (match["id"],))
                reused += 1
                case_ids.append(match["id"])
        stats = {
            "created": created,
            "updated": updated,
            "reused": reused,
            "obsolete": 0,
            "case_ids": case_ids,
        }
        conn.commit()
        conn.close()
        return stats

    # —— C-②8 增量对账 ——

    @staticmethod
    def _case_key(c) -> tuple:
        """稳定身份键：tp_id 优先（测试点驱动最稳定），否则 (fp_contract_id, title)。

        1:1 模式：键为 ("tp", tp_id)，与既有历史数据完全兼容（不误判 obsolete）。
        split 模式：spec 带 split_key，键为 ("tp", tp_id, split_key)，同一测试点的
        多条用例（不同维度）互不冲突。
        落库后 split_key 未持久化到列，但 title 含 [维度] 前缀且 tc_no 含 "::维度" 后缀，
        从 title 反推维度即可恢复 split_key（见 _split_key_of）。
        """
        tp = c.get("tp_id")
        if tp:
            sk = c.get("split_key") or CaseGenerator._split_key_of(c)
            if sk:
                return ("tp", tp, sk)
            return ("tp", tp)
        return ("fp", c.get("fp_contract_id"), c.get("title"))

    @staticmethod
    def _split_key_of(c) -> str | None:
        """从用例 title/tc_no 反推拆分维度；无则返回 None（即 1:1 模式用例）。"""
        tc = c.get("tc_no") or ""
        if "::" in tc:
            return tc.split("::", 1)[1]
        return None

    @staticmethod
    def _content_changed(old, spec) -> bool:
        """判断既有用例与实际应生成规格内容是否变化（决定 updated vs reused）。"""
        if (old.get("title") or "") != (spec.get("title") or ""):
            return True
        if (old.get("module") or "") != (spec.get("module") or ""):
            return True
        if (old.get("case_type") or "") != (spec.get("case_type") or ""):
            return True
        if (old.get("priority") or "") != (spec.get("priority") or ""):
            return True
        if (old.get("precondition") or "") != (spec.get("precondition") or ""):
            return True
        try:
            old_steps = json.loads(old.get("steps") or "[]")
            old_doc = json.loads(old.get("doc_steps") or "[]")
        except Exception:
            return True
        if old_steps != spec.get("steps"):
            return True
        return old_doc != spec.get("doc_steps", [])

    def _reconcile(self, cur, pid, specs, new_version, test_type) -> dict:
        """按键对账 + 落库（C-②8 核心）。

        old_rows：既有有效性用例（status 不为 archived，含上一轮 obsolete，便于复活）。
        逐条比对 specs 与 old_rows，产出 created/updated/reused/obsolete 四类。
        """
        cur.execute("SELECT * FROM cases WHERE project_id=? AND status!='archived'", (pid,))
        old_rows = [dict(r) for r in cur.fetchall()]
        old_by_key = {}
        for c in old_rows:
            old_by_key.setdefault(self._case_key(c), c)

        stats = {"created": 0, "updated": 0, "reused": 0, "obsolete": 0}
        seen = set()
        for spec in specs:
            key = self._case_key(spec)
            seen.add(key)
            old = old_by_key.get(key)
            if old is None:
                self._insert_case(
                    cur, pid, spec, new_version, test_type=test_type, status="generated"
                )
                stats["created"] += 1
            elif self._content_changed(old, spec):
                self._update_case(
                    cur, pid, old["id"], spec, new_version, test_type=test_type, status="updated"
                )
                stats["updated"] += 1
            else:
                # 既存且内容未变 → 复用，状态保持 generated（覆盖上一轮可能的 obsolete）
                if old.get("status") != "generated":
                    cur.execute("UPDATE cases SET status='generated' WHERE id=?", (old["id"],))
                stats["reused"] += 1

        # 剩余 old（键不在本轮 specs 中）→ 功能点已废弃/不再需要 → obsolete（保留可见）
        for key, c in old_by_key.items():
            if key in seen:
                continue
            cur.execute("UPDATE cases SET status='obsolete' WHERE id=?", (c["id"],))
            stats["obsolete"] += 1

        stats["active"] = stats["created"] + stats["updated"] + stats["reused"]
        return stats

    # —— 内部：构造与落库 ——

    def _insert_case(
        self,
        cur,
        pid,
        case,
        version: int = 1,
        test_type: str = Tag.FULL.value,
        status: str = "generated",
    ):
        cur.execute(
            """INSERT INTO cases
               (project_id, fp_id, tp_id, fp_contract_id, title, steps, ctype,
                tc_no, module, case_type, priority, precondition, doc_steps,
                review_status, status, version, review_comment, test_type)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                pid,
                case.get("fp_row_id"),
                case.get("tp_id"),
                case.get("fp_contract_id"),
                case["title"],
                json.dumps(case["steps"], ensure_ascii=False),
                case["ctype"],
                case.get("tc_no"),
                case.get("module"),
                case.get("case_type"),
                case.get("priority"),
                case.get("precondition"),
                json.dumps(case.get("doc_steps", []), ensure_ascii=False),
                "approved" if not settings.REVIEW_GATE else "pending",
                status,
                version,
                case.get("review_comment") or "",
                test_type,
            ),
        )

    def _update_case(
        self,
        cur,
        pid,
        cid,
        case,
        version: int = 1,
        test_type: str = Tag.FULL.value,
        status: str = "updated",
    ):
        """C-②8：内容变化时原地更新既有用例（保留 id/历史 runs 不被悬挂）。"""
        cur.execute(
            """UPDATE cases SET
                  title=?, steps=?, ctype=?, tc_no=?, module=?, case_type=?,
                  priority=?, precondition=?, doc_steps=?, status=?, version=?,
                  review_status=?, test_type=?, fp_id=?, tp_id=?, fp_contract_id=?
               WHERE id=?""",
            (
                case["title"],
                json.dumps(case["steps"], ensure_ascii=False),
                case["ctype"],
                case.get("tc_no"),
                case.get("module"),
                case.get("case_type"),
                case.get("priority"),
                case.get("precondition"),
                json.dumps(case.get("doc_steps", []), ensure_ascii=False),
                status,
                version,
                "approved" if not settings.REVIEW_GATE else "pending",
                test_type,
                case.get("fp_row_id"),
                case.get("tp_id"),
                case.get("fp_contract_id"),
                cid,
            ),
        )

    def _build_from_tp(self, tp, fp_map: dict, split_key: str | None = None) -> dict:
        """由测试点构建用例规格（TP→Case 主链路）+ 8 要素。

        split_key：CASE_PER_TP=split 时传入的拆分维度（如 TPType.NORMAL.value/TPType.BOUNDARY.value/TPType.ABNORMAL.value/TPType.SECURITY.value）。
        命中时用该维度覆盖 case_type、标题与稳定键后缀，使一个测试点产生多条差异化用例。
        """
        cat = tp.get("category") or TPType.NORMAL.value
        if split_key:
            cat = split_key
        method = tp.get("method")
        area = tp.get("area")
        # 统一正斜杠兜底（C-②7：历史库存在反斜杠路径，executor 跨平台读取会 file missing）
        src = (tp.get("source") or "").replace("\\", "/")
        m = (method or "").upper()
        if m in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
            is_api, kind = True, None
        elif m == MethodMarker.PAGE.value:
            is_api, kind = False, FType.PAGE.value
        elif m == MethodMarker.UI.value:
            is_api, kind = False, FType.COMPONENT.value
        elif m == MethodMarker.FUNC.value:
            is_api, kind = False, FType.BUSINESS.value
        else:
            is_api, kind = False, FType.COMPONENT.value
        ctype = FType.API.value if is_api else "e2e"
        title = f"[{cat}] {tp.get('title') or tp.get('tp_id')}"
        fp_row_id = fp_map.get(tp.get("fp_contract_id"))
        expect = tp.get("expect") or ""
        # split 模式下，同一测试点的多条用例用维度后缀区分稳定键（避免键冲突）
        split_suffix = f"::{split_key}" if split_key else ""
        # 机器可执行步（必须留在 steps[0]，executor 仅读 steps[0]）
        # 非 API 用例（page/component/business）统一以 ui_probe 动作透出，
        # 由 executor 按 kind 派发到 route_assert / component_assert / func_assert，
        # 使阶段3 产出的所有用例（含前端/业务类）均可被真实执行（不再 skipped）。
        steps = [
            {
                "action": "http_probe" if is_api else "ui_probe",
                "kind": kind,
                "tp_id": tp["tp_id"],
                "fp_id": tp.get("fp_contract_id"),
                "source": src,
                "file": src,
                "method": method,
                "path": area,
                "func": area if kind == FType.BUSINESS.value else None,
                "dimension": tp.get("dimension"),
                "expect": expect,
            }
        ]
        precondition = _precondition(tp)
        return {
            "title": title,
            "ctype": ctype,
            "steps": steps,
            "fp_row_id": fp_row_id,
            "tp_id": tp["tp_id"],
            "fp_contract_id": tp.get("fp_contract_id"),
            "tc_no": tp["tp_id"] + split_suffix,
            "split_key": split_key,
            "module": tp.get("module") or "",
            "case_type": cat,
            "priority": _priority(tp),
            "precondition": precondition,
            "doc_steps": _build_doc_steps(tp, precondition),
        }

    def _build_legacy(self, fp) -> dict:
        """回退分支（无测试点时按功能点生成），补足 8 要素默认值。"""
        ftype = fp["ftype"]
        name = fp["name"]
        fpath = fp.get("file_path")
        if ftype == FType.API.value:
            parts = name.split(" ", 1)
            method = parts[0] if len(parts) == 2 else "GET"
            path = parts[1] if len(parts) == 2 else name
            ctype = FType.API.value
            steps = [
                {
                    "action": "http_probe",
                    "file": fpath,
                    "method": method,
                    "path": path,
                    "expect": "route_defined",
                }
            ]
        elif ftype == FType.PAGE.value:
            p = name.replace("页面路由", "").strip()
            ctype = "e2e"
            steps = [
                {"action": "route_assert", "file": fpath, "path": p, "expect": "route_defined"}
            ]
        else:
            ctype = "e2e"
            steps = [{"action": "component_assert", "file": fpath, "expect": "interactive_present"}]
        # 默认值：无 TP 时，异常/安全维度未知，统一按「正常」处理
        precondition = "被测服务已启动，base_url 可达"
        doc_steps = [
            {"seq": 1, "type": "前置", "desc": precondition},
            {"seq": 2, "type": "执行", "desc": f"执行{ctype}断言：{name}"},
        ]
        return {
            "title": f"[正常] {name}",
            "ctype": ctype,
            "steps": steps,
            "fp_row_id": fp["id"],
            "tp_id": None,
            "fp_contract_id": fp.get("contract_id"),
            "tc_no": f"FP-{fp.get('contract_id') or fp['id']}",
            "module": fp.get("module") or "",
            "case_type": TPType.NORMAL.value,
            "priority": "P2",
            "precondition": precondition,
            "doc_steps": doc_steps,
        }

    # —— 交付物导出（C-★4） ——

    def export_test_cases(self, pid: int) -> dict:
        """导出 TEST_CASES.md + test_cases.json 到 <name>-test/ 目录。"""
        proj = pm.get(pid) or {}
        name = proj.get("name", f"pid{pid}")
        out_dir = PROJECT_ROOT.parent / f"{name}-test"
        out_dir.mkdir(parents=True, exist_ok=True)

        conn = get_conn()
        cur = conn.cursor()
        # 仅导出当前生效用例：archived（软删历史）与 obsolete（代码已废弃，不再需要）均不进交付物
        cur.execute(
            "SELECT * FROM cases WHERE project_id=? "
            "AND status NOT IN ('archived','obsolete') ORDER BY id",
            (pid,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        catalog = []
        for c in rows:
            doc_steps = json.loads(c["doc_steps"]) if c.get("doc_steps") else []
            catalog.append(
                {
                    "tc_no": c.get("tc_no"),
                    "title": c["title"],
                    "module": c.get("module"),
                    "case_type": c.get("case_type"),
                    "priority": c.get("priority"),
                    "precondition": c.get("precondition"),
                    "fp_id": c.get("fp_contract_id"),
                    "tp_id": c.get("tp_id"),
                    "ctype": c["ctype"],
                    "doc_steps": doc_steps,
                    # 全量/新增：生成范围维度，区别于 case_type（正常/异常），
                    # 供后续按类型统计与汇总分析（C：全量/新增 类型字段）
                    "test_type": c.get("test_type") or Tag.FULL.value,
                }
            )
        by_type = dict(Counter(c["case_type"] for c in catalog))
        by_priority = dict(Counter(c["priority"] for c in catalog))
        by_module = dict(Counter(c["module"] for c in catalog).most_common())
        # 全量/新增 维度统计
        by_test_type = dict(Counter(c["test_type"] for c in catalog))
        summary = {
            "count": len(catalog),
            "by_type": by_type,
            "by_priority": by_priority,
            "by_module": by_module,
            "by_test_type": by_test_type,
        }

        md = self._render_md(name, catalog, summary)
        md_path = out_dir / "TEST_CASES.md"
        json_path = out_dir / "test_cases.json"
        md_path.write_text(md, encoding="utf-8")
        json_path.write_text(
            json.dumps(
                {"project": name, "summary": summary, "cases": catalog},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return {
            "ok": True,
            "md_path": str(md_path),
            "json_path": str(json_path),
            "count": len(catalog),
            "summary": summary,
        }

    def _render_md(self, name, catalog, summary) -> str:
        L = [f"# 测试用例清册 · {name}", ""]
        L.append(
            f"> 自动生成，共 **{summary['count']}** 条用例。"
            f" 按类型（正常/异常）：{summary['by_type']}；"
            f"按优先级：{summary['by_priority']}；"
            f"按测试类型（全量/新增）：{summary['by_test_type']}。"
        )
        L.append("")
        L.append("## 一、汇总")
        L.append("")
        L.append("### 按类型（正常/异常）")
        for k, v in summary["by_type"].items():
            L.append(f"- {k}: {v}")
        L.append("")
        L.append("### 按测试类型（全量/新增）")
        for k, v in summary["by_test_type"].items():
            L.append(f"- {k}: {v}")
        L.append("")
        L.append("### 按优先级")
        for k, v in summary["by_priority"].items():
            L.append(f"- {k}: {v}")
        L.append("")
        L.append("### 按模块（Top）")
        for k, v in summary["by_module"].items():
            L.append(f"- {k}: {v}")
        L.append("")
        L.append("## 二、用例明细")
        L.append("")
        for c in catalog:
            L.append(f"### {c['tc_no']} · {c['title']}")
            L.append(f"- 模块：{c['module']}")
            L.append(
                f"- 类型：{c['case_type']}　优先级：{c['priority']}　测试类型：{c['test_type']}"
            )
            L.append(f"- 关联：FP `{c['fp_id']}` / TP `{c['tp_id']}`")
            L.append(f"- 前置条件：{c['precondition']}")
            L.append("- 步骤：")
            for s in c["doc_steps"]:
                exp = f"（预期：{s['expect']}）" if s.get("expect") else ""
                L.append(f"  {s['seq']}. [{s['type']}] {s['desc']}{exp}")
            L.append("")
        return "\n".join(L)


case_generator = CaseGenerator()
