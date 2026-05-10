from datetime import date, datetime, timedelta
from ai.claude_client import call_claude
from database.queries import (
    get_active_medications, get_recent_lab_reports,
    get_active_alerts, get_recent_care_events,
    get_upcoming_appointments, insert_daily_briefing
)

SYSTEM = "You are Meera's care assistant. Generate a concise daily health briefing for her father."

PROMPT_TEMPLATE = """Generate a daily health briefing for Meera about her father Rajesh.

Meera is a busy professional who checks this at 7 AM. She needs to know:
1. Is Dad okay? (overall status)
2. Is anything urgent? (alerts requiring action)
3. What happened in the last 24 hours?
4. What's coming up? (appointments, due tasks)

DATA:
- Active Medications: {medications}
- Last 24h Care Events: {care_events}
- Recent Lab Values: {recent_labs}
- Active Alerts: {alerts}
- Upcoming Appointments: {appointments}
- Last Caregiver Update: {last_caregiver_update}

RULES:
- Keep it under 200 words
- Lead with the status: ✅ All Good / ⚠️ Needs Attention / 🚨 Urgent
- Use simple language, no medical jargon
- If caregiver hasn't sent an update in 24+ hours, note it
- Include a confidence score: how complete is today's picture? (based on data freshness)
- End with action items if any
- Be warm but factual"""

async def generate_briefing(patient_id: str) -> str:
    today = date.today()
    meds = get_active_medications(patient_id)
    labs = get_recent_lab_reports(patient_id, days=30)
    alerts = get_active_alerts(patient_id)
    events = get_recent_care_events(patient_id, hours=24)
    appts = get_upcoming_appointments(patient_id)

    med_summary = f"{len(meds)} active medications"
    lab_summary = "; ".join(f"{l['test_name']}: {l['test_value']} {l.get('unit','')} ({'HIGH' if l['is_abnormal'] else 'OK'})" for l in labs[:4]) or "No recent labs"
    alert_summary = "; ".join(a["title"] for a in alerts[:3]) or "None"
    event_summary = "; ".join(e["event_description"] for e in events[:5]) or "No updates in last 24h"
    appt_summary = "; ".join(f"Dr. {a.get('doctors',{}).get('name','?')} on {a['appointment_date'][:10]}" for a in appts[:2]) or "None upcoming"

    last_event_time = events[0]["event_timestamp"] if events else None
    if last_event_time:
        delta = datetime.now() - datetime.fromisoformat(last_event_time[:19])
        last_update = f"{int(delta.total_seconds() / 3600)} hours ago"
    else:
        last_update = "More than 24 hours ago"

    prompt = PROMPT_TEMPLATE.format(
        medications=med_summary,
        care_events=event_summary,
        recent_labs=lab_summary,
        alerts=alert_summary,
        appointments=appt_summary,
        last_caregiver_update=last_update,
    )

    text = await call_claude(prompt, system=SYSTEM)

    insert_daily_briefing(patient_id, {
        "briefing_date": today.isoformat(),
        "briefing_text": text,
        "data_sources_used": ["medications", "care_events", "lab_reports", "alerts", "appointments"],
        "sent_at": datetime.now().isoformat(),
    })

    return text
