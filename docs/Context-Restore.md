# Aayu — Quick Context Restore

> **For Claude:** Read this file first when starting a new session on Aayu.
> Then read Progress.md for detail on what's done and what's next.

---

## In One Paragraph
Aayu (formerly CareCircle) is a **live, fully deployed** AI-powered health care coordination app for Indian family caregivers. It's a **Telegram bot + FastAPI web dashboard** running on Vercel at **getaayu.in**. Caregivers log in, create a patient profile, and upload prescriptions/labs/documents — the AI classifies and extracts all data automatically. The app also sends a personalized **Care Snapshot** on the dashboard and a **7 AM daily Telegram briefing**. Data is stored in Supabase PostgreSQL. The app is built on India's national health infrastructure (ABDM, UHI, ABHA).

## Live URLs
- **Web app:** https://getaayu.in
- **GitHub:** https://github.com/Srikanth1x/Carecercle
- **Telegram bot:** @GetAayuBot

## Codebase Location
```
C:/Users/srika/OneDrive - EDM Council/Desktop/03.Work/carecircle/
```

## Current State (as of 2026-06-08)
- **Fully deployed and live on Vercel at getaayu.in**
- **Sprint 1 COMPLETE** — multi-patient support + share links
- **Sprint 2 SCAFFOLD COMPLETE** — ABHA OTP verification UI + API client + dashboard badge
  - Schema v5 ran clean in Supabase (abha_verified, abha_verified_at, abha_mobile_last4 cols + abha_verifications table)
  - ABDM sandbox application SUBMITTED — status: In Progress (awaiting NHA approval, 2-4 days)
  - OTP flow degrades gracefully when ABDM_CLIENT_ID not yet set (shows amber "sandbox pending" notice)
- AI stack: **Groq (llama-4-scout-17b-16e-instruct)** is PRIMARY — free, vision-capable
  - Gemini 2.0 Flash = fallback
  - Anthropic Claude = available but NOT used (paid)
- GoDaddy DNS: A record @ → 76.76.21.21, CNAME www → cname.vercel-dns.com
- Telegram webhook registered at https://getaayu.in/webhook

## Bot Commands (set in BotFather for @GetAayuBot)
```
start - Welcome and setup guide
help - Show all commands
connect - Link your Aayu web account
disconnect - Unlink this Telegram account
summary - Today's care snapshot
briefing - Full daily health briefing
check - Quick status check
meds - Current medications
labs - Recent lab values
sos - Emergency crisis card
addappointment - Schedule a new appointment
```

## AI Stack (CRITICAL — Groq is PRIMARY)
```python
# ai/gemini_client.py — call_gemini() uses Groq first, Gemini as fallback
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# All AI callers import:
from ai.gemini_client import call_gemini as call_claude

# call_gemini signature:
async def call_gemini(prompt, image_path=None) -> str
# NOTE: no system= param — prepend system to prompt: f"{system}\n\n{prompt}"
```

## Env Vars (Vercel)
| Variable | Notes |
|----------|-------|
| SUPABASE_URL | Supabase project URL |
| SUPABASE_KEY | service_role key — bypasses RLS, required for all writes |
| GROQ_API_KEY | Primary AI — set |
| GEMINI_API_KEY | Fallback AI — set |
| ANTHROPIC_API_KEY | Available but not used (paid) |
| TELEGRAM_BOT_TOKEN | @GetAayuBot token — set in Vercel |
| CRON_SECRET | Protects cron endpoints |
| SESSION_SECRET | Cookie signing |
| ABDM_CLIENT_ID | NOT YET SET — pending NHA sandbox approval |
| ABDM_CLIENT_SECRET | NOT YET SET — pending NHA sandbox approval |
| ABDM_BASE_URL | https://sandbox.abdm.gov.in/api/v3 (default in code) |

