from playwright.sync_api import sync_playwright
import os

BASE = "http://127.0.0.1:8765"
OUT = os.path.join(os.path.dirname(__file__), "shots")
os.makedirs(OUT, exist_ok=True)

PAGES = [
    ("overview", "/"),
    ("seo", "/seo/"),
    ("keywords", "/keywords/"),
    ("positioning", "/positioning/"),
    ("pages", "/pages/"),
    ("alerts", "/alerts/"),
    ("backlinks", "/backlinks/"),
    ("ads", "/ads/"),
    ("settings", "/settings/"),
]

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()

    # login
    pg.goto(f"{BASE}/login/", wait_until="networkidle")
    if "login" in pg.url:
        pg.fill("input[name=username]", "founder")
        pg.fill("input[name=password]", "Test1234!")
        pg.click("button[type=submit], input[type=submit]")
        pg.wait_for_load_state("networkidle")
    print("after login url:", pg.url)

    for name, path in PAGES:
        try:
            pg.goto(f"{BASE}{path}", wait_until="networkidle", timeout=20000)
            pg.wait_for_timeout(1200)
            pg.screenshot(path=os.path.join(OUT, f"{name}.png"), full_page=True)
            # capture a text sample of main content
            txt = pg.inner_text("body")
            print(f"=== {name} ({path}) len={len(txt)} ===")
        except Exception as e:
            print(f"!! {name} FAILED: {e}")
    b.close()
print("done ->", OUT)
