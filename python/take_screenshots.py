"""
Taskly — Automated Screenshot Generator
========================================
Uses Playwright with system Chrome to capture high-resolution
UI screenshots of Taskly for README and documentation.

Usage:
  python3 python/take_screenshots.py
"""

import os
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR  = os.path.join(BASE_DIR, "screenshots")
URL         = "http://localhost:5050"


def capture_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--font-render-hinting=none"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 880},
            device_scale_factor=2,  # Crisp high-DPI retina screenshots
        )
        page = context.new_page()

        # 1. Dashboard View
        print("📷 Capturing 01_dashboard.png...")
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".hero")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_dashboard.png"))

        # 2. List Detail View
        print("📷 Capturing 02_list_detail.png...")
        # Click on the Personal list card
        page.click(".list-card:has-text('Personal')")
        page.wait_for_selector(".list-header")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "02_list_detail.png"))

        # 3. Add Task Modal
        print("📷 Capturing 03_add_task_modal.png...")
        page.click("#fab")
        page.wait_for_selector("#taskModal.open")
        time.sleep(0.4)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "03_add_task_modal.png"))
        page.click("#taskModal .modal-close")
        time.sleep(0.3)

        # 4. Create List Modal
        print("📷 Capturing 04_create_list_modal.png...")
        page.click(".back-btn")  # Go back to dashboard
        page.wait_for_selector(".hero")
        page.click("#addListBtn")
        page.wait_for_selector("#newListModal.open")
        time.sleep(0.4)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "04_create_list_modal.png"))
        page.click("#newListModal .modal-close")
        time.sleep(0.3)

        # 5. Profile Popover
        print("📷 Capturing 05_profile_popover.png...")
        page.click("#avatarBtn")
        page.wait_for_selector("#profilePopover.open")
        time.sleep(0.4)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "05_profile_popover.png"))

        # 6. Keyboard Shortcuts Modal
        print("📷 Capturing 06_keyboard_shortcuts.png...")
        page.click("#btn-keyboard-shortcuts")
        page.wait_for_selector("#shortcutsModal.open")
        time.sleep(0.4)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "06_keyboard_shortcuts.png"))
        page.click("#shortcutsModal .modal-close")
        time.sleep(0.3)

        # 7. Live Search
        print("📷 Capturing 07_live_search.png...")
        page.fill("#searchInput", "gym")
        page.wait_for_selector(".search-results-title")
        time.sleep(0.4)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "07_live_search.png"))

        browser.close()
        print("\n✨ All screenshots generated successfully in screenshots/!")


if __name__ == "__main__":
    capture_all()
