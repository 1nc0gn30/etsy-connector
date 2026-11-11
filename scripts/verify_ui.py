"""
verify_ui.py
Automated Headless Playwright Verification Harness for Etsy Connector
Verifies triple-viewport responsiveness, zero console errors, and zero horizontal overflow.
"""

import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SHOT_DIR = Path(os.environ.get("ETSY_CONNECTOR_SHOT_DIR", "/tmp/etsy_connector_shots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.environ.get("PORT", "8108"))
BASE_URL = f"http://127.0.0.1:{PORT}"


def verify() -> None:
    viewports = [
        {"name": "home_mobile.jpg", "width": 390, "height": 844, "device": "Mobile (390x844)"},
        {"name": "home_tablet.jpg", "width": 820, "height": 1180, "device": "Tablet (820x1180)"},
        {"name": "home_desktop.jpg", "width": 1425, "height": 900, "device": "Desktop (1425x900)"},
    ]
    results = {"viewports": [], "consoleErrors": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        for vp in viewports:
            page = browser.new_page(viewport={"width": vp["width"], "height": vp["height"]})
            errs = []
            page.on("console", lambda msg: errs.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: errs.append(str(err)))
            page.goto(BASE_URL, wait_until="networkidle")
            time.sleep(0.4)
            overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            shot_path = SHOT_DIR / vp["name"]
            page.screenshot(path=str(shot_path), full_page=False, type="jpeg", quality=85)
            passed = len(errs) == 0 and overflow <= 1
            results["viewports"].append({"device": vp["device"], "overflow": f"{overflow}px", "passed": passed})
            results["consoleErrors"].extend(errs)
            page.close()
        browser.close()

    print(json.dumps(results, indent=2))
    sys.exit(0 if all(v["passed"] for v in results["viewports"]) else 1)


if __name__ == "__main__":
    verify()
