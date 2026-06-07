"""
Playwright smoke-test for getaayu.in
Run:  python test_app.py
Requires: pip install playwright && playwright install chromium
"""
import os
import sys
from playwright.sync_api import sync_playwright, expect

BASE = "https://getaayu.in"
EMAIL = "srikanthkarkampally01@gmail.com"
PASSWORD = os.environ.get("CC_PASSWORD", "")

PASS_MARK = "[PASS]"
FAIL_MARK = "[FAIL]"
results = []

def check(label, condition, detail=""):
    status = PASS_MARK if condition else FAIL_MARK
    msg = f"{status} {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    results.append((label, condition))
    return condition


def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # ── 1. Public pages ─────────────────────────────────────────────
        print("\n=== Public Pages ===")

        page.goto(BASE + "/")
        page.wait_for_load_state("networkidle")
        check("Home page loads (200)", page.url.startswith(BASE))

        page.goto(BASE + "/health")
        page.wait_for_load_state("networkidle")
        body = page.content()
        check("Health endpoint returns ok", "ok" in body.lower() or "healthy" in body.lower(), body[:120])

        page.goto(BASE + "/login")
        page.wait_for_load_state("networkidle")
        check("Login page loads", "login" in page.url or "login" in page.content().lower())

        page.goto(BASE + "/register")
        page.wait_for_load_state("networkidle")
        check("Register page loads", "register" in page.url or "register" in page.content().lower())

        # ── 2. Auth guard – unauthenticated redirects ────────────────────
        print("\n=== Auth Guard (unauthenticated) ===")
        protected = [
            "/dashboard", "/medications", "/labs",
            "/timeline", "/alerts", "/appointments",
            "/patient/add", "/medications/add", "/labs/add",
            "/events/add", "/appointments/add",
        ]
        for path in protected:
            page.goto(BASE + path)
            page.wait_for_load_state("networkidle")
            landed = page.url
            redirected = "/login" in landed
            check(f"GET {path} -> /login when unauthed", redirected, f"landed={landed}")

        # ── 3. Login flow ────────────────────────────────────────────────
        print("\n=== Login Flow ===")
        if not PASSWORD:
            print("[SKIP] CC_PASSWORD env var not set — skipping authenticated tests")
            print("       Run:  CC_PASSWORD=your_pass python test_app.py")
        else:
            page.goto(BASE + "/login")
            page.wait_for_load_state("networkidle")
            page.fill('input[name="email"]', EMAIL)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")

            logged_in = "/dashboard" in page.url or "/no_patient" in page.url or "dashboard" in page.content().lower()
            check("Login succeeds -> dashboard or no_patient", logged_in, f"url={page.url}")

            if logged_in:
                page.screenshot(path="screenshot_dashboard.png", full_page=True)
                print("  [screenshot] screenshot_dashboard.png saved")

                # ── 4. Add forms render ──────────────────────────────────
                print("\n=== Add Forms (authenticated) ===")
                add_forms = {
                    "/patient/add":      "Patient",
                    "/medications/add":  "Medication",
                    "/labs/add":         "Lab",
                    "/events/add":       "Event",
                    "/appointments/add": "Appointment",
                }
                for path, label in add_forms.items():
                    page.goto(BASE + path)
                    page.wait_for_load_state("networkidle")
                    has_form = page.locator("form").count() > 0
                    check(f"{label} form renders at {path}", has_form, f"url={page.url}")
                    if not has_form:
                        print("  content snippet:", page.content()[:300])

                # ── 5. Core pages render when authenticated ──────────────
                print("\n=== Core Pages (authenticated) ===")
                core_pages = {
                    "/medications": "Medications",
                    "/labs":        "Lab Results",
                    "/timeline":    "Timeline",
                    "/alerts":      "Alerts",
                }
                for path, label in core_pages.items():
                    page.goto(BASE + path)
                    page.wait_for_load_state("networkidle")
                    ok = page.locator("h1, h2").count() > 0
                    check(f"{label} page renders", ok, f"url={page.url}")

                page.screenshot(path="screenshot_medications.png", full_page=True)
                print("  [screenshot] screenshot_medications.png saved")

        browser.close()

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        print("Failed checks:")
        for label, ok in results:
            if not ok:
                print(f"  - {label}")
    return passed == total


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
