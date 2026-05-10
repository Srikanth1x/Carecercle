from database.queries import get_patient_by_abha, get_active_medications, get_recent_lab_reports
from config.settings import PATIENT_ABHA_ID

_cached_crisis_card: str = None

def _build_crisis_card(patient: dict, meds: list) -> str:
    med_lines = "\n".join(
        f"{i}. {m['drug_name']} {m['dosage']} — {m['frequency']}"
        for i, m in enumerate(meds, 1)
    )
    conditions = ", ".join(patient.get("known_conditions") or [])

    return (
        f"🚨 *EMERGENCY INFO — {patient['full_name']}*\n\n"
        f"🏥 *NEAREST HOSPITAL:* City Heart Hospital, Lucknow\n\n"
        f"📞 *EMERGENCY CONTACTS:*\n"
        f"• Dr. Anil Kapoor (Cardiologist): +91-9800000010\n"
        f"• Dr. Priya Mehta (Endocrinologist): +91-9800000011\n"
        f"• Dr. Suresh Verma (GP): +91-9800000012\n"
        f"• Ambulance: 108\n\n"
        f"💊 *CURRENT MEDICATIONS:*\n{med_lines}\n\n"
        f"⚕️ *KNOWN CONDITIONS:* {conditions}\n"
        f"🩸 *BLOOD GROUP:* {patient.get('blood_group', 'N/A')}\n\n"
        f"⏱️ Share this with the ER doctor immediately."
    )

def get_crisis_card() -> str:
    global _cached_crisis_card
    if _cached_crisis_card:
        return _cached_crisis_card
    try:
        patient = get_patient_by_abha(PATIENT_ABHA_ID)
        meds = get_active_medications(patient["id"])
        _cached_crisis_card = _build_crisis_card(patient, meds)
        return _cached_crisis_card
    except Exception:
        return (
            "🚨 EMERGENCY\n"
            "Ambulance: 108\n"
            "City Heart Hospital, Lucknow\n"
            "ABHA ID: 12345678901234"
        )

def invalidate_cache():
    global _cached_crisis_card
    _cached_crisis_card = None
