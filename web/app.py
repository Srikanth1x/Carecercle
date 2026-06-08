import asyncio
import logging
import os
import tempfile
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse

from config.settings import CRON_SECRET
from web.auth import (
    supabase_login, supabase_register, require_user,
    set_session_cookie, clear_session_cookie, RedirectException
)
from database.auth_queries import get_patient_by_user_id, get_patients_by_user_id
from database.queries import (
    create_patient, get_or_create_doctor,
    get_active_medications, get_recent_lab_reports, get_active_alerts,
    get_recent_care_events, get_upcoming_appointments, acknowledge_alert,
    get_alert_by_id, insert_medication, insert_lab_report,
    insert_care_event, insert_appointment,
)

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
app = FastAPI(title="Aayu")
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

_PATIENT_COOKIE = "cc_patient"
_PATIENT_COOKIE_MAX_AGE = 86400 * 30  # 30 days

def _get_active_patient(user_id: str, cookie_patient_id: str = None) -> dict | None:
    """Return the active patient for a user. Prefers cookie selection, falls back to first."""
    all_patients = get_patients_by_user_id(user_id)
    if not all_patients:
        return None
    if cookie_patient_id:
        match = next((p for p in all_patients if p["id"] == cookie_patient_id), None)
        if match:
            return match
    return all_patients[0]

