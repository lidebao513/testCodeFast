import sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROME = r"C:\Users\EDY\AppData\Local\Google\Chrome\Application\chrome.exe"
URL = "http://47.97.154.50:8090/chat"
OUT = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test")
OUT.mkdir(parents=True, exist_ok=True)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--proxy-server=direct://", "--proxy-bypass-list=*"],
        )
        ctx = browser.new_context(ignore_https_errors=True)
        page = ctx.new_page()
        page.set_default_timeout(20000)
        logs = []
        page.on("console", lambda m: logs.append(f"[console:{m.type}] {m.text}"))
        page.on("pageerror", lambda e: logs.append(f"[pageerror] {e}"))

        print("goto", URL)
        page.goto(URL, wait_until="domcontentloaded")
        time.sleep(4)
        print("title:", page.title())
        print("url:", page.url)

        # dump inputs / buttons / forms
        fields = page.evaluate("""() => {
            const out = {url: location.href, title: document.title,
                inputs: [], buttons: [], forms: [], placeholders: [], texts: []};
            document.querySelectorAll('input,textarea').forEach(el=>{
                out.inputs.push({tag:el.tagName, type:el.type, name:el.name,
                    id:el.id, placeholder:el.placeholder, autocomplete:el.autocomplete});
            });
            document.querySelectorAll('button').forEach(el=>{
                const t=(el.innerText||'').trim(); if(t) out.buttons.push(t.slice(0,40));
            });
            document.querySelectorAll('form').forEach(f=>out.forms.push(f.getAttribute('action')||'(no action)'));
            document.querySelectorAll('[placeholder]').forEach(el=>out.placeholders.push(el.placeholder));
            // visible text snippets
            const body=document.body.innerText.replace(/\\s+/g,' ').trim();
            out.texts.push(body.slice(0,600));
            return out;
        }""")
        print("=== FIELDS ===")
        print(json.dumps(fields, ensure_ascii=False, indent=2))
        page.screenshot(path=str(OUT/"recon_landing.png"), full_page=False)
        print("screenshot ->", OUT/"recon_landing.png")

        # save logs
        (OUT/"recon_console.log").write_text("\n".join(logs), encoding="utf-8")
        ctx.close(); browser.close()

if __name__ == "__main__":
    main()
