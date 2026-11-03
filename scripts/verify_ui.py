"""
verify_ui.py
Automated Headless Playwright Verification Harness for Etsy Connector
Triple-Viewport Responsiveness, Zero Console Errors, Zero Horizontal Overflow,
Action Interception on Blueprint CSV Export, Instant Key Activation, and Clean URL Parameter Strip.
"""

import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

SHOT_DIR = Path('~/.gemini/antigravity-cli/brain/302ed169-2fc4-4fe5-98e4-ebd229505405/pod_shots/etsy_connector')
SHOT_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8852
BASE_URL = f"http://127.0.0.1:{PORT}"

def verify():
    print(f"[TEST] Starting Python Playwright Headless Verification on {BASE_URL}...")

    viewports = [
        {"name": "home_mobile.jpg", "width": 390, "height": 844, "device": "Mobile (iPhone 14)"},
        {"name": "home_tablet.jpg", "width": 820, "height": 1180, "device": "Tablet (iPad Air)"},
        {"name": "home_desktop.jpg", "width": 1425, "height": 900, "device": "Desktop (HD)"},
    ]

    results = {
        "viewports": [],
        "interceptionPass": False,
        "keyActivationPass": False,
        "urlParamPass": False,
        "consoleErrors": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )

        # 1. Triple Viewport Tests
        for vp in viewports:
            page = browser.new_page(viewport={"width": vp["width"], "height": vp["height"]})
            console_errors = []

            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            page.goto(BASE_URL, wait_until="networkidle")
            time.sleep(0.5)

            overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")

            shot_path = SHOT_DIR / vp["name"]
            page.screenshot(path=str(shot_path), full_page=False, type="jpeg", quality=85)

            passed = (len(console_errors) == 0 and overflow <= 1)
            print(f"[VIEWPORT] {vp['device']}: ConsoleErrors={len(console_errors)}, Overflow={overflow}px -> {'PASS' if passed else 'FAIL'}")

            for err in console_errors:
                results["consoleErrors"].append(f"[{vp['device']}] {err}")

            results["viewports"].append({
                "device": vp["device"],
                "width": vp["width"],
                "height": vp["height"],
                "consoleErrors": len(console_errors),
                "overflow": f"{overflow}px",
                "passed": passed,
                "screenshot": str(shot_path)
            })

            page.close()

        # 2. Interactive Interception & Key Verification Test
        context = browser.new_context(viewport={"width": 1425, "height": 900})
        page = context.new_page()
        interactive_errors = []

        page.on("console", lambda msg: interactive_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: interactive_errors.append(str(err)))

        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(0.5)

        initial_badge = page.locator("#licenseBadge").inner_text().strip()
        print(f"[BADGE] Initial badge text: '{initial_badge}'")

        # Switch to Tab 3 (POD) and trigger action interception on #btn-export-matrix
        print("[ACTION] Switching to tab-pod and triggering #btn-export-matrix...")
        page.evaluate("() => switchTab('pod')")
        time.sleep(0.3)
        page.evaluate("() => document.getElementById('btn-export-matrix').click()")
        time.sleep(0.4)

        modal_displayed = page.evaluate("() => window.getComputedStyle(document.getElementById('paywall-modal')).display !== 'none'")
        print(f"[MODAL] #paywall-modal is displayed: {modal_displayed}")
        results["interceptionPass"] = modal_displayed

        paywall_shot = SHOT_DIR / "paywall_modal.jpg"
        page.screenshot(path=str(paywall_shot), full_page=False, type="jpeg", quality=85)

        # Enter Key ETSY-PRO-2026 and Activate
        print("[LICENSE] Entering key 'ETSY-PRO-2026' in modal...")
        page.fill("#licenseKeyInput", "ETSY-PRO-2026")
        page.click("#btnActivateKey")
        time.sleep(0.6)

        unlocked_badge = page.locator("#licenseBadge").inner_text().strip()
        banner_hidden = page.evaluate("() => window.getComputedStyle(document.getElementById('salesBanner')).display === 'none'")
        overlay_hidden = page.evaluate("() => window.getComputedStyle(document.getElementById('podOverlay')).display === 'none'")
        blur_removed = page.evaluate("() => !document.getElementById('podJsonCode').classList.contains('blurred-content')")

        print(f"[LICENSE] Unlocked badge: '{unlocked_badge}'")
        print(f"[LICENSE] Sales banner hidden: {banner_hidden}")
        print(f"[LICENSE] POD overlay hidden: {overlay_hidden}")
        print(f"[LICENSE] Blur removed: {blur_removed}")

        results["keyActivationPass"] = ("PRO ACTIVE" in unlocked_badge and banner_hidden and overlay_hidden and blur_removed)

        unlocked_shot = SHOT_DIR / "pro_active_unlocked.jpg"
        page.screenshot(path=str(unlocked_shot), full_page=False, type="jpeg", quality=85)

        page.close()
        context.close()

        # 3. Test Fresh Load with ?licensed=true and URL parameter cleanup
        print("[URL] Testing instant 1-click checkout return ?licensed=true...")
        return_context = browser.new_context(viewport={"width": 1425, "height": 900})
        return_page = return_context.new_page()

        return_page.goto(f"{BASE_URL}/?licensed=true", wait_until="networkidle")
        time.sleep(0.5)

        return_badge = return_page.locator("#licenseBadge").inner_text().strip()
        current_url = return_page.url
        url_cleaned = "licensed=true" not in current_url

        print(f"[URL] Return badge: '{return_badge}', URL: '{current_url}', Cleaned: {url_cleaned}")
        results["urlParamPass"] = ("PRO ACTIVE" in return_badge and url_cleaned)

        return_page.close()
        return_context.close()

        browser.close()

    print("\n========================================")
    print("[RESULTS SUMMARY]")
    print(json.dumps(results, indent=2))
    print("========================================\n")

    all_passed = (
        all(vp["passed"] for vp in results["viewports"]) and
        results["interceptionPass"] and
        results["keyActivationPass"] and
        results["urlParamPass"] and
        len(results["consoleErrors"]) == 0
    )

    if all_passed:
        print("✅ ALL VERIFICATION CHECKS PASSED (100%)")
        sys.exit(0)
    else:
        print("❌ VERIFICATION CHECKS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    verify()