def get_patient_data(user: dict, active_patient_id: str = None) -> dict | None:
    all_patients = get_patients_by_user_id(user["id"])
    if not all_patients:
        return None
    if active_patient_id:
        patient = next((p for p in all_patients if p["id"] == active_patient_id), all_patients[0])
    else:
        patient = all_patients[0]
    pid = patient["id"]
    meds = get_active_medications(pid)
    labs = get_recent_lab_reports(pid, days=90)
    alerts = get_active_alerts(pid)
    events = get_recent_care_events(pid, hours=72)
    appts = get_upcoming_appointments(pid)
    has_critical = any(a["severity"] == "critical" for a in alerts)
    has_warning = any(a["severity"] in ("warning", "moderate") for a in alerts) or any(l["is_abnormal"] for l in labs)
    status = "critical" if has_critical else ("warning" if has_warning else "ok")
    return dict(patient=patient, all_patients=all_patients, meds=meds, labs=labs, alerts=alerts,
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
    token = result["access_token"]
    user_id = (result.get("user") or {}).get("id", "")
    first_patient = get_patient_by_user_id(user_id) if user_id else None
    dest = "/dashboard" if first_patient else "/setup"
    response = RedirectResponse(dest, status_code=303)
    set_session_cookie(response, token)
    if first_patient:
        response.set_cookie(_PATIENT_COOKIE, first_patient["id"],
                            httponly=True, samesite="lax", max_age=_PATIENT_COOKIE_MAX_AGE)
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
    response.delete_cookie(_PATIENT_COOKIE)
    return response

# ---- Setup wizard (first patient) ----

@app.get("/setup")
async def setup_page(request: Request, user: dict = Depends(require_user)):
    if get_patient_by_user_id(user["id"]):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("setup.html", {"request": request, "error": None})

@app.post("/setup")
async def setup_submit(
    request: Request, user: dict = Depends(require_user),
    full_name: str = Form(...),
    date_of_birth: str = Form(""),
    gender: str = Form(""),
    blood_group: str = Form(""),
    phone: str = Form(""),
    abha_id: str = Form(""),
    abha_address: str = Form(""),
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
            "abha_id": abha_id.replace("-", "").strip() or None,
            "abha_address": abha_address.strip() or None,
            "emergency_contact_name": emergency_contact_name or None,
            "emergency_contact_phone": emergency_contact_phone or None,
            "address_city": address_city or None,
            "address_state": address_state or None,
            "known_conditions": conditions,
        }
        patient = create_patient(user["id"], data)
        response = RedirectResponse("/upload", status_code=303)
        response.set_cookie(_PATIENT_COOKIE, patient["id"],
                            httponly=True, samesite="lax", max_age=_PATIENT_COOKIE_MAX_AGE)
        return response
    except Exception as e:
        logger.exception("Failed to create patient")
        return templates.TemplateResponse("setup.html", {
            "request": request, "error": str(e)
        })

# ---- ABHA OTP Verification (Sprint 2) ----

@app.get("/abha/verify")
async def abha_verify_page(request: Request, user: dict = Depends(require_user)):
    active_pid = request.cookies.get(_PATIENT_COOKIE)
    patient = _get_active_patient(user["id"], active_pid)
    if not patient:
        return RedirectResponse("/setup")
    return templates.TemplateResponse("abha_verify.html", {"request": request, "patient": patient})


@app.post("/abha/send-otp")
async def abha_send_otp(request: Request, user: dict = Depends(require_user)):
    from config.settings import ABDM_CLIENT_ID
    if not ABDM_CLIENT_ID:
        return JSONResponse({"ok": False, "error": "ABDM sandbox not yet active. Enter ABHA number manually for now."}, status_code=503)
    body = await request.json()
    mobile = (body.get("mobile") or "").strip()
    if not mobile or len(mobile) != 10:
        return JSONResponse({"ok": False, "error": "Enter a valid 10-digit mobile number."}, status_code=400)
    try:
        from abdm.abha_api import generate_mobile_otp
        result = await generate_mobile_otp(mobile)
        return JSONResponse({"ok": True, "txnId": result.get("txnId") or result.get("transactionId")})
    except Exception as e:
        logger.exception("ABHA OTP send failed")
        return JSONResponse({"ok": False, "error": "Could not reach ABDM. Try again."}, status_code=502)


@app.post("/abha/verify-otp")
async def abha_verify_otp(request: Request, user: dict = Depends(require_user)):
    body = await request.json()
    txn_id = body.get("txnId", "")
    otp = body.get("otp", "").strip()
    mobile = body.get("mobile", "").strip()
    patient_id = body.get("patientId", "")
    if not all([txn_id, otp, mobile, patient_id]):
        return JSONResponse({"ok": False, "error": "Missing fields."}, status_code=400)
    try:
        from abdm.abha_api import verify_abha_by_mobile
        from database.queries import save_abha_verification
        profile = await verify_abha_by_mobile(mobile, otp, txn_id)
        patient = save_abha_verification(patient_id, profile)
        return JSONResponse({
            "ok": True,
            "abhaNumber": profile["abha_number"],
            "abhaAddress": profile.get("abha_address"),
            "name": profile.get("name_on_abha"),
        })
    except Exception as e:
        logger.exception("ABHA OTP verify failed")
        return JSONResponse({"ok": False, "error": "OTP verification failed. Check the code and try again."}, status_code=400)


# ---- Add another patient ----

@app.get("/patient/new")
async def new_patient_page(request: Request, user: dict = Depends(require_user)):
    return templates.TemplateResponse("setup.html", {
        "request": request, "error": None, "form_action": "/patient/new"
    })

@app.post("/patient/new")
async def new_patient_submit(
    request: Request, user: dict = Depends(require_user),
    full_name: str = Form(...),
    date_of_birth: str = Form(""),
    gender: str = Form(""),
    blood_group: str = Form(""),
    phone: str = Form(""),
    abha_id: str = Form(""),
    abha_address: str = Form(""),
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
            "abha_id": abha_id.replace("-", "").strip() or None,
            "abha_address": abha_address.strip() or None,
            "emergency_contact_name": emergency_contact_name or None,
            "emergency_contact_phone": emergency_contact_phone or None,
            "address_city": address_city or None,
            "address_state": address_state or None,
            "known_conditions": conditions,
        }
        patient = create_patient(user["id"], data)
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(_PATIENT_COOKIE, patient["id"],
                            httponly=True, samesite="lax", max_age=_PATIENT_COOKIE_MAX_AGE)
        return response
    except Exception as e:
        logger.exception("Failed to create patient")
        return templates.TemplateResponse("setup.html", {
            "request": request, "error": str(e), "form_action": "/patient/new"
        })

# ---- Patient switcher ----

@app.get("/patients/switch/{patient_id}")
async def switch_patient(patient_id: str, request: Request, user: dict = Depends(require_user)):
    all_patients = get_patients_by_user_id(user["id"])
    if not any(p["id"] == patient_id for p in all_patients):
        return RedirectResponse("/dashboard")
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(_PATIENT_COOKIE, patient_id,
                        httponly=True, samesite="lax", max_age=_PATIENT_COOKIE_MAX_AGE)
    return response

# ---- Upload records ----

@app.get("/upload")
async def upload_page(request: Request, user: dict = Depends(require_user)):
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
    if not patient:
        return RedirectResponse("/setup")
    all_patients = get_patients_by_user_id(user["id"])
    return templates.TemplateResponse("upload.html", {
        "request": request, "patient": patient, "all_patients": all_patients
    })

@app.post("/upload/analyze")
async def upload_analyze(
    request: Request,
    user: dict = Depends(require_user),
    files: List[UploadFile] = File(...),
):
    import datetime
    from ai.document_classifier import classify
    from ai.ocr import extract_prescription_from_photo
    from ai.pdf_parser import extract_lab_report_from_pdf

    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
    if not patient:
        return JSONResponse({"error": "No patient found"}, status_code=400)

    pid = patient["id"]
    results = []

    for upload in files:
        filename = upload.filename or "unknown"
        suffix = os.path.splitext(filename)[1].lower() or ".bin"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await upload.read())
            tmp_path = tmp.name

        file_result = {"filename": filename, "type": "other", "description": "", "saved": [], "skipped": [], "abnormal": [], "error": None}

        try:
            # Step 1: Classify
            cls = await classify(tmp_path)
            doc_type = cls.get("type", "other")
            file_result["type"] = doc_type
            file_result["description"] = cls.get("description", "")

            # Step 2: Extract + Save
            if doc_type == "prescription":
                result = await extract_prescription_from_photo(tmp_path)
                for med in result.get("medications", []):
                    doctor_id = None
                    if result.get("doctor_name"):
                        doc = get_or_create_doctor(
                            result["doctor_name"],
                            specialty=result.get("doctor_specialty"),
                            hospital=result.get("hospital_name"),
                        )
                        doctor_id = doc["id"] if doc else None
                    outcome = insert_medication(pid, doctor_id, {
                        "drug_name": med["drug_name"],
                        "dosage": med.get("dosage") or "",
                        "frequency": med.get("frequency") or "as directed",
                        "timing": med.get("timing"),
                        "route": med.get("route", "oral"),
                        "source_type": "photo_ocr",
                        "source_raw_text": str(result),
                        "status": "active",
                    })
                    if outcome.get("action") == "duplicate":
                        file_result["skipped"].append(med["drug_name"])
                    else:
                        file_result["saved"].append(med["drug_name"])
                if result.get("notes"):
                    file_result["description"] = result["notes"]

            elif doc_type in ("lab_report", "imaging_report", "other"):
                result = await extract_lab_report_from_pdf(tmp_path) if suffix == ".pdf" else await extract_prescription_from_photo(tmp_path)
                for test in result.get("tests", []):
                    insert_lab_report(pid, {
                        "test_name": test["test_name"],
                        "test_value": str(test.get("value", "")),
                        "unit": test.get("unit"),
                        "reference_range": test.get("reference_range"),
                        "is_abnormal": test.get("is_abnormal", False),
                        "test_date": result.get("date") or datetime.date.today().isoformat(),
                        "lab_name": result.get("lab_name"),
                        "source_type": "pdf_extract",
                        "source_raw_text": str(result),
                    })
                    file_result["saved"].append(test["test_name"])
                    if test.get("is_abnormal"):
                        file_result["abnormal"].append(test["test_name"])
                if result.get("notes") and not file_result["description"]:
                    file_result["description"] = result["notes"]

            elif doc_type in ("discharge_summary", "vaccination_record"):
                result = await extract_lab_report_from_pdf(tmp_path) if suffix == ".pdf" else {"tests": [], "notes": cls.get("description", "")}
                insert_care_event(pid, {
                    "event_type": "document",
                    "event_description": cls.get("description", filename),
                    "severity": "normal",
                    "reported_by": "web_upload",
                    "source_type": "pdf_extract",
                    "source_raw_text": result.get("notes", ""),
                })
                file_result["saved"].append("Document logged")

        except Exception as e:
            logger.exception("Failed to process %s", filename)
            file_result["error"] = str(e)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        results.append(file_result)

    # Send emergency Telegram alert if any abnormal values found
    all_abnormal = []
    for r in results:
        for flag in r.get("abnormal", []):
            all_abnormal.append(f"{flag} ({r['filename']})")
    if all_abnormal:
        asyncio.create_task(_send_emergency_alerts(patient, all_abnormal))

    return JSONResponse({"results": results})

