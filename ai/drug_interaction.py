import json
from ai.claude_client import call_claude
from database.queries import insert_alert

SYSTEM = "You are a clinical pharmacist assistant helping a non-medical family caregiver understand medication safety."

PROMPT_TEMPLATE = """Analyze the following active medication list for potential drug-drug interactions, contraindications, and safety concerns.

PATIENT PROFILE:
- Age: {age}
- Conditions: {conditions}
- Recent Lab Values: {labs}

ACTIVE MEDICATIONS:
{medication_list}

For each potential interaction found, provide:
{{
  "interactions": [
    {{
      "drug_a": "name",
      "drug_b": "name",
      "severity": "mild|moderate|severe",
      "description": "What happens when these are taken together",
      "mechanism": "Why this interaction occurs (simple terms)",
      "recommendation": "What Meera should discuss with the doctor",
      "requires_immediate_action": true/false
    }}
  ],
  "overall_safety_assessment": "summary in 2-3 plain sentences",
  "suggested_monitoring": ["what to watch for"]
}}

IMPORTANT RULES:
- Only flag interactions clinically significant for THIS patient's profile
- DO NOT flag theoretical interactions that don't apply given the patient's lab values
- Use plain language — Meera is not a doctor
- Always recommend discussing with the prescribing doctor — never say "stop taking"
- Include: "This is an AI-generated analysis. Always confirm with your doctor before making any changes to medication."
Return ONLY valid JSON."""

async def check_drug_interactions(patient: dict, medications: list) -> str:
    if len(medications) < 2:
        return "✅ Only one medication on file — no interaction check needed."

    from database.queries import get_recent_lab_reports
    labs = get_recent_lab_reports(patient["id"], days=60)
    lab_summary = ", ".join(f"{l['test_name']}: {l['test_value']} {l.get('unit','')}" for l in labs[:5]) or "No recent labs"

    from datetime import date
    dob = patient.get("date_of_birth")
    age = (date.today() - date.fromisoformat(dob)).days // 365 if dob else "Unknown"

    med_list = "\n".join(
        f"- {m['drug_name']} {m['dosage']} {m['frequency']} "
        f"(prescribed by {m.get('doctors', {}).get('name', 'Unknown') if m.get('doctors') else 'Unknown'} "
        f"for {m.get('purpose', 'N/A')})"
        for m in medications
    )

    prompt = PROMPT_TEMPLATE.format(
        age=age,
        conditions=", ".join(patient.get("known_conditions") or []),
        labs=lab_summary,
        medication_list=med_list,
    )

    raw = await call_claude(prompt, system=SYSTEM)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw.strip())
    except Exception:
        return raw

    interactions = data.get("interactions", [])

    if not interactions:
        return (
            "✅ No significant drug interactions found for Dad's current medications.\n\n"
            f"Overall: {data.get('overall_safety_assessment', '')}\n\n"
            "_This is an AI-generated analysis. Always confirm with your doctor._"
        )

    lines = ["⚠️ *DRUG INTERACTION ANALYSIS*\n"]
    for ix in interactions:
        severity_icon = "🔴" if ix["severity"] == "severe" else "🟡" if ix["severity"] == "moderate" else "🟢"
        lines.append(
            f"{severity_icon} *{ix['drug_a']} + {ix['drug_b']}* ({ix['severity'].upper()})\n"
            f"{ix['description']}\n"
            f"What to do: {ix['recommendation']}"
        )

    lines.append(f"\n📊 Overall: {data.get('overall_safety_assessment', '')}")
    lines.append("\n_This is an AI-generated analysis. Always confirm with your doctor before making any changes to medication._")

    for ix in interactions:
        insert_alert(patient["id"], {
            "alert_type": "drug_interaction",
            "severity": ix["severity"],
            "title": f"Drug Interaction: {ix['drug_a']} + {ix['drug_b']}",
            "description": ix["description"],
            "recommendation": ix["recommendation"],
        })

    return "\n\n".join(lines)
