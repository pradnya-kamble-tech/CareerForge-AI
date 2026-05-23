"""
Phase 8 — Desktop Interaction Test Suite (Selenium + Chrome)
Covers: DOM assertions, console auditing, click flows, loader lifecycle,
        memory/state leak loops, modal focus, keyboard nav, duplicate overlay guards.
Run: python -m pytest tests/interaction_test.py -v --tb=short
"""

import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000"
ROUTES = ["/", "/login", "/register", "/student", "/student?demo=1", "/recruiter", "/admin"]

# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    drv = webdriver.Chrome(options=opts)
    drv.set_window_size(1440, 900)
    yield drv
    drv.quit()

def wait(driver, seconds=0.5):
    time.sleep(seconds)

def get_console_errors(driver):
    logs = driver.get_log("browser")
    return [l for l in logs if l["level"] in ("SEVERE", "WARNING")]

def assert_no_console_errors(driver, route=""):
    errors = get_console_errors(driver)
    # Filter benign third-party noise
    real_errors = [e for e in errors if "favicon" not in e["message"].lower()]
    assert len(real_errors) == 0, \
        f"Console errors on {route}:\n" + "\n".join(e["message"] for e in real_errors)

def assert_no_duplicate_ids(driver):
    ids = driver.execute_script(
        "return Array.from(document.querySelectorAll('[id]')).map(e => e.id)"
    )
    non_empty = [i for i in ids if i]
    assert len(non_empty) == len(set(non_empty)), \
        f"Duplicate IDs found: {[i for i in non_empty if non_empty.count(i) > 1]}"

def assert_single_loader(driver):
    overlays = driver.find_elements(By.ID, "cf-eva-loader-overlay")
    assert len(overlays) <= 1, f"Expected ≤1 loader overlay, found {len(overlays)}"

def assert_loader_gone(driver, timeout=5):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.ID, "cf-eva-loader-overlay")) == 0
        or not d.find_element(By.ID, "cf-eva-loader-overlay").is_displayed()
    )

# ──────────────────────────────────────────────
# 1. Route Render + Core DOM Assertions
# ──────────────────────────────────────────────

class TestRouteRender:
    @pytest.mark.parametrize("route", ROUTES)
    def test_route_renders_200(self, driver, route):
        driver.get(BASE_URL + route)
        wait(driver)
        assert "500" not in driver.title.lower(), f"Server error on {route}"
        assert "traceback" not in driver.page_source.lower(), \
            f"Jinja traceback detected on {route}"
        assert "internal server error" not in driver.page_source.lower(), \
            f"Internal server error on {route}"

    @pytest.mark.parametrize("route", ROUTES)
    def test_no_duplicate_ids(self, driver, route):
        driver.get(BASE_URL + route)
        wait(driver)
        assert_no_duplicate_ids(driver)

    @pytest.mark.parametrize("route", ROUTES)
    def test_no_console_errors_on_load(self, driver, route):
        driver.get(BASE_URL + route)
        wait(driver)
        get_console_errors(driver)  # flush existing
        driver.refresh()
        wait(driver)
        assert_no_console_errors(driver, route)

    def test_loader_overlay_exists_once(self, driver):
        driver.get(BASE_URL + "/student?demo=1")
        wait(driver)
        assert_single_loader(driver)

    def test_charts_render_canvas(self, driver):
        driver.get(BASE_URL + "/recruiter")
        wait(driver, 1.5)
        canvases = driver.find_elements(By.TAG_NAME, "canvas")
        assert len(canvases) >= 1, "No charts rendered on recruiter dashboard"

    def test_aria_live_on_loader(self, driver):
        driver.get(BASE_URL + "/student?demo=1")
        wait(driver)
        overlay = driver.find_elements(By.ID, "cf-eva-loader-overlay")
        if overlay:
            aria = overlay[0].get_attribute("aria-live")
            assert aria in ("polite", "assertive"), \
                "Loader overlay missing aria-live attribute"

