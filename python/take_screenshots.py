"""
Taskly — Dual-Theme Automated Screenshot Generator
===================================================
Uses Playwright with Chrome to capture high-resolution
UI screenshots of Taskly across BOTH Light Theme and Dark Theme.

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


def set_theme(page, theme: str):
    """Set light or dark theme via profile popover or JS dataset."""
    page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}'); localStorage.setItem('taskly_theme', '{theme}');")
    time.sleep(0.3)


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
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".hero")

        for theme in ["light", "dark"]:
            print(f"\n🎨 Capturing screenshots for [{theme.upper()} THEME]...")
            set_theme(page, theme)

            # 1. Dashboard View
            print(f"  📷 01_dashboard_{theme}.png")
            page.click(".nav-item:has-text('Dashboard')")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"01_dashboard_{theme}.png"))

            # 2. Calendar View
            print(f"  📷 02_calendar_{theme}.png")
            page.click(".nav-item:has-text('Calendar')")
            page.wait_for_selector(".calendar-header")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"02_calendar_{theme}.png"))

            # 3. List Detail View
            print(f"  📷 03_list_detail_{theme}.png")
            page.click(".nav-item:has-text('Personal')")
            page.wait_for_selector(".list-header")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"03_list_detail_{theme}.png"))

            # 4. Add Task Modal
            print(f"  📷 04_add_task_modal_{theme}.png")
            page.click("#fab")
            page.wait_for_selector("#taskModal.open")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"04_add_task_modal_{theme}.png"))
            page.click("#taskModal .modal-close")
            time.sleep(0.3)

            # 5. Create List Modal
            print(f"  📷 05_create_list_modal_{theme}.png")
            page.click(".nav-item:has-text('Dashboard')")
            time.sleep(0.3)
            page.click("#addListBtn")
            page.wait_for_selector("#newListModal.open")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"05_create_list_modal_{theme}.png"))
            page.click("#newListModal .modal-close")
            time.sleep(0.3)

            # 6. Profile Popover
            print(f"  📷 06_profile_popover_{theme}.png")
            page.click("#avatarBtn")
            page.wait_for_selector("#profilePopover.open")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"06_profile_popover_{theme}.png"))

            # 7. Keyboard Shortcuts Modal
            print(f"  📷 07_keyboard_shortcuts_{theme}.png")
            page.click("#btn-keyboard-shortcuts")
            page.wait_for_selector("#shortcutsModal.open")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"07_keyboard_shortcuts_{theme}.png"))
            page.click("#shortcutsModal .modal-close")
            time.sleep(0.3)

            # 8. Live Search
            print(f"  📷 08_live_search_{theme}.png")
            page.fill("#searchInput", "gym")
            page.wait_for_selector(".search-results-title")
            time.sleep(0.4)
            page.screenshot(path=os.path.join(OUTPUT_DIR, f"08_live_search_{theme}.png"))
            page.fill("#searchInput", "")

        browser.close()
        print("\n✨ All 16 dual-theme screenshots generated successfully in screenshots/!")


if __name__ == "__main__":
    capture_all()