# ---- Dashboard ----

@app.get("/dashboard")
async def dashboard(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user, request.cookies.get(_PATIENT_COOKIE))
    if not data:
        return RedirectResponse("/setup", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request, **data})

# ---- Medications ----

@app.get("/medications")
async def medications(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user, request.cookies.get(_PATIENT_COOKIE))
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("medications.html", {"request": request, **data})

@app.get("/medications/add")
async def add_medication_page(request: Request, user: dict = Depends(require_user)):
    if not _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE)):
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
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
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
    data = get_patient_data(user, request.cookies.get(_PATIENT_COOKIE))
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("labs.html", {"request": request, **data})

@app.get("/labs/add")
async def add_lab_page(request: Request, user: dict = Depends(require_user)):
    if not _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE)):
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
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
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
    data = get_patient_data(user, request.cookies.get(_PATIENT_COOKIE))
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("timeline.html", {"request": request, **data})

@app.get("/events/add")
async def add_event_page(request: Request, user: dict = Depends(require_user)):
    if not _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE)):
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
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
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
    if not _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE)):
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
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
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

@app.get("/appointments")
async def appointments_page(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user, request.cookies.get(_PATIENT_COOKIE))
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("appointments.html", {"request": request, **data})

# ---- Alerts ----

@app.get("/alerts")
async def alerts_page(request: Request, user: dict = Depends(require_user)):
    data = get_patient_data(user, request.cookies.get(_PATIENT_COOKIE))
    if not data:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("alerts.html", {"request": request, **data})

