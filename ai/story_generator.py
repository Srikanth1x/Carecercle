from ai.claude_client import call_claude
from database.queries import (
    get_active_medications, get_recent_lab_reports,
    get_active_alerts, get_upcoming_appointments,
)

STORY_PROMPT = """\
You are writing a short, warm "care snapshot" for a caregiver dashboard.

The person reading this is a busy professional — checking this at 7 AM or 10 PM after a long day. \
They are caring for a parent from a distance. They want one paragraph that tells them: \
who this person is, what they're managing, what the current picture looks like, and what needs attention.

Write in second person ("Your father..." or "Your mother..."). Be warm, human, specific. \
No bullet points. No medical jargon. No fluff. 120-160 words max.

PATIENT: {name}, {age} years old
CONDITIONS: {conditions}
CURRENT MEDICATIONS ({med_count}): {med_names}
DOCTORS: {doctors}
RECENT LAB FLAGS: {lab_flags}
UPCOMING: {upcoming}
ACTIVE ALERTS: {alerts}

Write the snapshot now. Start with "Your {relation}..." — \
infer the relation from context or just use "Your parent".
"""


async def generate_care_story(patient: dict) -> str:
    pid = patient["id"]
    name = patient.get("full_name", "your parent")

    from datetime import date
    dob = patient.get("date_of_birth") or ""
    try:
        birth_year = int(dob[:4])
        age = date.today().year - birth_year
    except Exception:
        age = "unknown"

    conditions = ", ".join(patient.get("known_conditions") or []) or "conditions not listed"
    meds = get_active_medications(pid)
    med_names = ", ".join(m["drug_name"] for m in meds[:6])
    if len(meds) > 6:
        med_names += f" and {len(meds) - 6} more"

    # Collect unique doctors from meds
    doctors = list({m["doctors"]["name"] for m in meds if m.get("doctors")})
    doctor_str = ", ".join(f"Dr. {d}" for d in doctors[:4]) or "not yet linked"

    labs = get_recent_lab_reports(pid, days=60)
    abnormal = [l for l in labs if l.get("is_abnormal")]
    if abnormal:
        lab_flags = ", ".join(
            f"{l['test_name']} ({l['test_value']} {l.get('unit', '')})"
            for l in abnormal[:4]
        )
    else:
        lab_flags = "all recent values within range" if labs else "no recent labs on file"

    appts = get_upcoming_appointments(pid)
    if appts:
        next_appt = appts[0]
        dr = (next_appt.get("doctors") or {}).get("name", "doctor")
        upcoming = f"Appointment with Dr. {dr} on {next_appt['appointment_date'][:10]}"
    else:
        upcoming = "no upcoming appointments"

    active_alerts = get_active_alerts(pid)
    alert_str = ", ".join(a["title"] for a in active_alerts[:3]) or "none"

    prompt = STORY_PROMPT.format(
        name=name,
        age=age,
        conditions=conditions,
        med_count=len(meds),
        med_names=med_names or "none on file",
        doctors=doctor_str,
        lab_flags=lab_flags,
        upcoming=upcoming,
        alerts=alert_str,
    )

    system = "You are a care assistant. Write warm, human, concise care snapshots for family caregivers."
    return await call_claude(prompt, system=system)
