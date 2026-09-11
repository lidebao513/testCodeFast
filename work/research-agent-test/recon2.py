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
    pg.fill('input[placeholder="邮箱账号"]',EMAIL)
    pg.fill('input[placeholder="密码"]',PWD)
    pg.fill('input[placeholder="动态口令（6位）"]',OTP)
    pg.click('button:has-text("登 录")'); time.sleep(6)
    # new session
    nb=pg.query_selector('button:has-text("新建会话")')
    if nb: nb.click(); time.sleep(2)
    ta=pg.query_selector('textarea'); ta.click(); ta.fill("请用一个词回答：今天是星期几？")
    pg.keyboard.press("Enter"); time.sleep(15)
    # inspect DOM: find container and message children
    info=pg.evaluate("""()=>{
        const ta=document.querySelector('textarea');
        const comp=ta? ta.closest('div'):null;
        // walk up to a container with many children
        let box=comp;
        for(let i=0;i<8 && box;i++){ if(box.children.length>2) break; box=box.parentElement; }
        const o={composerClass: comp? comp.className.toString().slice(0,60):null,
                 containerClass: box? box.className.toString().slice(0,80):null,
                 containerTag: box? box.tagName:null,
                 childCount: box? box.children.length:-1,
                 children:[]};
        if(box){ for(const c of Array.from(box.children).slice(-6)){
            o.children.push({tag:c.tagName, cls:(c.className||'').toString().slice(0,70),
                             txt:(c.innerText||'').replace(/\\s+/g,' ').trim().slice(0,50), tlen:(c.innerText||'').length});
        }}
        // also: all elements whose text includes our prompt
        const hits=[...document.querySelectorAll('*')].filter(e=>e.children.length===0 && (e.innerText||'').includes('星期几'));
        o.promptLeafHits=hits.slice(0,3).map(e=>({tag:e.tagName,cls:(e.className||'').toString().slice(0,60),txt:(e.innerText||'').slice(0,40)}));
        return o;
    }""")
    print(json.dumps(info,ensure_ascii=False,indent=2))
    pg.screenshot(path=str(OUT/"recon2.png"))
    ctx.close(); b.close()