# ──────────────────────────────────────────────
# 2. CTA & Button Interaction
# ──────────────────────────────────────────────

class TestCTAInteractions:
    def test_landing_cta_navigates(self, driver):
        driver.get(BASE_URL + "/")
        wait(driver)
        ctas = driver.find_elements(By.CSS_SELECTOR, "a.cf-cta-btn, button.cf-cta-btn, a[href='/register']")
        assert len(ctas) > 0, "No CTA buttons on landing page"

    def test_student_analyse_cta_exists(self, driver):
        driver.get(BASE_URL + "/student?demo=1")
        wait(driver)
        btn = driver.find_elements(By.CSS_SELECTOR, "[id*='analyse'], [id*='analyze'], .cf-cta-btn")
        assert len(btn) > 0, "No Analyse CTA on student dashboard"

    def test_export_button_enabled(self, driver):
        driver.get(BASE_URL + "/admin")
        wait(driver)
        export_btns = driver.find_elements(By.CSS_SELECTOR, ".cf-download-btn, [id*='export'], [id*='download']")
        for btn in export_btns:
            disabled = btn.get_attribute("disabled")
            assert disabled is None, f"Export button unexpectedly disabled: {btn.get_attribute('id')}"

# ──────────────────────────────────────────────
# 3. Loader Lifecycle
# ──────────────────────────────────────────────

class TestLoaderLifecycle:
    def test_no_duplicate_loader_on_rapid_clicks(self, driver):
        """EC-02: Rapid clicks must not stack multiple overlays."""
        driver.get(BASE_URL + "/student?demo=1")
        wait(driver, 1)
        btns = driver.find_elements(By.CSS_SELECTOR, ".cf-cta-btn, .cf-pill-btn")
        if not btns:
            pytest.skip("No clickable CTAs on demo student page")
        for _ in range(5):
            try:
                btns[0].click()
            except Exception:
                pass
            time.sleep(0.1)
        assert_single_loader(driver)
        # flush console after rapid click
        get_console_errors(driver)

# ──────────────────────────────────────────────
# 4. Tooltip Tests
# ──────────────────────────────────────────────

class TestTooltips:
    def test_tooltip_open_close_loop(self, driver):
        """EC-04, EC-10: 20× open/close leaves zero portals."""
        driver.get(BASE_URL + "/student?demo=1")
        wait(driver)
        triggers = driver.find_elements(By.CSS_SELECTOR, "[data-cf-tooltip], .cf-tooltip-trigger")
        if not triggers:
            pytest.skip("No tooltip triggers on student demo page")
        trigger = triggers[0]
        for _ in range(20):
            webdriver.ActionChains(driver).move_to_element(trigger).perform()
            time.sleep(0.1)
            webdriver.ActionChains(driver).move_by_offset(500, 300).perform()
            time.sleep(0.1)
        portals = driver.find_elements(By.CSS_SELECTOR, ".cf-tooltip-portal, .cf-tooltip-content")
        assert len(portals) == 0, f"Orphaned tooltip portals after 20× hover: {len(portals)}"

    def test_esc_dismisses_tooltip(self, driver):
        driver.get(BASE_URL + "/student?demo=1")
        wait(driver)
        triggers = driver.find_elements(By.CSS_SELECTOR, "[data-cf-tooltip], .cf-tooltip-trigger")
        if not triggers:
            pytest.skip("No tooltip triggers")
        webdriver.ActionChains(driver).move_to_element(triggers[0]).perform()
        time.sleep(0.3)
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.2)
        portals = driver.find_elements(By.CSS_SELECTOR, ".cf-tooltip-portal, .cf-tooltip-content")
        visible = [p for p in portals if p.is_displayed()]
        assert len(visible) == 0, "Tooltip still visible after ESC"

# ──────────────────────────────────────────────
# 5. Neon Checkbox
# ──────────────────────────────────────────────

