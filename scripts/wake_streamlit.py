"""Open the Streamlit Community Cloud app in a real browser and wake it if asleep.

Streamlit Cloud apps sleep after about 12 hours without visitors, and a plain
HTTP GET does not wake them (the page is a static shell until JavaScript and
the WebSocket connect). This uses headless Chromium via Playwright, clicks the
"wake up" button when it is shown, and checks that the app itself rendered.

    python scripts/wake_streamlit.py https://hiresense-ai-vishal.streamlit.app "HireSense"
"""
import sys
import time

from playwright.sync_api import sync_playwright

WAKE_TEXT = "get this app back up"


def app_text(page):
    texts = []
    for frame in page.frames:
        try:
            texts.append(frame.locator("body").inner_text(timeout=2000))
        except Exception:
            pass
    return "\n".join(texts)


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://hiresense-ai-vishal.streamlit.app"
    expect = sys.argv[2] if len(sys.argv) > 2 else "HireSense"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(8000)

        woke = False
        button = page.locator(f"button:has-text('{WAKE_TEXT}')")
        if button.count():
            print("App was asleep, clicking the wake-up button")
            button.first.click()
            woke = True

        start = time.time()
        while time.time() - start < 300:
            text = app_text(page)
            if expect.lower() in text.lower() and WAKE_TEXT not in text.lower():
                print(f"OK   app rendered after {time.time() - start:.0f}s (woken={woke})")
                browser.close()
                return
            page.wait_for_timeout(10_000)
        page.screenshot(path="streamlit_failure.png", full_page=True)
        browser.close()
        raise SystemExit(f"FAIL app did not show '{expect}' within 5 minutes")


if __name__ == "__main__":
    main()
