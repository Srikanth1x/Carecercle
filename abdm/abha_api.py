"""
ABDM M1 — ABHA Verification via Mobile OTP
Sandbox base URL: https://sandbox.abdm.gov.in/api/v3
Production base URL: https://healthidsbx.abdm.gov.in/api/v3 (after go-live)

Flow:
  1. generate_mobile_otp(mobile)  → txn_id
  2. verify_mobile_otp(txn_id, otp) → auth token + ABHA profile
  3. get_abha_profile(token)        → full ABHA card details
"""

import httpx
import logging
from config.settings import ABDM_CLIENT_ID, ABDM_CLIENT_SECRET, ABDM_BASE_URL

logger = logging.getLogger(__name__)

TIMEOUT = 15.0

# ---------- Auth ----------

async def _get_access_token() -> str:
    url = f"{ABDM_BASE_URL}/gateway/sessions"
    payload = {
        "clientId": ABDM_CLIENT_ID,
        "clientSecret": ABDM_CLIENT_SECRET,
        "grantType": "client_credentials",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()["accessToken"]


# ---------- M1: ABHA by Mobile OTP ----------

async def generate_mobile_otp(mobile: str) -> dict:
    """Send OTP to mobile number. Returns {"txnId": "..."}"""
    token = await _get_access_token()
    url = f"{ABDM_BASE_URL}/abha/api/v3/enrollment/request/otp"
    payload = {
        "scope": ["abha-login", "mobile-verify"],
        "loginHint": "mobile",
        "loginId": mobile,
        "otpSystem": "abdm",
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def verify_mobile_otp(txn_id: str, otp: str) -> dict:
    """Verify OTP. Returns {"token": "...", "expiresIn": 1800, "refreshToken": "..."}"""
    token = await _get_access_token()
    url = f"{ABDM_BASE_URL}/abha/api/v3/enrollment/auth/byAbdm"
    payload = {
        "scope": ["abha-login", "mobile-verify"],
        "authData": {
            "authMethods": ["otp"],
            "otp": {"txnId": txn_id, "otpValue": otp},
        },
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def get_abha_profile(user_token: str) -> dict:
    """Fetch full ABHA card using the user-level token from verify_mobile_otp."""
    token = await _get_access_token()
    url = f"{ABDM_BASE_URL}/abha/api/v3/profile/account"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Token": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()


# ---------- High-level helper ----------

async def verify_abha_by_mobile(mobile: str, otp: str, txn_id: str) -> dict:
    """
    Step 2 of the flow (OTP already sent via generate_mobile_otp).
    Returns normalised profile dict ready to store in DB.
    Raises httpx.HTTPStatusError on ABDM API failures.
    """
    auth = await verify_mobile_otp(txn_id, otp)
    user_token = auth.get("token") or auth.get("accessToken")
    profile = await get_abha_profile(user_token)

    abha_number = profile.get("ABHANumber") or profile.get("healthIdNumber", "")
    abha_address = profile.get("preferredAbhaAddress") or profile.get("healthId", "")

    return {
        "abha_number": abha_number,
        "abha_address": abha_address,
        "name_on_abha": profile.get("name", ""),
        "gender": profile.get("gender", ""),
        "year_of_birth": str(profile.get("yearOfBirth", "")),
        "mobile_last4": mobile[-4:],
        "raw_response": profile,
    }
