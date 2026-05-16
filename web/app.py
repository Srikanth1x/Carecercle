import asyncio
import logging
from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
import os

from config.settings import CRON_SECRET
from web.auth import (
    supabase_login, supabase_register, require_user,
    set_session_cookie, clear_session_cookie, RedirectException
)
from database.auth_queries import get_patient_by_user_id
from database.queries import (
    create_patient, get_or_create_doctor,
    get_active_medications, get_recent_lab_reports, get_active_alerts,
    get_recent_care_events, get_upcoming_appointments, acknowledge_alert,
    get_alert_by_id, insert_medication, insert_lab_report,
    insert_care_event, insert_appointment,
)

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
app = FastAPI(title="CareCircle")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ---- Telegram PTB singleton (webhook mode) ----

_ptb_app = None
_ptb_lock = asyncio.Lock()

async def _get_ptb_app():
    global _ptb_app
    async with _ptb_lock:
        if _ptb_app is None:
            from bot.main import create_app
            _ptb_app = create_app()
            await _ptb_app.initialize()
    return _ptb_app

# ---- Exception handler ----

@app.exception_handler(RedirectException)
async def redirect_exception_handler(request, exc):
    return RedirectResponse(url=exc.url)

# ---- Helpers ----

def get_patient_data(user: dict) -> dict | None:
    patient = get_patient_by_user_id(user["id"])
    if not patient:
        return None
    pid = patient["id"]
    meds = get_active_medications(pid)
    labs = get_recent_lab_reports(pid, days=90)
    alerts = get_active_alerts(pid)
    events = get_recent_care_events(pid, hours=72)
    appts = get_upcoming_appointments(pid)
    has_critical = any(a["severity"] == "critical" for a in alerts)
    has_warning = any(a["severity"] in ("warning", "moderate") for a in alerts) or any(l["is_abnormal"] for l in labs)
    status = "critical" if has_critical else ("warning" if has_warning else "ok")
    return dict(patient=patient, meds=meds, labs=labs, alerts=alerts,
                events=events, appts=appts, status=status)

def _check_cron_auth(request: Request) -> bool:
    if not CRON_SECRET:
        logger.error("CRON_SECRET is not set — rejecting cron request")
        return False
    auth = request.headers.get("authorization", "")
    return auth == f"Bearer {CRON_SECRET}"

# ---- Public routes ----

@app.get("/")
async def home(request: Request):
    token = request.cookies.get("cc_token")
    if token:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    registered = request.query_params.get("registered")
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "registered": registered})

