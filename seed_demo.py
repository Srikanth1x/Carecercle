"""
Demo seed script — run once to populate realistic presentation data.
Run from repo root: python seed_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from database.supabase_client import get_client
from database.auth_queries import get_patient_by_user_id
from database.queries import insert_care_event, insert_appointment, insert_alert, get_or_create_doctor
from datetime import datetime, date, timedelta, timezone

USER_EMAIL = "srikanthkarkampally01@gmail.com"
USER_PASS  = "123456"

# ── Resolve patient via service client ───────────────────────────
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

db_anon = create_client(SUPABASE_URL, SUPABASE_KEY)
auth = db_anon.auth.sign_in_with_password({"email": USER_EMAIL, "password": USER_PASS})
user_id = auth.user.id
token = auth.session.access_token
print(f"Signed in as user_id: {user_id}")

# Use an authed client to bypass RLS
db_authed = create_client(SUPABASE_URL, SUPABASE_KEY)
db_authed.postgrest.auth(token)

res = db_authed.table("patients").select("*").eq("user_id", user_id).execute()
if not res.data:
    print("No patient found — complete setup at getaayu.in first.")
    sys.exit(1)
patient = res.data[0]

# Patch get_client singleton to use authed client for inserts
import database.supabase_client as _sc
_sc._client = db_authed

pid = patient["id"]
print(f"Seeding data for patient: {patient['full_name']} ({pid})")

now = datetime.now(timezone.utc)
today = date.today()


# ── Appointments ─────────────────────────────────────────────────
appt_data = [
    {
        "doctor": "Venkata Lakshmi", "specialty": "Cardiology",
        "hospital": "Apollo Hospitals, Hyderabad",
        "days": 12, "type": "Follow-up",
        "notes": "Review echocardiogram results and adjust Diltiazem dose if needed.",
        "prerequisites": ["ECG", "2D Echo repeat"], "prereq_status": "pending",
    },
    {
        "doctor": "Annapurna", "specialty": "Endocrinology",
        "hospital": "KIMS Hospital, Secunderabad",
        "days": 22, "type": "Routine check",
        "notes": "HbA1c follow-up — target below 7.5%.",
        "prerequisites": ["Fasting Blood Sugar", "HbA1c"], "prereq_status": "pending",
    },
    {
        "doctor": "Srinivasa Rao", "specialty": "General Physician",
        "hospital": "Rao Clinic, Secunderabad",
        "days": 5, "type": "Routine check",
        "notes": "Monthly BP review and medication refill.",
        "prerequisites": [], "prereq_status": "done",
    },
]

for a in appt_data:
    doc = get_or_create_doctor(a["doctor"], specialty=a["specialty"], hospital=a["hospital"])
    appt_date = (today + timedelta(days=a["days"])).isoformat() + "T10:00:00"
    insert_appointment(pid, {
        "doctor_id": doc["id"] if doc else None,
        "appointment_date": appt_date,
        "appointment_type": a["type"],
        "hospital": a["hospital"],
        "notes": a["notes"],
        "prerequisites": a["prerequisites"] or None,
        "prerequisite_status": a["prereq_status"],
    })
    print(f"  ✓ Appointment: Dr. {a['doctor']} in {a['days']} days")


# ── Care Events (Timeline) ────────────────────────────────────────
events = [
    {
        "hours_ago": 2,
        "type": "observation",
        "desc": "Morning BP: 142/88 mmHg. Slightly elevated. Took Amlodipine 5mg after breakfast.",
        "severity": "attention", "by": "caregiver", "source": "caregiver_update",
    },
    {
        "hours_ago": 5,
        "type": "medication_taken",
        "desc": "All morning medications taken on time: Metformin 500mg, Levothyroxine 50mcg, Aspirin 75mg.",
        "severity": "normal", "by": "caregiver", "source": "caregiver_update",
    },
    {
        "hours_ago": 26,
        "type": "symptom",
        "desc": "Mild dizziness reported after lunch. Lasted ~20 minutes. Blood sugar checked: 168 mg/dL post-meal.",
        "severity": "attention", "by": "caregiver", "source": "caregiver_update",
    },
    {
        "hours_ago": 30,
        "type": "medication_taken",
        "desc": "All medications taken. Skipped evening walk due to rain.",
        "severity": "normal", "by": "caregiver", "source": "caregiver_update",
    },
    {
        "hours_ago": 50,
        "type": "observation",
        "desc": "Fasting blood sugar: 142 mg/dL. Slightly above target. Discussed dietary adjustments with patient.",
        "severity": "attention", "by": "caregiver", "source": "caregiver_update",
    },
    {
        "hours_ago": 72,
        "type": "doctor_visit",
        "desc": "GP visit completed. Dr. Srinivasa Rao reviewed BP log. Advised continuing current medications. Next visit in 5 days.",
        "severity": "normal", "by": "caregiver", "source": "manual",
    },
    {
        "hours_ago": 96,
        "type": "medication_taken",
        "desc": "Missed evening Metformin dose. Patient forgot — caregiver reminded via call.",
        "severity": "attention", "by": "caregiver", "source": "caregiver_update",
    },
]

for e in events:
    ts = (now - timedelta(hours=e["hours_ago"])).isoformat()
    insert_care_event(pid, {
        "event_type": e["type"],
        "event_description": e["desc"],
        "event_timestamp": ts,
        "severity": e["severity"],
        "reported_by": e["by"],
        "source_type": e["source"],
    })
    print(f"  ✓ Event ({e['hours_ago']}h ago): {e['type']}")


# ── Alerts ────────────────────────────────────────────────────────
alerts = [
    {
        "title": "HbA1c above target — 8.2%",
        "body": "Latest HbA1c is 8.2%, above the 7.5% target. Review with Dr. Annapurna at upcoming endocrinology appointment.",
        "severity": "warning", "category": "lab_result",
    },
    {
        "title": "ECG and Echo not yet scheduled",
        "body": "Cardiology follow-up with Dr. Venkata Lakshmi is in 12 days. ECG and repeat 2D Echo are listed as prerequisites and have not been booked.",
        "severity": "warning", "category": "appointment_prereq",
    },
    {
        "title": "Medication refill due in 5 days",
        "body": "Diltiazem 60mg and Clopidogrel 75mg supply estimated to run out in ~5 days. Contact Rao Clinic for prescription renewal.",
        "severity": "moderate", "category": "medication",
    },
]

for a in alerts:
    insert_alert(pid, {
        "title": a["title"],
        "body": a["body"],
        "severity": a["severity"],
        "category": a["category"],
        "status": "active",
    })
    print(f"  ✓ Alert: {a['title']}")

print("\nDemo data seeded successfully.")
