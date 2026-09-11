# -*- coding: utf-8 -*-
"""Phase 2: 为 test_points_new.json 中的每一条测试点设计一条对应测试用例。

- 用例与测试点 1:1 对应（覆盖无遗漏）。
- 标签（平台契约）：test point 的 tag=更新 → 用例标签=新增；否则=全量。
- 执行策略：
    API  (GET/POST/PUT/PATCH/DELETE) -> 走 Playwright Chromium 的 API 请求上下文探活+断言
    UI   (UI)                          -> 浏览器导航到对应页面
    FUNC (FUNC)                        -> 浏览器进入对话，发送触发该能力的消息
产物：full_run/all_cases.json
"""
import json
import os
import re
import sys

BASE = r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test"
TP_JSON = os.path.join(BASE, "test_points_new.json")
OUT = os.path.join(BASE, "full_run", "all_cases.json")

BASE_URL = "http://47.97.154.50:8090"

HTTP_VERBS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# 模块 -> 前端路由（UI 导航用）
MODULE_ROUTE = {
    "邮件 Email": "/pc/email",
    "日程 Schedule": "/pc/schedule",
    "知识库 Knowledge": "/pc/knowledge",
    "定时任务 Tasks": "/pc/tasks",
    "产物/文档 Artifact": "/pc/artifacts",
    "每日业绩 DailyPerf": "/pc/daily-perf",
    "审计/审核看板 Audit": "/pc/audit",
    "技能 Skills": "/pc/skills",
    "连接器 Connector": "/pc/connectors",
    "启新记 Qixinji": "/pc/qixinji",
    "发现 Discover": "/pc/discover",
    "对话/会话 Chat": "/chat",
    "账户/用户/鉴权 Auth": "/pc/settings",
}


def sub_params(path: str) -> str:
    """把 {tid}/{account_id} 等路径参数替换为占位值 'test'。"""
    return re.sub(r"\{[^}]+\}", "test", path or "")


def exec_type_of(method: str) -> str:
    if method in HTTP_VERBS:
        return "api"
    if method == "UI":
        return "ui_nav"
    if method == "FUNC":
        return "chat"
    return "api"


def build_prompt(tp: dict) -> str:
    """为 FUNC（业务函数）测试点构造一条对话触发消息。"""
    sem = (tp.get("semantic") or "").strip()
    module = (tp.get("module") or "").strip()
    action = ""
    name = tp.get("name", "")
    if "·" in name:
        action = name.split("·")[-1].strip()
    if not action:
        action = sem or name
    return f"请使用「{module}」的能力处理：{action}。请给出结果。"


def pass_criteria_desc(tp_type: str) -> str:
    if tp_type == "正常":
        return "期望 HTTP 2xx（路由可用、返回预期业务结果）"
    if tp_type == "安全":
        return "期望 401/403（缺失/越权访问被正确拒绝）"
    if tp_type == "边界":
        return "期望 400/422（非法/缺失参数被正确拒绝）"
    if tp_type == "异常":
        return "期望 404（不存在资源被正确拒绝）"
    return "按用例设计预期判定"


def main():
    tps = json.load(open(TP_JSON, encoding="utf-8"))
    if isinstance(tps, dict):
        tps = tps.get("test_points", [])
    cases = []
    for i, tp in enumerate(tps, 1):
        method = tp.get("method", "")
        etype = exec_type_of(method)
        tag = "新增" if tp.get("tag") == "更新" else "全量"
        case = {
            "case_id": f"TC-{i:03d}",
            "tp_id": tp.get("id"),
            "module": tp.get("module"),
            "fp_id": tp.get("fp_id"),
            "fp_name": tp.get("fp_name"),
            "fp_title": tp.get("fp_title"),
            "tag": tag,                       # 全量 / 新增
            "dimension": tp.get("tp_type"),   # 正常/异常/安全/边界
            "dimension_full": tp.get("dimension"),
            "method": method,
            "path": tp.get("area"),
            "expect": tp.get("expect"),
            "semantic": tp.get("semantic"),
            "exec_type": etype,
        }
        if etype == "api":
            case["exec"] = {
                "kind": "api",
                "http_method": method,
                "url": BASE_URL + sub_params(tp.get("area", "")),
                "need_auth": True,
            }
        elif etype == "ui_nav":
            route = tp.get("area") or MODULE_ROUTE.get(tp.get("module"), "/chat")
            case["exec"] = {"kind": "ui_nav", "route": route}
        else:  # chat
            case["exec"] = {"kind": "chat", "prompt": build_prompt(tp)}
        case["pass_criteria"] = pass_criteria_desc(tp.get("tp_type"))
        cases.append(case)

    by_tag = {}
    by_type = {}
    by_module = {}
    for c in cases:
        by_tag[c["tag"]] = by_tag.get(c["tag"], 0) + 1
        by_type[c["exec_type"]] = by_type.get(c["exec_type"], 0) + 1
        by_module[c["module"]] = by_module.get(c["module"], 0) + 1

    out = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "base_url": BASE_URL,
        "total": len(cases),
        "by_tag": by_tag,
        "by_exec_type": by_type,
        "by_module": by_module,
        "cases": cases,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"[gen_cases] 用例总数 = {len(cases)}（应等于测试点数 400）")
    print(f"[gen_cases] 标签分布(全量/新增) = {by_tag}")
    print(f"[gen_cases] 执行类型分布 = {by_type}")
    print(f"[gen_cases] 模块数 = {len(by_module)}")
    print(f"[gen_cases] 写入 -> {OUT}")


if __name__ == "__main__":
    main()