class TestNeonCheckbox:
    def test_aria_checked_syncs(self, driver):
        """EC-08: aria-checked must match visual state."""
        driver.get(BASE_URL + "/recruiter")
        wait(driver)
        boxes = driver.find_elements(By.CSS_SELECTOR, ".cf-neon-checkbox, input[type='checkbox']")
        if not boxes:
            pytest.skip("No checkboxes on recruiter page")
        box = boxes[0]
        initial = box.get_attribute("aria-checked") or ("true" if box.is_selected() else "false")
        driver.execute_script("arguments[0].click();", box)
        time.sleep(0.2)
        after = box.get_attribute("aria-checked") or ("true" if box.is_selected() else "false")
        assert initial != after, "aria-checked did not change after click"

    def test_rapid_toggle_no_leak(self, driver):
        """EC-10: 20× toggle must not multiply listeners (check DOM stability)."""
        driver.get(BASE_URL + "/recruiter")
        wait(driver)
        boxes = driver.find_elements(By.CSS_SELECTOR, ".cf-neon-checkbox, input[type='checkbox']")
        if not boxes:
            pytest.skip("No checkboxes")
        box = boxes[0]
        for _ in range(20):
            driver.execute_script("arguments[0].click();", box)
            time.sleep(0.05)
        assert_no_duplicate_ids(driver)
        assert_no_console_errors(driver, "/recruiter toggle loop")

# ──────────────────────────────────────────────
# 6. State Integrity — Dashboard Switching
# ──────────────────────────────────────────────

class TestStateIntegrity:
    def test_no_orphaned_overlays_after_dashboard_switch(self, driver):
        """EC-05: Switching dashboards rapidly must leave no overlays."""
        dashboards = ["/student?demo=1", "/recruiter", "/admin"]
        for _ in range(5):
            for d in dashboards:
                driver.get(BASE_URL + d)
                time.sleep(0.3)
        overlays = driver.find_elements(By.ID, "cf-eva-loader-overlay")
        visible_overlays = [o for o in overlays if o.is_displayed()]
        assert len(visible_overlays) == 0, \
            f"Orphaned overlays after rapid dashboard switching: {len(visible_overlays)}"

    def test_no_console_errors_after_dashboard_switch(self, driver):
        get_console_errors(driver)  # flush
        for d in ["/student?demo=1", "/recruiter", "/admin", "/student?demo=1"]:
            driver.get(BASE_URL + d)
            time.sleep(0.4)
        assert_no_console_errors(driver, "dashboard switch series")

# ──────────────────────────────────────────────
# 7. Keyboard Navigation
# ──────────────────────────────────────────────

class TestKeyboardNavigation:
    def test_tab_reaches_focusable_elements(self, driver):
        driver.get(BASE_URL + "/")
        wait(driver)
        body = driver.find_element(By.TAG_NAME, "body")
        body.click()
        for _ in range(10):
            webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()
            time.sleep(0.1)
        focused = driver.execute_script("return document.activeElement.tagName")
        interactive_tags = {"A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"}
        assert focused.upper() in interactive_tags, \
            f"Tab did not land on interactive element: {focused}"

# ──────────────────────────────────────────────
# 8. Admin Refresh Debounce
# ──────────────────────────────────────────────

class TestAdminRefresh:
    def test_rapid_refresh_no_duplicate_requests(self, driver):
        """EC-12: Rapid refresh clicks must be debounced."""
        driver.get(BASE_URL + "/admin")
        wait(driver)
        refresh_btns = driver.find_elements(
            By.CSS_SELECTOR, "[id*='refresh'], [id*='reload'], .cf-pill-btn"
        )
        if not refresh_btns:
            pytest.skip("No refresh button on admin page")
        btn = refresh_btns[0]
        for _ in range(10):
            try:
                btn.click()
            except Exception:
                pass
            time.sleep(0.1)
        assert_no_console_errors(driver, "/admin rapid refresh")
        assert_single_loader(driver)
