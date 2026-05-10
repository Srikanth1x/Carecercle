from ai.claude_client import call_claude

SYSTEM = "You are a medication adherence analyst helping a family caregiver detect deviations from prescribed medication schedules."

PROMPT_TEMPLATE = """Compare prescribed medications vs actual reported behavior and identify deviations.

PRESCRIBED MEDICATIONS:
{prescribed}

RECENT CARE EVENTS (last 48h):
{events}

Identify any deviations such as:
- Wrong timing (e.g., prescribed after meals but taken before)
- Missed doses
- Wrong dose
- Medications taken with food when they shouldn't be (or vice versa)

Return a brief plain-language report. If everything looks fine, say so.
Never say "stop taking" — always recommend discussing with the doctor."""

async def detect_deviations(patient: dict, medications: list, care_events: list) -> str:
    if not medications or not care_events:
        return ""

    prescribed = "\n".join(
        f"- {m['drug_name']} {m['dosage']}: {m['frequency']}, {m.get('timing', 'no timing specified')}"
        for m in medications
    )
    events = "\n".join(
        f"- {e['event_type']}: {e['event_description']} (at {e['event_timestamp'][:16]})"
        for e in care_events
    )

    prompt = PROMPT_TEMPLATE.format(prescribed=prescribed, events=events)
    return await call_claude(prompt, system=SYSTEM)
