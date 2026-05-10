from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
import os

from web.auth import (
    supabase_login, supabase_register, require_user,
    set_session_cookie, clear_session_cookie, RedirectException
)
from database.auth_queries import get_patient_by_user_id
from database.queries import (
    get_active_medications, get_recent_lab_reports, get_active_alerts,
    get_recent_care_events, get_upcoming_appointments, acknowledge_alert
)

BASE_DIR = os.path.dirname(__file__)
app = FastAPI(title="CareCircle")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.exception_handler(RedirectException)
async def redirect_exception_handler(request, exc):
    return RedirectResponse(url=exc.url)

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
    result = await supabase_login(email, password)
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
    result = await supabase_register(email, password)
    if not result or result.get("error") or result.get("code"):
        msg = result.get("msg") or result.get("message") or "Registration failed. Try a stronger password."
        return templates.TemplateResponse("register.html", {"request": request, "error": msg})
    return RedirectResponse("/login?registered=1", status_code=303)

@app.get("/logout")
async def logout():
    response = RedirectResponse("/login")
    clear_session_cookie(response)
    return response

# ---- Protected routes ----

@app.get("/dashboard")
async def dashboard(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return templates.TemplateResponse("no_patient.html", {"request": request, "user": user})
    return templates.TemplateResponse("dashboard.html", {"request": request, **data})

@app.get("/medications")
async def medications(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("medications.html", {"request": request, **data})

@app.get("/labs")
async def labs_page(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("labs.html", {"request": request, **data})

@app.get("/timeline")
async def timeline(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("timeline.html", {"request": request, **data})

@app.get("/alerts")
async def alerts_page(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user)
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("alerts.html", {"request": request, **data})

@app.post("/alerts/{alert_id}/acknowledge")
async def ack_alert(alert_id: str, user: dict = Depends(require_user)):
    acknowledge_alert(alert_id)
    return JSONResponse({"status": "ok"})