@app.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        result = await supabase_login(email, password)
    except ValueError as e:
        return templates.TemplateResponse("login.html", {
            "request": request, "error": str(e), "registered": None
        })
    if not result:
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Invalid email or password.", "registered": None
        })
    response = RedirectResponse("/dashboard", status_code=303)
    set_session_cookie(response, result["access_token"])
    return response

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register")
async def register_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        result = await supabase_register(email, password)
    except ValueError as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": str(e)})
    if not result or result.get("error") or result.get("code"):
        msg = (result.get("msg") or result.get("message") if result else None) or "Registration failed. Try a stronger password."
        return templates.TemplateResponse("register.html", {"request": request, "error": msg})
    return RedirectResponse("/login?registered=1", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse("/login")
    clear_session_cookie(response)
    return response

# ---- Patient setup ----

@app.get("/patient/add")
async def add_patient_page(request: Request, user: dict = Depends(require_user)):
    if get_patient_by_user_id(user["id"]):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("add_patient.html", {"request": request, "error": None})

@app.post("/patient/add")
async def add_patient_submit(
    request: Request, user: dict = Depends(require_user),
    full_name: str = Form(...),
    date_of_birth: str = Form(""),
    gender: str = Form(""),
    blood_group: str = Form(""),
    phone: str = Form(""),
    emergency_contact_name: str = Form(""),
    emergency_contact_phone: str = Form(""),
    address_city: str = Form(""),
    address_state: str = Form(""),
    known_conditions: str = Form(""),
):
    try:
        conditions = [c.strip() for c in known_conditions.split(",") if c.strip()] if known_conditions else []
        data = {
            "full_name": full_name,
            "date_of_birth": date_of_birth or None,
            "gender": gender or None,
            "blood_group": blood_group or None,
            "phone": phone or None,
            "emergency_contact_name": emergency_contact_name or None,
            "emergency_contact_phone": emergency_contact_phone or None,
            "address_city": address_city or None,
            "address_state": address_state or None,
            "known_conditions": conditions,
        }
        create_patient(user["id"], data)
        return RedirectResponse("/dashboard", status_code=303)
    except Exception as e:
        logger.exception("Failed to create patient")
        return templates.TemplateResponse("add_patient.html", {
            "request": request, "error": str(e)
        })

# ---- Dashboard ----

@app.get("/dashboard")
async def dashboard(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return templates.TemplateResponse("no_patient.html", {"request": request, "user": user})
    return templates.TemplateResponse("dashboard.html", {"request": request, **data})

# ---- Medications ----

@app.get("/medications")
async def medications(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("medications.html", {"request": request, **data})

@app.get("/medications/add")
async def add_medication_page(request: Request, user: dict = Depends(require_user)):
    if not get_patient_by_user_id(user["id"]):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("add_medication.html", {"request": request, "error": None})

@app.post("/medications/add")
async def add_medication_submit(
    request: Request, user: dict = Depends(require_user),
    drug_name: str = Form(...),
    dosage: str = Form(...),
    frequency: str = Form(...),
    timing: str = Form(""),
    route: str = Form("oral"),
    purpose: str = Form(""),
    prescribed_date: str = Form(""),
    doctor_name: str = Form(""),
):
    patient = get_patient_by_user_id(user["id"])
    if not patient:
        return RedirectResponse("/dashboard")
    try:
        doctor = get_or_create_doctor(doctor_name) if doctor_name else None
        doctor_id = doctor["id"] if doctor else None
        insert_medication(patient["id"], doctor_id, {
            "drug_name": drug_name,
            "dosage": dosage,
            "frequency": frequency,
            "timing": timing or None,
            "route": route,
            "purpose": purpose or None,
            "prescribed_date": prescribed_date or None,
            "status": "active",
        })
        return RedirectResponse("/medications", status_code=303)
    except Exception as e:
        logger.exception("Failed to add medication")
        return templates.TemplateResponse("add_medication.html", {
            "request": request, "error": str(e)
        })

# ---- Labs ----

@app.get("/labs")
async def labs_page(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("labs.html", {"request": request, **data})

@app.get("/labs/add")
async def add_lab_page(request: Request, user: dict = Depends(require_user)):
    if not get_patient_by_user_id(user["id"]):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("add_lab.html", {"request": request, "error": None})

@app.post("/labs/add")
async def add_lab_submit(
    request: Request, user: dict = Depends(require_user),
    test_name: str = Form(...),
    test_value: str = Form(...),
    unit: str = Form(""),
    reference_range: str = Form(""),
    test_date: str = Form(...),
    lab_name: str = Form(""),
    is_abnormal: str = Form(""),
):
    patient = get_patient_by_user_id(user["id"])
    if not patient:
        return RedirectResponse("/dashboard")
    try:
        insert_lab_report(patient["id"], {
            "test_name": test_name,
            "test_value": test_value,
            "unit": unit or None,
            "reference_range": reference_range or None,
            "test_date": test_date,
            "lab_name": lab_name or None,
            "is_abnormal": bool(is_abnormal),
        })
        return RedirectResponse("/labs", status_code=303)
    except Exception as e:
        logger.exception("Failed to add lab report")
        return templates.TemplateResponse("add_lab.html", {
            "request": request, "error": str(e)
        })

# ---- Timeline / Care Events ----

@app.get("/timeline")
async def timeline(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("timeline.html", {"request": request, **data})

@app.get("/events/add")
async def add_event_page(request: Request, user: dict = Depends(require_user)):
    if not get_patient_by_user_id(user["id"]):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("add_event.html", {"request": request, "error": None})

@app.post("/events/add")
async def add_event_submit(
    request: Request, user: dict = Depends(require_user),
    event_type: str = Form(...),
    event_description: str = Form(...),
    severity: str = Form("normal"),
    reported_by: str = Form(""),
):
    patient = get_patient_by_user_id(user["id"])
    if not patient:
        return RedirectResponse("/dashboard")
    try:
        insert_care_event(patient["id"], {
            "event_type": event_type,
            "event_description": event_description,
            "severity": severity,
            "reported_by": reported_by or "web",
            "source_type": "web",
        })
        return RedirectResponse("/timeline", status_code=303)
    except Exception as e:
        logger.exception("Failed to add care event")
        return templates.TemplateResponse("add_event.html", {
            "request": request, "error": str(e)
        })

# ---- Appointments ----

@app.get("/appointments/add")
async def add_appointment_page(request: Request, user: dict = Depends(require_user)):
    if not get_patient_by_user_id(user["id"]):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("add_appointment.html", {"request": request, "error": None})

@app.post("/appointments/add")
async def add_appointment_submit(
    request: Request, user: dict = Depends(require_user),
    appointment_date: str = Form(...),
    appointment_type: str = Form("Follow-up"),
    doctor_name: str = Form(""),
    hospital: str = Form(""),
    prerequisites: str = Form(""),
    notes: str = Form(""),
):
    patient = get_patient_by_user_id(user["id"])
    if not patient:
        return RedirectResponse("/dashboard")
    try:
        doctor = get_or_create_doctor(doctor_name, hospital=hospital or None) if doctor_name else None
        doctor_id = doctor["id"] if doctor else None
        prereqs = [p.strip() for p in prerequisites.split(",") if p.strip()] if prerequisites else []
        insert_appointment(patient["id"], {
            "doctor_id": doctor_id,
            "appointment_date": appointment_date,
            "appointment_type": appointment_type,
            "hospital": hospital or None,
            "prerequisites": prereqs,
            "prerequisite_status": "pending" if prereqs else "none",
            "notes": notes or None,
            "status": "scheduled",
        })
        return RedirectResponse("/dashboard", status_code=303)
    except Exception as e:
        logger.exception("Failed to add appointment")
        return templates.TemplateResponse("add_appointment.html", {
            "request": request, "error": str(e)
        })

# ---- Appointments list ----

@app.get("/appointments")
async def appointments_page(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("appointments.html", {"request": request, **data})

# ---- Alerts ----

@app.get("/alerts")
async def alerts_page(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("alerts.html", {"request": request, **data})

@app.post("/alerts/{alert_id}/acknowledge")
async def ack_alert(alert_id: str, user: dict = Depends(require_user)):
    patient = get_patient_by_user_id(user["id"])
    if not patient:
        return JSONResponse({"error": "Not found"}, status_code=404)
    alert = get_alert_by_id(alert_id)
    if not alert or alert["patient_id"] != patient["id"]:
        return JSONResponse({"error": "Not found"}, status_code=404)
    acknowledge_alert(alert_id)
    return JSONResponse({"status": "ok"})

# ---- Telegram webhook ----

@app.post("/webhook")
async def telegram_webhook(request: Request):
    ptb = await _get_ptb_app()
    body = await request.json()
    from telegram import Update
    update = Update.de_json(body, ptb.bot)
    await ptb.process_update(update)
    return JSONResponse({"ok": True})

# ---- Cron endpoints ----

@app.get("/cron/briefing")
async def cron_briefing(request: Request):
    if not _check_cron_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    ptb = await _get_ptb_app()
    from bot.scheduler import send_daily_briefing
    await send_daily_briefing(bot=ptb.bot)
    return JSONResponse({"ok": True})

@app.get("/cron/nudges")
async def cron_nudges(request: Request):
    if not _check_cron_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    ptb = await _get_ptb_app()
    from bot.scheduler import check_task_nudges
    await check_task_nudges(bot=ptb.bot)
    return JSONResponse({"ok": True})

@app.get("/cron/silence")
async def cron_silence(request: Request):
    if not _check_cron_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    ptb = await _get_ptb_app()
    from bot.scheduler import check_silence
    await check_silence(bot=ptb.bot)
    return JSONResponse({"ok": True})

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})
