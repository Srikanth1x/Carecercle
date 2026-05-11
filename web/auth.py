import logging
import httpx
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from config.settings import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1"

def _headers():
    return {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}

async def supabase_login(email: str, password: str) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{SUPABASE_AUTH_URL}/token?grant_type=password",
                json={"email": email, "password": password},
                headers=_headers(),
                timeout=10.0,
            )
    except httpx.TimeoutException:
        raise ValueError("Login service timed out. Please try again.")
    except httpx.RequestError as e:
        logger.error("Supabase login network error: %s", e)
        raise ValueError("Could not reach login service. Please try again.")

    if r.status_code == 200:
        return r.json()

    try:
        body = r.json()
        msg = body.get("error_description") or body.get("msg") or body.get("message") or "Invalid email or password."
    except Exception:
        msg = "Invalid email or password."
    raise ValueError(msg)

async def supabase_register(email: str, password: str) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{SUPABASE_AUTH_URL}/signup",
                json={"email": email, "password": password},
                headers=_headers(),
                timeout=10.0,
            )
        return r.json()
    except httpx.TimeoutException:
        raise ValueError("Registration service timed out. Please try again.")
    except httpx.RequestError as e:
        logger.error("Supabase register network error: %s", e)
        raise ValueError("Could not reach registration service. Please try again.")

async def get_user_from_token(token: str) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{SUPABASE_AUTH_URL}/user",
                headers={**_headers(), "Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
    except httpx.RequestError as e:
        logger.error("Supabase token validation error: %s", e)
        return None

    if r.status_code != 200:
        return None
    user = r.json()
    if not isinstance(user, dict) or "id" not in user:
        return None
    return user

def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="cc_token", value=token,
        httponly=True, secure=True, max_age=60 * 60 * 24 * 7, samesite="lax"
    )

def clear_session_cookie(response: Response) -> None:
    response.delete_cookie("cc_token")

async def get_current_user(request: Request) -> dict | None:
    token = request.cookies.get("cc_token")
    if not token:
        return None
    return await get_user_from_token(token)

async def require_user(request: Request) -> dict:
    user = await get_current_user(request)
    if not user:
        raise RedirectException("/login")
    return user

class RedirectException(Exception):
    def __init__(self, url: str):
        self.url = url
