import os
try:/n    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:/n    pass
import sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROME = r"C:\Users\EDY\AppData\Local\Google\Chrome\Application\chrome.exe"
LOGIN = "http://47.97.154.50:8090/login"
OUT = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test")
OUT.mkdir(parents=True, exist_ok=True)
EMAIL = os.getenv("RA_WEB_ACCOUNT", ""); PWD = os.getenv("RA_WEB_PASSWORD", ""); OTP = os.getenv("RA_WEB_OTP", "")
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--proxy-server=direct://","--proxy-bypass-list=*"])
        ctx = browser.new_context(ignore_https_errors=True)
        page = ctx.new_page(); page.set_default_timeout(25000)
        page.goto(LOGIN, wait_until="domcontentloaded"); time.sleep(2)
        page.fill('input[placeholder="邮箱账号"]', EMAIL)
        page.fill('input[placeholder="密码"]', PWD)
        page.fill('input[placeholder="动态口令（6位）"]', OTP)
        page.click('button:has-text("登 录")'); time.sleep(6)
        # authenticated?
        auth = page.evaluate("""() => {
            const body=document.body.innerText;
            const hasLoginForm = !!document.querySelector('input[placeholder="邮箱账号"]');
            const hasApp = body.includes('新建会话') || body.includes('福享AI');
            return {hasLoginForm, hasApp, url: location.href};
        }""")
        print("AUTH CHECK:", json.dumps(auth, ensure_ascii=False))
        if auth["hasLoginForm"] or not auth["hasApp"]:
            print("LOGIN NOT OK"); page.screenshot(path=str(OUT/"login_failed.png")); ctx.close(); browser.close(); return
        print("LOGIN OK — exploring chat composer on current page")
        info = page.evaluate("""() => {
            const o={url:location.href,
                textareas:[], inputs:[], buttons:[], contenteditables:[],
                divs_with_input_cls:[]};
            document.querySelectorAll('textarea').forEach(e=>o.textareas.push({ph:e.placeholder,id:e.id,cls:(e.className||'').toString().slice(0,80)}));
            document.querySelectorAll('input:not([type=hidden])').forEach(e=>o.inputs.push({type:e.type,ph:e.placeholder,id:e.id}));
            document.querySelectorAll('button').forEach(e=>{const t=(e.innerText||'').trim(); if(t)o.buttons.push(t.slice(0,30));});
            document.querySelectorAll('[contenteditable="true"]').forEach(e=>o.contenteditables.push((e.className||'').toString().slice(0,80)));
            o.bodyTop = document.body.innerText.replace(/\\s+/g,' ').trim().slice(0,300);
            return o;
        }""")
        print(json.dumps(info, ensure_ascii=False, indent=2))
        page.screenshot(path=str(OUT/"chat_after_login.png"), full_page=False)
        # probe send
        ta = page.query_selector('textarea')
        if ta:
            ta.click(); ta.fill("你好，请用一句话介绍你能做什么。")
            # press Enter
            page.keyboard.press("Enter"); time.sleep(3)
            still = page.evaluate("()=>document.querySelector('textarea')?.value||''")
            if still.strip():
                for b in page.query_selector_all('button'):
                    t=(b.inner_text or '').strip()
                    if t in ("发送","Send") or t in "➤➡↑":
                        b.click(); break
            time.sleep(25)
            resp = page.evaluate("""() => {
                const all=[...document.querySelectorAll('div,p,span,li,pre,article')].map(e=>e.innerText).filter(t=>t&&t.trim().length>15);
                return {count:all.length, sample:all.slice(-8)};
            }""")
            print("=== PROBE RESPONSE ===")
            print(json.dumps(resp, ensure_ascii=False, indent=2))
            page.screenshot(path=str(OUT/"chat_hello_resp.png"), full_page=False)
        ctx.close(); browser.close()

if __name__ == "__main__":
    main()
