import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

output_dir = Path("report/img")
output_dir.mkdir(parents=True, exist_ok=True)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Launching browser: {chrome_path}")

queries = [
    (
        "kg_count.png",
        "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;",
        5,
    ),
    (
        "kg_cross_kb.png",
        "MATCH p= (:Person)-[:INVOLVED_IN]-> (:Case)-[:CHARGED_WITH]-> (:Crime)<-[:DEFINES]- (:Article) RETURN p LIMIT 25;",
        8,
    ),
    (
        "kg_my_case.png",
        "MATCH p= (:Person {name:'Cái Quang Huy'}) -[:INVOLVED_IN]-> (k:Case) -[:CHARGED_WITH]-> (:Crime) <-[:DEFINES]- (:Article) OPTIONAL MATCH q=(k)-[:INVOLVES|LOCATED_IN]->() RETURN p, q;",
        8,
    ),
]

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=chrome_path,
        headless=True,
        args=["--disable-web-security", "--allow-file-access-from-files"]
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        permissions=["clipboard-read", "clipboard-write"]
    )
    page = context.new_page()
    
    print("Navigating to http://localhost:7474/browser/ ...")
    page.goto("http://localhost:7474/browser/", timeout=30000)
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Login if needed
    password_input = page.locator('input[type="password"]')
    if password_input.count() > 0:
        print("Logging in with password...")
        password_input.first.click()
        password_input.first.fill("password123")
        time.sleep(1)
        password_input.first.press("Enter")
        time.sleep(5)
    
    # Dismiss any welcome tooltips
    dismiss_btn = page.locator('button:has-text("Dismiss")')
    if dismiss_btn.count() > 0:
        dismiss_btn.first.click()
        time.sleep(1)
        print("Dismissed popup tooltip")

    editor_el = page.locator('.monaco-editor, div[role="textbox"]').first

    def set_and_run(cmd: str, wait_sec: int, out_filename: str | None = None):
        print(f"Setting query: {cmd[:60]}...")
        # Dismiss any popup if still there
        if page.locator('button:has-text("Dismiss")').count() > 0:
            page.locator('button:has-text("Dismiss")').first.click()
            time.sleep(0.5)

        editor_el.click()
        time.sleep(0.3)

        # Use Monaco API or clipboard to paste exact unicode string
        success = page.evaluate("""(text) => {
            if (window.monaco && window.monaco.editor && window.monaco.editor.getEditors().length > 0) {
                window.monaco.editor.getEditors()[0].setValue(text);
                return true;
            }
            return false;
        }""", cmd)

        if not success:
            page.keyboard.press("Control+A")
            time.sleep(0.2)
            page.keyboard.press("Backspace")
            time.sleep(0.2)
            page.evaluate("(text) => navigator.clipboard.writeText(text)", cmd)
            page.keyboard.press("Control+V")
            time.sleep(0.3)

        # Press Control+Enter to execute query
        page.keyboard.press("Control+Enter")
        print(f"Executing and waiting {wait_sec}s...")
        time.sleep(wait_sec)

        # Again check if any popup appeared
        if page.locator('button:has-text("Dismiss")').count() > 0:
            page.locator('button:has-text("Dismiss")').first.click()
            time.sleep(0.5)

        if out_filename:
            out_path = output_dir / out_filename
            page.screenshot(path=str(out_path))
            print(f"--> Successfully saved {out_path} ({os.path.getsize(out_path)} bytes)")

    # Clear screen initially
    set_and_run(":clear", 2)

    for filename, cypher, wait_s in queries:
        set_and_run(":clear", 1)
        set_and_run(cypher, wait_s, filename)
        time.sleep(1)

    browser.close()
    print("ALL 3 SCREENSHOTS CAPTURED PERFECTLY!")
