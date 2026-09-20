import os
try:/n    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:/n    pass
# -*- coding: utf-8 -*-
"""定位助手消息行：从 bubble-user 向上找对话容器，列出其消息子元素 class/文本。"""
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
    pg.fill('input[placeholder="邮箱账号"]',EMAIL)
    pg.fill('input[placeholder="密码"]',PWD)
    pg.fill('input[placeholder="动态口令（6位）"]',OTP)
    pg.click('button:has-text("登 录")'); time.sleep(6)
    nb=pg.query_selector('button:has-text("新建会话")')
    if nb: nb.click(); time.sleep(2)
    ta=pg.query_selector('textarea'); ta.click(); ta.fill("请用一个词回答：今天是星期几？")
    pg.keyboard.press("Enter"); time.sleep(18)
    info=pg.evaluate("""()=>{
        const ub=document.querySelector('.bubble-user');
        if(!ub) return {err:'no bubble-user'};
        // 向上找对话容器：含多个子消息行
        let box=ub.parentElement, guard=0;
        while(box && guard++<12){ if(box.children.length>=2) break; box=box.parentElement; }
        const o={userBubbleClass: ub.className.toString().slice(0,90),
                 containerClass: box? box.className.toString().slice(0,90):null,
                 containerChildren: box? box.children.length:-1, rows:[]};
        if(box){ for(const c of Array.from(box.children)){
            const cls=(c.className||'').toString();
            const txt=(c.innerText||'').replace(/\\s+/g,' ').trim();
            o.rows.push({cls: cls.slice(0,70), tlen: txt.length, head: txt.slice(0,40)});
        }}
        return o;
    }""")
    print(json.dumps(info,ensure_ascii=False,indent=2))
    pg.screenshot(path=str(OUT/"debug_bubble.png"))
    ctx.close(); b.close()
