from database.supabase_client import get_client

def get_user_profile(telegram_chat_id: str) -> dict | None:
    db = get_client()
    result = db.table("user_profiles") \
        .select("user_id") \
        .eq("telegram_chat_id", str(telegram_chat_id)) \
        .execute()
    return result.data[0] if result.data else None

def set_telegram_chat_id(user_id: str, telegram_chat_id: str) -> None:
    db = get_client()
    db.table("user_profiles").upsert({
        "user_id": user_id,
        "telegram_chat_id": str(telegram_chat_id)
    }).execute()

def get_patient_by_user_id(user_id: str) -> dict | None:
    """Returns the first patient for a user (kept for backward compatibility)."""
    db = get_client()
    result = db.table("patients").select("*") \
        .eq("user_id", user_id).order("created_at").execute()
    return result.data[0] if result.data else None

def get_patients_by_user_id(user_id: str) -> list:
    """Returns all patients for a user, ordered by creation date."""
    db = get_client()
    result = db.table("patients").select("*") \
        .eq("user_id", user_id).order("created_at").execute()
    return result.data or []

def get_all_linked_users() -> list:
    db = get_client()
    result = db.table("user_profiles") \
        .select("user_id, telegram_chat_id") \
        .not_.is_("telegram_chat_id", "null") \
        .execute()
    return result.data or []
