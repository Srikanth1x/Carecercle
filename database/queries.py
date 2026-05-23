import random
from datetime import datetime, timedelta, timezone
from database.supabase_client import get_client
from abdm.consent import log_access


def get_patient_for_telegram_user(telegram_chat_id: str) -> dict | None:
    """Resolve a Telegram chat_id to a patient dict. Returns None if not linked."""
    from database.auth_queries import get_user_profile, get_patient_by_user_id
    profile = get_user_profile(str(telegram_chat_id))
    if not profile:
        return None
    return get_patient_by_user_id(profile["user_id"])


def create_patient(user_id: str, data: dict) -> dict:
    db = get_client()
    name = data.get("full_name", "patient")
    first = name.split()[0].lower()
    fallback_abha_id = str(random.randint(10000000000000, 99999999999999))
    fallback_abha_address = f"{first}.{random.randint(1000, 9999)}@carecircle"
    record = {
        "user_id": user_id,
        "abha_id": data.get("abha_id") or fallback_abha_id,
        "abha_address": data.get("abha_address") or fallback_abha_address,
        **{k: v for k, v in data.items() if k not in ("abha_id", "abha_address")},
    }
    result = db.table("patients").insert(record).execute()
    if not result.data:
        raise RuntimeError("Failed to create patient")
    return result.data[0]


def get_or_create_doctor(name: str, specialty: str = None, hospital: str = None) -> dict | None:
    if not name or not name.strip():
        return None
    # Strip leading "Dr." so templates that add "Dr." don't double it
    clean = name.strip()
    for prefix in ("Dr. ", "Dr."):
        if clean.startswith(prefix):
            clean = clean[len(prefix):].strip()
            break
    doctor = get_doctor_by_name(clean)
    if doctor:
        return doctor
    db = get_client()
    result = db.table("doctors").insert({
        "name": clean,
        "specialty": specialty,
        "hospital": hospital,
    }).execute()
    return result.data[0] if result.data else None


def get_active_medications(patient_id: str) -> list:
    db = get_client()
    result = db.table("medications").select("*, doctors(name, specialty, phone)") \
        .eq("patient_id", patient_id).eq("status", "active").execute()
    return result.data


def get_recent_lab_reports(patient_id: str, days: int = 90) -> list:
    db = get_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    result = db.table("lab_reports").select("*") \
        .eq("patient_id", patient_id).gte("test_date", since) \
        .order("test_date", desc=True).execute()
    return result.data


def get_upcoming_appointments(patient_id: str) -> list:
    db = get_client()
    now = datetime.now(timezone.utc).isoformat()
    result = db.table("appointments").select("*, doctors(name, specialty, phone, hospital)") \
        .eq("patient_id", patient_id).eq("status", "scheduled") \
        .gte("appointment_date", now).order("appointment_date").execute()
    return result.data


def get_recent_care_events(patient_id: str, hours: int = 24) -> list:
    db = get_client()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    result = db.table("care_events").select("*") \
        .eq("patient_id", patient_id).gte("event_timestamp", since) \
        .order("event_timestamp", desc=True).execute()
    return result.data


def get_active_alerts(patient_id: str) -> list:
    db = get_client()
    result = db.table("alerts").select("*") \
        .eq("patient_id", patient_id).eq("status", "active") \
        .order("created_at", desc=True).execute()
    return result.data


def get_alert_by_id(alert_id: str) -> dict | None:
    db = get_client()
    result = db.table("alerts").select("id, patient_id, status").eq("id", alert_id).execute()
    return result.data[0] if result.data else None


def insert_medication(patient_id: str, doctor_id: str, data: dict) -> dict:
    db = get_client()
    existing = db.table("medications").select("id, dosage, status") \
        .eq("patient_id", patient_id).eq("drug_name", data["drug_name"]).eq("status", "active").execute()

    if existing.data:
        old = existing.data[0]
        if old["dosage"] == data.get("dosage"):
            return {"action": "duplicate", "id": old["id"]}
        db.table("medications").update({"status": "superseded"}).eq("id", old["id"]).execute()

    record = {**data, "patient_id": patient_id, "doctor_id": doctor_id}
    result = db.table("medications").insert(record).execute()
    if not result.data:
        raise RuntimeError("Failed to insert medication — Supabase returned no data")
    log_access(patient_id, "system", "caregiver_app", "write", ["medications"])
    return {"action": "inserted", "data": result.data[0]}


def insert_lab_report(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("lab_reports").insert({"patient_id": patient_id, **data}).execute()
    if not result.data:
        raise RuntimeError("Failed to insert lab report — Supabase returned no data")
    log_access(patient_id, "system", "caregiver_app", "write", ["lab_reports"])
    return result.data[0]


def insert_care_event(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("care_events").insert({"patient_id": patient_id, **data}).execute()
    if not result.data:
        raise RuntimeError("Failed to insert care event — Supabase returned no data")
    return result.data[0]


def insert_appointment(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("appointments").insert({"patient_id": patient_id, **data}).execute()
    if not result.data:
        raise RuntimeError("Failed to insert appointment — Supabase returned no data")
    return result.data[0]


def insert_alert(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("alerts").insert({"patient_id": patient_id, **data}).execute()
    if not result.data:
        raise RuntimeError("Failed to insert alert — Supabase returned no data")
    return result.data[0]


def acknowledge_alert(alert_id: str) -> None:
    db = get_client()
    db.table("alerts").update({
        "status": "acknowledged",
        "acknowledged_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", alert_id).execute()


def insert_daily_briefing(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("daily_briefings").insert({"patient_id": patient_id, **data}).execute()
    if not result.data:
        raise RuntimeError("Failed to insert daily briefing — Supabase returned no data")
    return result.data[0]


def get_doctor_by_name(name: str) -> dict | None:
    db = get_client()
    result = db.table("doctors").select("*").ilike("name", f"%{name}%").execute()
    return result.data[0] if result.data else None


def create_share_link(patient_id: str) -> dict:
    from abdm.sharing import generate_share_token
    db = get_client()
    token = generate_share_token()
    result = db.table("share_links").insert({
        "patient_id": patient_id,
        "token": token,
    }).execute()
    if not result.data:
        raise RuntimeError("Failed to create share link")
    return result.data[0]


def get_share_link_by_token(token: str) -> dict | None:
    from datetime import datetime, timezone
    db = get_client()
    now = datetime.now(timezone.utc).isoformat()
    result = db.table("share_links").select("*") \
        .eq("token", token).gte("expires_at", now).execute()
    return result.data[0] if result.data else None
