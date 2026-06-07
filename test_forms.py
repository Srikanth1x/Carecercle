"""
End-to-end test of all data entry forms (assumes patient already linked).
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "https://getaayu.in"
EMAIL = "srikanthkarkampally01@gmail.com"
PASSWORD = "123456"

results = []

def check(label, condition, detail=""):
    status = "[PASS]" if condition else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    results.append((label, condition))
    return condition

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ── Login ────────────────────────────────────────────────────────
        print("\n=== Login ===")
        page.goto(BASE + "/login")
        page.wait_for_load_state("networkidle")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        check("Login -> /dashboard", "/dashboard" in page.url, page.url)

        # ── Dashboard state ───────────────────────────────────────────────
        print("\n=== Dashboard ===")
        page.screenshot(path="ss_dashboard.png", full_page=True)
        has_patient = "No patient linked" not in page.content()
        check("Patient is linked (not 'No patient linked')", has_patient)
        if not has_patient:
            print("  STOP: patient not linked — cannot test forms")
            browser.close()
            return False

        # ── Add medication ────────────────────────────────────────────────
        print("\n=== Add Medication ===")
        page.goto(BASE + "/medications/add")
        page.wait_for_load_state("networkidle")
        check("Medication form loads", page.locator("form").count() > 0, page.url)

        page.fill('input[name="drug_name"]', "Metformin")
        page.fill('input[name="dosage"]', "500mg")
        page.fill('input[name="frequency"]', "Twice daily")
        page.fill('input[name="timing"]', "After meals")
        page.fill('input[name="purpose"]', "Blood sugar control")
        page.fill('input[name="prescribed_date"]', "2025-01-01")
        page.fill('input[name="doctor_name"]', "Dr. Ramesh Kumar")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        check("Medication saved -> /medications", "/medications" in page.url, page.url)
        page.screenshot(path="ss_medications.png", full_page=True)

        # ── Add lab result ────────────────────────────────────────────────
        print("\n=== Add Lab Result ===")
        page.goto(BASE + "/labs/add")
        page.wait_for_load_state("networkidle")
        check("Lab form loads", page.locator("form").count() > 0, page.url)

        page.fill('input[name="test_name"]', "HbA1c")
        page.fill('input[name="test_value"]', "7.2")
        page.fill('input[name="unit"]', "%")
        page.fill('input[name="reference_range"]', "4.0-5.6")
        page.fill('input[name="test_date"]', "2025-05-01")
        page.fill('input[name="lab_name"]', "Apollo Diagnostics")
        # mark as abnormal
        cb = page.locator('input[name="is_abnormal"]')
        if cb.count() > 0:
            cb.check()
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        check("Lab result saved -> /labs", "/labs" in page.url, page.url)
        page.screenshot(path="ss_labs.png", full_page=True)

        # ── Add care event ────────────────────────────────────────────────
        print("\n=== Add Care Event ===")
        page.goto(BASE + "/events/add")
        page.wait_for_load_state("networkidle")
        check("Event form loads", page.locator("form").count() > 0, page.url)

        page.select_option('select[name="event_type"]', "symptom_reported")
        page.select_option('select[name="severity"]', "moderate")
        page.fill('textarea[name="event_description"]', "Mild headache in the evening, resolved after rest")
        page.fill('input[name="reported_by"]', "Srikanth")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        check("Event saved -> /timeline", "/timeline" in page.url, page.url)
        page.screenshot(path="ss_timeline.png", full_page=True)

        # ── Add appointment ───────────────────────────────────────────────
        print("\n=== Add Appointment ===")
        page.goto(BASE + "/appointments/add")
        page.wait_for_load_state("networkidle")
        check("Appointment form loads", page.locator("form").count() > 0, page.url)

        page.fill('input[name="appointment_date"]', "2025-06-15T10:00")
        page.select_option('select[name="appointment_type"]', "Follow-up")
        page.fill('input[name="doctor_name"]', "Dr. Ramesh Kumar")
        page.fill('input[name="hospital"]', "Apollo Hospital Hyderabad")
        page.fill('textarea[name="notes"]', "Bring last 3 months HbA1c reports")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        check("Appointment saved -> /appointments or /dashboard",
              "/appointments" in page.url or "/dashboard" in page.url, page.url)
        page.screenshot(path="ss_appointments.png", full_page=True)

        # ── Final dashboard ───────────────────────────────────────────────
        print("\n=== Final Dashboard ===")
        page.goto(BASE + "/dashboard")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="ss_final_dashboard.png", full_page=True)
        print("  [screenshot] ss_final_dashboard.png")

        browser.close()

    print("\n" + "=" * 50)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        print("Failed:")
        for label, ok in results:
            if not ok:
                print(f"  - {label}")
    return passed == total

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
