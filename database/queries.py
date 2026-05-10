from datetime import datetime, timedelta
from database.supabase_client import get_client
from abdm.consent import log_access

def get_patient_for_telegram_user(telegram_chat_id: str) -> dict | None:
    """Resolve a Telegram chat_id to a patient dict. Returns None if not linked."""
    from database.auth_queries import get_user_profile, get_patient_by_user_id
    profile = get_user_profile(str(telegram_chat_id))
    if not profile:
        return None
    return get_patient_by_user_id(profile["user_id"])

def get_active_medications(patient_id: str) -> list:
    db = get_client()
    result = db.table("medications").select("*, doctors(name, specialty, phone)") \
        .eq("patient_id", patient_id).eq("status", "active").execute()
    log_access(patient_id, "system", "caregiver_app", "view", ["medications"])
    return result.data

def get_recent_lab_reports(patient_id: str, days: int = 90) -> list:
    db = get_client()
    since = (datetime.now() - timedelta(days=days)).date().isoformat()
    result = db.table("lab_reports").select("*") \
        .eq("patient_id", patient_id).gte("test_date", since) \
        .order("test_date", desc=True).execute()
    log_access(patient_id, "system", "caregiver_app", "view", ["lab_reports"])
    return result.data

def get_upcoming_appointments(patient_id: str) -> list:
    db = get_client()
    now = datetime.now().isoformat()
    result = db.table("appointments").select("*, doctors(name, specialty, phone, hospital)") \
        .eq("patient_id", patient_id).eq("status", "scheduled") \
        .gte("appointment_date", now).order("appointment_date").execute()
    return result.data

def get_recent_care_events(patient_id: str, hours: int = 24) -> list:
    db = get_client()
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
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
    log_access(patient_id, "system", "caregiver_app", "write", ["medications"])
    return {"action": "inserted", "data": result.data[0]}

def insert_lab_report(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("lab_reports").insert({"patient_id": patient_id, **data}).execute()
    log_access(patient_id, "system", "caregiver_app", "write", ["lab_reports"])
    return result.data[0]

def insert_care_event(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("care_events").insert({"patient_id": patient_id, **data}).execute()
    return result.data[0]

def insert_alert(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("alerts").insert({"patient_id": patient_id, **data}).execute()
    return result.data[0]

def acknowledge_alert(alert_id: str) -> None:
    db = get_client()
    db.table("alerts").update({
        "status": "acknowledged",
        "acknowledged_at": datetime.now().isoformat()
    }).eq("id", alert_id).execute()

def insert_daily_briefing(patient_id: str, data: dict) -> dict:
    db = get_client()
    result = db.table("daily_briefings").insert({"patient_id": patient_id, **data}).execute()
    return result.data[0]

def get_doctor_by_name(name: str) -> dict | None:
    db = get_client()
    result = db.table("doctors").select("*").ilike("name", f"%{name}%").execute()
    return result.data[0] if result.data else None
