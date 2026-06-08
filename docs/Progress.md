# Aayu — Progress Tracker

Last updated: 2026-06-08

---

## Completed

### Deployment
- [x] Live at https://getaayu.in (Vercel)
- [x] GitHub: https://github.com/Srikanth1x/Carecercle (main, up to date)
- [x] GoDaddy domain getaayu.in: A @ → 76.76.21.21, CNAME www → cname.vercel-dns.com
- [x] Telegram webhook at https://getaayu.in/webhook
- [x] Vercel Cron: briefing (7AM IST), nudges (9AM IST), silence (8PM IST)

### Auth & Security
- [x] Login/register via Supabase Auth REST
- [x] Session cookie: httponly, secure, 7-day, samesite=lax
- [x] IDOR fix on /alerts/{id}/acknowledge
- [x] CRON_SECRET required on cron endpoints
- [x] RLS: backend_full_access TO service_role on all tables

### Web Forms & Pages
- [x] /patient/add, /medications/add, /labs/add, /events/add, /appointments/add
- [x] /dashboard, /medications, /labs, /timeline, /appointments, /alerts, /no_patient
- [x] Active nav tab highlighting (teal-400)
- [x] Unified upload page — AI classifies each file per-type

### AI
- [x] **Groq (llama-4-scout-17b-16e-instruct) — PRIMARY, free, vision-capable**
- [x] Gemini 2.0 Flash — fallback
- [x] Robust JSON parsing in all extractors
- [x] ai/text_parser.py: non-medical text → empty events, no crash

### Care Story / Daily Briefing
- [x] /api/story — Care Snapshot from real patient data
- [x] Dashboard Care Snapshot card — async JS load
- [x] /cron/briefing — 7AM IST daily Telegram message

### Database (Schema v5 — current)
- [x] patients: abha_verified, abha_verified_at, abha_mobile_last4
- [x] abha_verifications table
- [x] share_links table, user_profiles table
- [x] All core tables: patients, medications, lab_reports, care_events, appointments, alerts, daily_briefings, doctors
- [x] RLS, indexes, CHECK constraints, triggers

### Telegram Bot (@GetAayuBot)
- [x] Migrated from @CarCercle_Bot to @GetAayuBot
- [x] Webhook mode, PTB singleton with asyncio.Lock
- [x] /start + /help — comprehensive WELCOME message
- [x] /connect, /disconnect, /summary, /check, /meds, /labs, /briefing, /sos, /addappointment
- [x] Document handler: PDF + JPG/PNG/WEBP — classifies → OCR or lab extractor
- [x] Text handler: non-medical → helpful examples, medical → care events
- [x] BotFather /setcommands configured
- [x] Emergency alerts on abnormal lab upload

### Rebrand: CareCircle → Aayu (2026-06-08)
- [x] All templates: title, nav logo, bot mentions → Aayu / @GetAayuBot
- [x] abdm/abha.py: suffix "@carecircle" → "@aayu"
- [x] database/queries.py: fallback abha_address suffix → "@aayu"
- [x] abdm/consent.py, bot/handlers/connect.py, bot/main.py, scripts/link_telegram.py
- [x] test files: carecercle.vercel.app → getaayu.in

### Sprint 1 — DONE (2026-05-29)
- [x] Multi-patient per caregiver — patient switcher dropdown, cc_patient cookie
- [x] Share links — share_links table, generate/view routes, public share.html

### Sprint 2 — Scaffold DONE (2026-06-08)
- [x] ABDM sandbox registration submitted (In Progress, NHA approval 2-4 days)
- [x] abdm/abha_api.py — ABDM M1 API client (OTP send, verify, profile fetch)
- [x] web/templates/abha_verify.html — 3-state OTP flow (mobile → OTP → success)
- [x] web/app.py: /abha/verify, /abha/send-otp, /abha/verify-otp routes
- [x] dashboard.html: ABHA verified (emerald) / unverified (blue + Verify link) badges
- [x] database/queries.py: save_abha_verification()
- [x] config/settings.py: ABDM_CLIENT_ID, ABDM_CLIENT_SECRET, ABDM_BASE_URL
- [x] Graceful degradation: 503 + amber notice when credentials not set
- [x] Schema v5 ran clean in Supabase

---

## Pending / Next Steps

### Sprint 2 — Remaining
- [ ] **When NHA emails credentials**: add ABDM_CLIENT_ID + ABDM_CLIENT_SECRET to Vercel env vars
- [ ] Update setup.html Step 2: OTP verification option (vs manual ABHA entry)
- [ ] User action: send `/connect` to @GetAayuBot to re-link Telegram

### Sprint 3 — Self-HIP Registration
- [ ] abdm/fhir_serializer.py — FHIR R4 JSON serialization
- [ ] abdm/hip_client.py — ABDM HIP webhook handlers
- [ ] Auto-push records to ABHA locker on upload
- [ ] CERT-IN security audit

### Sprint 4 — HIU + Consent UI
- [ ] abdm/hiu_client.py — consent request, FHIR fetch, decrypt
- [ ] /consent page — view/revoke consents
- [ ] "Fetch Hospital Records" button on dashboard

### Sprint 5 — Full UHI EUA (Q4 2026)
- [ ] Register Aayu as UHI EUA with NHA
- [ ] /book and /sync Telegram commands
- [ ] HCX insurance claim initiation

### Business
- [ ] 10 pilot families (target: Q3 2026)
- [ ] Privacy Policy + Terms of Service pages
- [ ] DPDP Act 2023 compliance review
- [ ] Pre-seed round (target: Q3 2026)

### UX / Parity
- [ ] setup.html Step 2: OTP option
- [ ] /addmedication, /addlab, /addevent Telegram handlers
- [ ] Edit/delete on web forms
- [ ] Patient profile edit page (/patient/edit)
- [ ] Medication discontinue/archive flow

---

## Known Issues / Watch Out For
- **SUPABASE_KEY must be service_role key** — anon key causes RLS violations on all writes
- **Groq is primary AI** — do NOT switch to Anthropic (paid)
- **call_gemini has no system= param** — prepend: `f"{system}\n\n{prompt}"`
- **PDF to Groq**: must render to PNG first (Groq rejects raw PDF bytes)
- **ABDM credentials**: not yet in Vercel — OTP flow shows 503 until ABDM_CLIENT_ID set
- `vercel.json`: cannot have both `builds` and `functions` — use only `builds`