@app.post("/alerts/{alert_id}/acknowledge")
async def ack_alert(alert_id: str, request: Request, user: dict = Depends(require_user)):
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
    if not patient:
        return JSONResponse({"error": "Not found"}, status_code=404)
    alert = get_alert_by_id(alert_id)
    if not alert or alert["patient_id"] != patient["id"]:
        return JSONResponse({"error": "Not found"}, status_code=404)
    acknowledge_alert(alert_id)
    return JSONResponse({"status": "ok"})

# ---- Share links ----

@app.post("/share/generate")
async def generate_share(request: Request, user: dict = Depends(require_user)):
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
    if not patient:
        return JSONResponse({"error": "No patient"}, status_code=404)
    from database.queries import create_share_link
    link = create_share_link(patient["id"])
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({"url": f"{base_url}/share/{link['token']}", "expires_in": "7 days"})

@app.get("/share/{token}")
async def share_view(token: str, request: Request):
    from database.queries import get_share_link_by_token
    from database.supabase_client import get_client
    link = get_share_link_by_token(token)
    if not link:
        return templates.TemplateResponse("share.html", {"request": request, "expired": True})
    pid = link["patient_id"]
    db = get_client()
    patient_result = db.table("patients").select("*").eq("id", pid).execute()
    patient = patient_result.data[0] if patient_result.data else None
    if not patient:
        return templates.TemplateResponse("share.html", {"request": request, "expired": True})
    meds = get_active_medications(pid)
    labs = get_recent_lab_reports(pid, days=30)
    alerts = get_active_alerts(pid)
    appts = get_upcoming_appointments(pid)
    return templates.TemplateResponse("share.html", {
        "request": request, "expired": False,
        "patient": patient, "meds": meds, "labs": labs, "alerts": alerts, "appts": appts
    })

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

