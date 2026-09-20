import os
try:/n    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:/n    pass
# -*- coding: utf-8 -*-
"""一次性前端侦察：登录后枚举 福享Agent 线上 UI 暴露的全部功能入口，
为"全功能测试"提供准确的功能模块清单（侧边栏/导航/按钮/菜单/可交互入口）。
仅读操作，不写数据。
"""
import sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROME = r"C:\Users\EDY\AppData\Local\Google\Chrome\Application\chrome.exe"
LOGIN = "http://47.97.154.50:8090/login"
CHAT = "http://47.97.154.50:8090/chat"
OUT = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test")
OUT.mkdir(parents=True, exist_ok=True)
STATE = OUT / "state.json"
EMAIL = os.getenv("RA_WEB_ACCOUNT", ""); PWD = os.getenv("RA_WEB_PASSWORD", ""); OTP = os.getenv("RA_WEB_OTP", "")
def login(page):
    page.goto(LOGIN, wait_until="domcontentloaded", timeout=40000); time.sleep(2)
    page.fill('input[placeholder="邮箱账号"]', EMAIL)
    page.fill('input[placeholder="密码"]', PWD)
    page.fill('input[placeholder="动态口令（6位）"]', OTP)
    page.click('button:has-text("登 录")'); time.sleep(6)
    return page.evaluate("""()=>({hasLogin:!!document.querySelector('input[placeholder="邮箱账号"]'),
        app:document.body.innerText.includes('新建会话')||document.body.innerText.includes('福享')})""")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--proxy-server=direct://","--proxy-bypass-list=*"])
        ctx = browser.new_context(ignore_https_errors=True, viewport={"width":1440,"height":900},
                                  storage_state=str(STATE) if STATE.exists() else None)
        page = ctx.new_page(); page.set_default_timeout(25000)
        page.goto(CHAT, wait_until="domcontentloaded", timeout=40000); time.sleep(4)
        if page.evaluate("""()=>!!document.querySelector('input[placeholder="邮箱账号"]')"""):
            print("[recon] 登录态失效，重登")
            login(page); ctx.storage_state(path=str(STATE))
            page.goto(CHAT, wait_until="domcontentloaded", timeout=40000); time.sleep(4)
        else:
            print("[recon] 复用登录态 OK")
        data = page.evaluate("""()=>{
            const out={url:location.href, title:document.title,
                buttons:[], navs:[], placeholders:[], sideTexts:[], bodyText:''};
            const seen=new Set();
            const push=(arr,t)=>{t=(t||'').trim(); if(t&&!seen.has(t)){seen.add(t); arr.push(t.slice(0,60));}};
            document.querySelectorAll('button').forEach(b=>push(out.buttons,b.innerText));
            document.querySelectorAll('a').forEach(a=>push(out.navs,a.innerText));
            document.querySelectorAll('[placeholder]').forEach(e=>out.placeholders.push(e.placeholder));
            // 侧边栏/导航区域文本（常见容器）
            document.querySelectorAll('nav, aside, [class*="sidebar"], [class*="menu"], [class*="sider"], [class*="left"]').forEach(el=>{
                const t=el.innerText.replace(/\\s+/g,' ').trim(); if(t) out.sideTexts.push(t.slice(0,400));
            });
            out.bodyText=document.body.innerText.replace(/\\s+/g,' ').trim().slice(0,2500);
            return out;
        }""")
        # 尝试点击"新建会话"以确认对话区可用
        nb=page.query_selector('button:has-text("新建会话")')
        data["hasNewSessionBtn"]=bool(nb)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        page.screenshot(path=str(OUT/"recon_full.png"), full_page=True)
        print("[recon] screenshot ->", OUT/"recon_full.png")
        ctx.close(); browser.close()

if __name__ == "__main__":
    main()
