import httpx
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from config.settings import SUPABASE_URL, SUPABASE_KEY

SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1"

def _headers():
    return {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}

async def supabase_login(email: str, password: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{SUPABASE_AUTH_URL}/token?grant_type=password",
            json={"email": email, "password": password},
            headers=_headers()
        )
    return r.json() if r.status_code == 200 else None

async def supabase_register(email: str, password: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{SUPABASE_AUTH_URL}/signup",
            json={"email": email, "password": password},
            headers=_headers()
        )
    return r.json()

async def get_user_from_token(token: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SUPABASE_AUTH_URL}/user",
            headers={**_headers(), "Authorization": f"Bearer {token}"}
        )
    return r.json() if r.status_code == 200 else None

def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="cc_token", value=token,
        httponly=True, max_age=60 * 60 * 24 * 7, samesite="lax"
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
