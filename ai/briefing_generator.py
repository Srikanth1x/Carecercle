from datetime import date, datetime, timezone, timedelta
from ai.claude_client import call_claude
from database.queries import (
    get_active_medications, get_recent_lab_reports,
    get_active_alerts, get_recent_care_events,
    get_upcoming_appointments, insert_daily_briefing
)

PROMPT_TEMPLATE = """You are sending the morning health briefing to {caregiver_name} about {patient_name}.

{caregiver_name} is a busy professional. It's 7 AM. They need to know in under 60 seconds: \
is their parent okay, is anything urgent, and what do they need to do today?

DATA:
Active Medications: {medications}
Last 24h Events: {care_events}
Recent Lab Values: {recent_labs}
Active Alerts: {alerts}
Upcoming Appointments: {appointments}
Last caregiver update: {last_caregiver_update}

FORMAT — use exactly this structure:
*Good morning, {caregiver_name}* — here's today on {patient_name}.

[One sentence: overall status — ✅ All clear / ⚠️ Needs attention / 🚨 Urgent]

[2-3 sentences: what happened in the last 24 hours, or what's notable. Be specific and human.]

[If alerts or upcoming appointments, one line each starting with 📌 or ⚠️]

[End with one action item if needed, or "Nothing urgent — carry on." if all is fine]

Keep under 180 words. No medical jargon. Warm, direct, specific."""

async def generate_briefing(patient: dict) -> str:
    patient_id = patient["id"]
    patient_name = patient.get("full_name", "the patient")
    caregiver_name = patient.get("emergency_contact_name", "Caregiver")

    system = f"You are {caregiver_name}'s care assistant. Generate a concise daily health briefing about {patient_name}."

    today = date.today()
    meds = get_active_medications(patient_id)
    labs = get_recent_lab_reports(patient_id, days=30)
    alerts = get_active_alerts(patient_id)
    events = get_recent_care_events(patient_id, hours=24)
    appts = get_upcoming_appointments(patient_id)

    med_summary = f"{len(meds)} active medications"
    lab_summary = "; ".join(
        f"{l['test_name']}: {l['test_value']} {l.get('unit','')} ({'HIGH' if l['is_abnormal'] else 'OK'})"
        for l in labs[:4]
    ) or "No recent labs"
    alert_summary = "; ".join(a["title"] for a in alerts[:3]) or "None"
    event_summary = "; ".join(e["event_description"] for e in events[:5]) or "No updates in last 24h"
    appt_summary = "; ".join(
        f"Dr. {a.get('doctors',{}).get('name','?')} on {a['appointment_date'][:10]}"
        for a in appts[:2]
    ) or "None upcoming"

    last_event_time = events[0]["event_timestamp"] if events else None
    if last_event_time:
        delta = datetime.now(timezone.utc) - datetime.fromisoformat(last_event_time[:19]).replace(tzinfo=timezone.utc)
        last_update = f"{int(delta.total_seconds() / 3600)} hours ago"
    else:
        last_update = "More than 24 hours ago"

    prompt = PROMPT_TEMPLATE.format(
        caregiver_name=caregiver_name,
        patient_name=patient_name,
        medications=med_summary,
        care_events=event_summary,
        recent_labs=lab_summary,
        alerts=alert_summary,
        appointments=appt_summary,
        last_caregiver_update=last_update,
    )

    text = await call_claude(prompt, system=system)

    insert_daily_briefing(patient_id, {
        "briefing_date": today.isoformat(),
        "briefing_text": text,
        "data_sources_used": ["medications", "care_events", "lab_reports", "alerts", "appointments"],
        "sent_at": datetime.now(timezone.utc).isoformat(),
    })

    return text
