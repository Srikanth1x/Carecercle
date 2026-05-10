from ai.claude_client import call_claude
from database.queries import get_upcoming_appointments, get_recent_lab_reports

SYSTEM = "You are a healthcare gap detector helping a family caregiver stay on top of necessary medical tasks."

PROMPT_TEMPLATE = """Identify missing tasks or preparation gaps for an upcoming medical appointment.

UPCOMING APPOINTMENTS:
{appointments}

RECENT LAB TESTS (last 90 days):
{labs}

PATIENT CONDITIONS: {conditions}

Identify:
1. Any prerequisites listed for appointments that are not yet done (based on recent labs)
2. Any lab tests that are overdue given the patient's conditions (e.g., HbA1c every 3 months for diabetics)
3. Any medication refills that may be needed soon

Return a plain-language list of action items for Meera. Be brief and actionable.
Each item should start with a bullet point."""

async def detect_gaps(patient: dict) -> list[str]:
    pid = patient["id"]
    appts = get_upcoming_appointments(pid)
    labs = get_recent_lab_reports(pid, days=90)

    if not appts:
        return []

    appt_summary = "\n".join(
        f"- {a['appointment_date'][:10]} with Dr. {a.get('doctors', {}).get('name', '?')}, "
        f"prerequisites: {', '.join(a.get('prerequisites') or ['none'])}"
        for a in appts
    )
    lab_summary = "\n".join(
        f"- {l['test_name']}: {l['test_date']}"
        for l in labs
    ) or "No recent labs"

    prompt = PROMPT_TEMPLATE.format(
        appointments=appt_summary,
        labs=lab_summary,
        conditions=", ".join(patient.get("known_conditions") or []),
    )

    result = await call_claude(prompt, system=SYSTEM)
    return [line.strip() for line in result.strip().splitlines() if line.strip().startswith("•") or line.strip().startswith("-")]
