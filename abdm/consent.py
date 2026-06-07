import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def log_access(patient_id: str, requester_name: str, requester_role: str,
               access_type: str, records_accessed: list) -> None:
    try:
        from database.supabase_client import get_client
        db = get_client()
        db.table("consent_log").insert({
            "patient_id": patient_id,
            "requester_name": requester_name,
            "requester_role": requester_role,
            "access_type": access_type,
            "records_accessed": records_accessed,
            "consent_status": "granted",
            "granted_by": "caregiver",
            "granted_at": datetime.now(timezone.utc).isoformat(),
            "purpose": "Aayu caregiver access"
        }).execute()
    except Exception:
        logger.warning("Failed to write consent log for patient %s", patient_id)
