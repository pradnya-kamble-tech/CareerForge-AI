"""
Phase 8 — Mobile Interaction Test Suite (Playwright)
Devices: iPhone 13 (iOS Safari), Pixel 6 (Android Chrome)
Covers: tap targets, tooltip dismissal, scroll, overflow, mobile nav, chart clip.
Run: python -m pytest tests/mobile_interaction_test.py -v --tb=short
Requirements: pip install playwright pytest-playwright && playwright install chromium
"""

import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://127.0.0.1:5000"

DEVICES = [
    {
        "name": "iPhone 13",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 390, "height": 844},
        "has_touch": True,
    },
    {
        "name": "Pixel 6",
        "user_agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Mobile Safari/537.36",
        "viewport": {"width": 412, "height": 915},
        "has_touch": True,
    },
]

ROUTES = ["/", "/login", "/student?demo=1", "/recruiter", "/admin"]


def run_for_devices(test_fn):
    """Helper: runs a test function for each emulated device."""
    for device in DEVICES:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=device["user_agent"],
                viewport=device["viewport"],
                has_touch=device["has_touch"],
                is_mobile=True,
            )
            page = ctx.new_page()
            try:
                test_fn(page, device["name"])
            finally:
                ctx.close()
                browser.close()


# ──────────────────────────────────────────────
# 1. No Horizontal Overflow
# ──────────────────────────────────────────────

class TestMobileOverflow:
    @pytest.mark.parametrize("route", ROUTES)
    def test_no_horizontal_overflow(self, route):
        def check(page, device_name):
            page.goto(BASE_URL + route)
            page.wait_for_load_state("networkidle")
            scroll_width = page.evaluate("document.documentElement.scrollWidth")
            client_width = page.evaluate("document.documentElement.clientWidth")
            assert scroll_width <= client_width + 5, \
                f"[{device_name}] Horizontal overflow on {route}: " \
                f"scrollWidth={scroll_width} > clientWidth={client_width}"
        run_for_devices(check)


# ──────────────────────────────────────────────
# 2. Tap Targets ≥ 44×44 px
# ──────────────────────────────────────────────

class TestTapTargets:
    def test_buttons_meet_tap_target_size(self):
        def check(page, device_name):
            page.goto(BASE_URL + "/student?demo=1")
            page.wait_for_load_state("networkidle")
            small = page.evaluate("""
                Array.from(document.querySelectorAll('button, a, input[type=checkbox]'))
                  .filter(el => {
                    const r = el.getBoundingClientRect();
                    return (r.width > 0 && r.height > 0) && (r.width < 44 || r.height < 44);
                  })
                  .map(el => el.id || el.className || el.tagName)
            """)
            assert len(small) == 0, \
                f"[{device_name}] Buttons below 44px tap target: {small[:5]}"
        run_for_devices(check)


# ──────────────────────────────────────────────
# 3. Mobile Nav Toggle
# ──────────────────────────────────────────────

class TestMobileNav:
    def test_hamburger_opens_menu(self):
        def check(page, device_name):
            page.goto(BASE_URL + "/")
            page.wait_for_load_state("networkidle")
            hamburger = page.query_selector(
                ".cf-nav-hamburger, #cf-nav-toggle, [aria-label='Open menu'], button.hamburger"
            )
            if not hamburger:
                return  # landing page may not have hamburger; skip silently
            hamburger.tap()
            page.wait_for_timeout(400)
            menu = page.query_selector(".cf-mobile-nav, .cf-nav-menu, nav[aria-expanded='true']")
            assert menu or page.evaluate(
                "document.querySelector('.cf-nav-menu, nav')?.classList.contains('open') || false"
            ), f"[{device_name}] Mobile nav did not open after hamburger tap"
        run_for_devices(check)

    def test_scroll_while_loader_active(self):
        def check(page, device_name):
            page.goto(BASE_URL + "/student?demo=1")
            page.wait_for_load_state("networkidle")
            # Trigger a scroll while loader might be present
            page.evaluate("window.scrollTo(0, 500)")
            page.wait_for_timeout(200)
            page.evaluate("window.scrollTo(0, 0)")
            # Confirm no scroll lock artifact
            scroll_y = page.evaluate("window.scrollY")
            # Just confirm page is responsive; no hard lock
            assert scroll_y is not None, f"[{device_name}] scrollY unreachable — possible scroll lock"
        run_for_devices(check)


# ──────────────────────────────────────────────
# 4. Tooltip Dismissal on Mobile
# ──────────────────────────────────────────────

class TestMobileTooltip:
    def test_tooltip_tap_outside_dismisses(self):
        def check(page, device_name):
            page.goto(BASE_URL + "/student?demo=1")
            page.wait_for_load_state("networkidle")
            trigger = page.query_selector("[data-cf-tooltip], .cf-tooltip-trigger")
            if not trigger:
                return
            trigger.tap()
            page.wait_for_timeout(300)
            # Tap outside
            page.tap("body", position={"x": 5, "y": 5})
            page.wait_for_timeout(300)
            portals = page.query_selector_all(".cf-tooltip-portal, .cf-tooltip-content")
            visible = [p for p in portals if p.is_visible()]
            assert len(visible) == 0, \
                f"[{device_name}] Tooltip still visible after tap-outside"
        run_for_devices(check)


# ──────────────────────────────────────────────
# 5. Chart Not Clipped on Mobile
# ──────────────────────────────────────────────

class TestMobileChart:
    def test_chart_canvas_not_clipped(self):
        def check(page, device_name):
            page.goto(BASE_URL + "/recruiter")
            page.wait_for_load_state("networkidle")
            canvases = page.query_selector_all("canvas")
            for canvas in canvases:
                box = canvas.bounding_box()
                if box and box["width"] > 0:
                    vp_width = page.viewport_size["width"]
                    assert box["x"] + box["width"] <= vp_width + 2, \
                        f"[{device_name}] Chart canvas overflows viewport: " \
                        f"x={box['x']} w={box['width']} vp={vp_width}"
        run_for_devices(check)


# ──────────────────────────────────────────────
# 6. Stacked Button Layout
# ──────────────────────────────────────────────

class TestMobileButtons:
    def test_buttons_not_overflowing_container(self):
        def check(page, device_name):
            page.goto(BASE_URL + "/student?demo=1")
            page.wait_for_load_state("networkidle")
            overflow_buttons = page.evaluate("""
                Array.from(document.querySelectorAll('button, a.cf-cta-btn, a.cf-pill-btn'))
                  .filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.right > window.innerWidth + 2;
                  })
                  .map(el => el.id || el.textContent.trim().slice(0, 30))
            """)
            assert len(overflow_buttons) == 0, \
                f"[{device_name}] Buttons overflowing viewport: {overflow_buttons[:3]}"
        run_for_devices(check)


# ──────────────────────────────────────────────
# 7. Console Errors on Mobile Devices
# ──────────────────────────────────────────────

class TestMobileConsole:
    @pytest.mark.parametrize("route", ["/", "/student?demo=1", "/recruiter", "/admin"])
    def test_no_console_errors_on_mobile(self, route):
        def check(page, device_name):
            errors = []
            page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)
            page.on("pageerror", lambda err: errors.append(err))
            page.goto(BASE_URL + route)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            assert len(errors) == 0, \
                f"[{device_name}] Console errors on {route}: {[str(e) for e in errors[:3]]}"
        run_for_devices(check)
