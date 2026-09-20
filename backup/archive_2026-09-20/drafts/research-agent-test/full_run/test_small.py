# -*- coding: utf-8 -*-
"""小批量验证：登录重试 + API + 对话 + UI 导航 各一例。"""
import json
import os
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rac", os.path.join(HERE, "run_all_cases.py"))
rac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rac)

cases = json.load(open(os.path.join(HERE, "all_cases.json"), encoding="utf-8"))["cases"]
api_case = next(c for c in cases if c["exec_type"] == "api")
chat_case = next(c for c in cases if c["exec_type"] == "chat")
ui_case = next(c for c in cases if c["exec_type"] == "ui_nav")
print("selected:", api_case["case_id"], chat_case["case_id"], ui_case["case_id"])

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context()
    anon_ctx = p.request.new_context()
    page = ctx.new_page()
    ok = rac.do_login(page)
    print("login ok:", ok, "url:", page.url)
    tokens = rac.grab_tokens(page)
    print("tokens:", "bmp" if tokens.get("bmp") else "无", "access" if tokens.get("access") else "无")

    r, d, _ = rac.exec_api(anon_ctx, ctx, page, api_case, tokens, lambda: rac.do_login(page))
    print("API", api_case["case_id"], "->", r, d[:60])

    # 选一个安全类用例验证无鉴权被拒
    sec_case = next((c for c in cases if c["exec_type"] == "api" and c["dimension"] == "安全"), None)
    if sec_case:
        rs, ds, _ = rac.exec_api(anon_ctx, ctx, page, sec_case, tokens, lambda: rac.do_login(page))
        print("SEC", sec_case["case_id"], "->", rs, ds[:60])

    r2, d2 = rac.exec_chat(page, chat_case)
    print("CHAT", chat_case["case_id"], "->", r2, d2[:60])

    r3, d3 = rac.exec_ui_nav(page, ui_case)
    print("UI", ui_case["case_id"], "->", r3, d3[:60])
    browser.close()
print("SMALLTEST DONE")