@app.get("/cron/test-briefing")
async def test_briefing(request: Request, user: dict = Depends(require_user)):
    try:
        patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
        if not patient:
            return JSONResponse({"error": "No patient"}, status_code=404)
        from database.auth_queries import get_all_linked_users
        linked = [u for u in get_all_linked_users() if u.get("user_id") == user["id"]]
        if not linked or not linked[0].get("telegram_chat_id"):
            return JSONResponse({"error": "No Telegram linked"}, status_code=400)
        from ai.briefing_generator import generate_briefing
        from telegram import Bot
        from config.settings import TELEGRAM_BOT_TOKEN
        text = await generate_briefing(patient)
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=linked[0]["telegram_chat_id"],
            text=text,
            parse_mode="Markdown"
        )
        return JSONResponse({"ok": True, "preview": text[:400]})
    except Exception as e:
        logger.exception("test-briefing failed")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/cron/wipe-demo")
async def wipe_demo(request: Request, user: dict = Depends(require_user)):
    from database.supabase_client import get_client
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
    if not patient:
        return JSONResponse({"error": "No patient"}, status_code=404)
    pid = patient["id"]
    db = get_client()
    db.table("appointments").delete().eq("patient_id", pid).execute()
    db.table("alerts").delete().eq("patient_id", pid).execute()
    db.table("care_events").delete().eq("patient_id", pid).execute()
    return JSONResponse({"ok": True, "wiped": ["appointments", "alerts", "care_events"]})


