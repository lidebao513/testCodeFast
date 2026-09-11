import os
try:/n    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:/n    pass
# -*- coding: utf-8 -*-
import time, json
from pathlib import Path
from playwright.sync_api import sync_playwright
CHROME = r"C:\Users\EDY\AppData\Local\Google\Chrome\Application\chrome.exe"
LOGIN = "http://47.97.154.50:8090/login"
OUT = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test"); OUT.mkdir(exist_ok=True)
EMAIL = os.getenv("RA_WEB_ACCOUNT", ""); PWD = os.getenv("RA_WEB_PASSWORD", ""); OTP = os.getenv("RA_WEB_OTP", "")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,headless=True,
        args=["--no-sandbox","--disable-dev-shm-usage","--proxy-server=direct://","--proxy-bypass-list=*"])
    ctx=b.new_context(ignore_https_errors=True,viewport={"width":1440,"height":900})
    pg=ctx.new_page(); pg.set_default_timeout(30000)
    for _ in range(3):
        try: pg.goto(LOGIN,wait_until="domcontentloaded",timeout=40000); break
        except Exception as e: print("retry",e); time.sleep(3)
    time.sleep(2)
    pg.fill('input[placeholder="邮箱账号"]',EMAIL); pg.fill('input[placeholder="密码"]',PWD)
    pg.fill('input[placeholder="动态口令（6位）"]',OTP); pg.click('button:has-text("登 录")'); time.sleep(6)
    nb=pg.query_selector('button:has-text("新建会话")')
    if nb: nb.click(); time.sleep(2)
    prompt="请写一份关于企业年金业务的详细分析报，要求结构清晰、不少于 800 字，包含现状、问题与建议三部分。"
    ta=pg.query_selector('textarea'); ta.click(); ta.fill(prompt); pg.keyboard.press("Enter"); time.sleep(30)
    info=pg.evaluate("""()=>{
        const els=[...document.querySelectorAll('[class*=\"bubble\"]')];
        return els.map(e=>({cls:(e.className||'').toString().slice(0,70),
            tlen:(e.innerText||'').length,
            txt:(e.innerText||'').replace(/\\s+/g,' ').trim().slice(0,120)}));
    }""")
    print("=== BUBBLES (",len(info),") ===")
    for i,e in enumerate(info): print(i, json.dumps(e,ensure_ascii=False))
    # also dump last big text block
    pg.screenshot(path=str(OUT/"debug_td.png"))
    ctx.close(); b.close()