## Key Files
| File | Purpose |
|------|---------|
| `web/app.py` | FastAPI — all routes, PTB singleton, webhook, cron, /abha/* endpoints |
| `web/auth.py` | supabase_login(), session cookie, require_user dependency |
| `web/templates/base.html` | Nav with active tab JS highlighting (teal-400 for active) |
| `web/templates/dashboard.html` | ABHA badge (verified/unverified) + async /api/story load |
| `web/templates/abha_verify.html` | ABHA OTP verification flow (3 steps: mobile → OTP → success) |
| `web/templates/upload.html` | Unified drop zone, file chips, per-file result cards |
| `database/queries.py` | All DB reads/writes; save_abha_verification() |
| `database/auth_queries.py` | user_profiles: get/set telegram_chat_id |
| `database/schema_v5.sql` | Adds abha_verified cols + abha_verifications table |
| `abdm/abha_api.py` | Full ABDM M1 API client — OTP, verify, profile fetch |
| `abdm/abha.py` | Local ABHA ID generator (fallback), suffix = "@aayu" |
| `bot/handlers/start.py` | /start and /help — comprehensive WELCOME message |
| `bot/handlers/text_handler.py` | Non-medical text → helpful examples; medical → care events |
| `bot/handlers/document_handler.py` | PDF + JPG/PNG/WEBP — classifies + routes to OCR/lab extractor |
| `ai/gemini_client.py` | Groq (primary) + Gemini (fallback) unified call_gemini() |
| `ai/text_parser.py` | Robust JSON parsing + try/except fallback for non-medical text |
| `config/settings.py` | All env vars including ABDM_CLIENT_ID, ABDM_CLIENT_SECRET |

## Special Endpoints
| Endpoint | Purpose |
|----------|---------|
| `POST /upload/analyze` | Unified upload — accepts multiple files, AI classifies each |
| `GET /api/story` | Returns Care Snapshot JSON for dashboard async load |
| `GET /cron/test-briefing` | Manually trigger daily briefing + Telegram send |
| `GET /abha/verify` | ABHA OTP verification page |
| `POST /abha/send-otp` | Trigger ABDM M1 OTP to mobile — returns txnId |
| `POST /abha/verify-otp` | Verify OTP, fetch profile, save to DB |

## ABDM Sprint 2 — OTP Flow
```python
# abdm/abha_api.py
async def _get_access_token() -> str          # POST /gateway/sessions
async def generate_mobile_otp(mobile) -> dict  # returns {"txnId": "..."}
async def verify_mobile_otp(txn_id, otp) -> dict  # returns user token
async def get_abha_profile(user_token) -> dict    # GET profile
async def verify_abha_by_mobile(mobile, otp, txn_id) -> dict  # high-level helper

# When ABDM_CLIENT_ID is empty: /abha/send-otp returns HTTP 503 + amber notice in UI
# When credentials arrive: add to Vercel env vars → OTP flow activates automatically
```

## JSON Parsing (Robust)
```python
def _parse_raw(raw):
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw).strip()
    start = raw.find("{"); end = raw.rfind("}") + 1
    if start != -1 and end > start: raw = raw[start:end]
    raw = re.sub(r",\s*([}\]])", r"\1", raw)  # remove trailing commas
    return json.loads(raw)
```

## Design System (dark theme)
- Background: `bg-zinc-950` (#09090b)
- Surface/card: `bg-zinc-900` (#18181b)
- Border: `border-zinc-800` / `border-zinc-700`
- Accent: `teal-400` / `teal-500` (#2dd4bf / #14b8a6)
- Text: `text-white` / `text-zinc-100` / `text-zinc-400`
- No emojis, no em dashes anywhere in templates

## UHI/ABDM Context
- **ABHA** = 14-digit health ID. Aayu stores placeholder IDs until ABDM sandbox live
- **HIE-CM** = Health Information Exchange & Consent Manager — federated consent, NOT blockchain
- **Aayu's ABDM roles:** HIU (requests records with consent) + EUA (service discovery) + HIP (Sprint 3)
- **ABDM certification path:** Sandbox → M1 → M2 (HIP) → M3 (HIU) → CERT-IN cert → production

## How to Ask Claude to Continue
Say: **"Read the Vault and pick up where we left off"**