@app.get("/cron/seed-demo")
async def seed_demo(request: Request, user: dict = Depends(require_user)):
    from datetime import date, datetime, timedelta, timezone
    from database.queries import insert_care_event, insert_appointment, insert_alert, get_or_create_doctor

    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
    if not patient:
        return JSONResponse({"error": "No patient found"}, status_code=404)
    pid = patient["id"]

    now = datetime.now(timezone.utc)
    today = date.today()
    seeded = {"appointments": 0, "events": 0, "alerts": 0}

    appt_data = [
        {"doctor": "Venkata Lakshmi", "specialty": "Cardiology", "hospital": "Apollo Hospitals, Hyderabad", "days": 12, "type": "Follow-up", "notes": "Review echocardiogram results and adjust Diltiazem dose.", "prerequisites": ["ECG", "2D Echo repeat"], "prereq_status": "pending"},
        {"doctor": "Annapurna", "specialty": "Endocrinology", "hospital": "KIMS Hospital, Secunderabad", "days": 22, "type": "Routine check", "notes": "HbA1c follow-up — target below 7.5%.", "prerequisites": ["Fasting Blood Sugar", "HbA1c"], "prereq_status": "pending"},
        {"doctor": "Srinivasa Rao", "specialty": "General Physician", "hospital": "Rao Clinic, Secunderabad", "days": 5, "type": "Routine check", "notes": "Monthly BP review and medication refill.", "prerequisites": [], "prereq_status": "done"},
    ]
    for a in appt_data:
        doc = get_or_create_doctor(a["doctor"], specialty=a["specialty"], hospital=a["hospital"])
        insert_appointment(pid, {"doctor_id": doc["id"] if doc else None, "appointment_date": (today + timedelta(days=a["days"])).isoformat() + "T10:00:00", "appointment_type": a["type"], "hospital": a["hospital"], "notes": a["notes"], "prerequisites": a["prerequisites"] or None, "prerequisite_status": a["prereq_status"]})
        seeded["appointments"] += 1

    events = [
        {"h": 2, "type": "observation", "desc": "Morning BP: 142/88 mmHg. Slightly elevated. Took Amlodipine 5mg after breakfast.", "sev": "attention", "src": "caregiver_update"},
        {"h": 5, "type": "medication_taken", "desc": "All morning medications taken on time: Metformin 500mg, Levothyroxine 50mcg, Aspirin 75mg.", "sev": "normal", "src": "caregiver_update"},
        {"h": 26, "type": "symptom", "desc": "Mild dizziness reported after lunch. Lasted ~20 minutes. Blood sugar checked: 168 mg/dL post-meal.", "sev": "attention", "src": "caregiver_update"},
        {"h": 30, "type": "medication_taken", "desc": "All medications taken. Skipped evening walk due to rain.", "sev": "normal", "src": "caregiver_update"},
        {"h": 50, "type": "observation", "desc": "Fasting blood sugar: 142 mg/dL. Slightly above target. Dietary adjustments discussed.", "sev": "attention", "src": "caregiver_update"},
        {"h": 72, "type": "doctor_visit", "desc": "GP visit with Dr. Srinivasa Rao. BP log reviewed. Continuing current medications. Next visit in 5 days.", "sev": "normal", "src": "manual"},
        {"h": 96, "type": "medication_taken", "desc": "Missed evening Metformin dose. Patient forgot — caregiver reminded via call.", "sev": "attention", "src": "caregiver_update"},
    ]
    for e in events:
        insert_care_event(pid, {"event_type": e["type"], "event_description": e["desc"], "event_timestamp": (now - timedelta(hours=e["h"])).isoformat(), "severity": e["sev"], "reported_by": "caregiver", "source_type": e["src"]})
        seeded["events"] += 1

    alert_data = [
        {"title": "HbA1c above target — 8.2%", "desc": "Latest HbA1c is 8.2%, above the 7.5% target. Review with Dr. Annapurna at upcoming endocrinology appointment.", "sev": "warning", "type": "lab_flag"},
        {"title": "ECG and Echo not yet scheduled", "desc": "Cardiology follow-up with Dr. Venkata Lakshmi is in 12 days. ECG and 2D Echo are prerequisites and have not been booked.", "sev": "warning", "type": "appointment"},
        {"title": "Medication refill due in 5 days", "desc": "Diltiazem 60mg and Clopidogrel 75mg supply estimated to run out in ~5 days. Contact Rao Clinic for prescription renewal.", "sev": "warning", "type": "medication"},
    ]
    for a in alert_data:
        insert_alert(pid, {"title": a["title"], "description": a["desc"], "severity": a["sev"], "alert_type": a["type"], "status": "active"})
        seeded["alerts"] += 1

    return JSONResponse({"ok": True, "seeded": seeded, "patient": patient["full_name"]})


@app.get("/api/story")
async def care_story(request: Request, user: dict = Depends(require_user)):
    patient = _get_active_patient(user["id"], request.cookies.get(_PATIENT_COOKIE))
    if not patient:
        return JSONResponse({"story": ""})
    from ai.story_generator import generate_care_story
    try:
        story = await generate_care_story(patient)
    except Exception as e:
        logger.exception("Story generation failed")
        story = ""
    return JSONResponse({"story": story})


async def _send_emergency_alerts(patient: dict, abnormal_items: list):
    """Fire-and-forget: send Telegram alert when critical abnormal values are uploaded."""
    try:
        from database.auth_queries import get_all_linked_users
        users = get_all_linked_users()
        patient_user_id = patient.get("user_id")
        linked = [u for u in users if u.get("user_id") == patient_user_id]
        if not linked:
            return
        ptb = await _get_ptb_app()
        lines = "\n".join(f"• {item}" for item in abnormal_items[:8])
        msg = (
            f"🚨 *Abnormal values detected in uploaded documents*\n\n"
            f"{lines}\n\n"
            f"_Review these with {patient.get('full_name', 'your parent')}'s doctor._"
        )
        for u in linked:
            chat_id = u.get("telegram_chat_id")
            if chat_id:
                await ptb.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    except Exception:
        logger.exception("Emergency alert send failed")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})
