import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)
from database.queries import get_patient_for_telegram_user, insert_appointment, get_or_create_doctor

logger = logging.getLogger(__name__)

ASK_DOCTOR, ASK_DATE, ASK_HOSPITAL, ASK_TYPE, ASK_NOTES = range(5)


async def add_appointment_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    patient = get_patient_for_telegram_user(str(update.effective_chat.id))
    if not patient:
        await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
        return ConversationHandler.END
    context.user_data["appt_patient_id"] = patient["id"]
    await update.message.reply_text(
        "📅 Let's add an appointment.\n\n"
        "Doctor's name? (or type 'skip')"
    )
    return ASK_DOCTOR


async def got_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["appt_doctor"] = None if text.lower() == "skip" else text
    await update.message.reply_text(
        "Date and time?\nFormat: YYYY-MM-DD HH:MM (e.g. 2026-06-15 10:30)\nor just YYYY-MM-DD for all-day"
    )
    return ASK_DATE


async def got_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    dt = None
    for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(text, fmt)
            break
        except ValueError:
            pass
    if not dt:
        await update.message.reply_text("Couldn't read that date. Try: 2026-06-15 10:30")
        return ASK_DATE
    context.user_data["appt_date"] = dt.isoformat()
    await update.message.reply_text("Hospital or clinic name? (or 'skip')")
    return ASK_HOSPITAL


async def got_hospital(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["appt_hospital"] = None if text.lower() == "skip" else text
    await update.message.reply_text(
        "Appointment type?\nOptions: Follow-up, Consultation, Lab Test, Procedure\n(or type your own / 'skip')"
    )
    return ASK_TYPE


async def got_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["appt_type"] = None if text.lower() == "skip" else text
    await update.message.reply_text("Any prerequisites or notes? (or 'skip')")
    return ASK_NOTES


async def got_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    notes = None if text.lower() == "skip" else text

    patient_id = context.user_data["appt_patient_id"]
    doctor_name = context.user_data.get("appt_doctor")
    hospital = context.user_data.get("appt_hospital")

    doctor_id = None
    if doctor_name:
        doc = get_or_create_doctor(doctor_name, hospital=hospital)
        if doc:
            doctor_id = doc["id"]

    try:
        insert_appointment(patient_id, {
            "doctor_id": doctor_id,
            "appointment_date": context.user_data["appt_date"],
            "hospital": hospital,
            "appointment_type": context.user_data.get("appt_type") or "Follow-up",
            "notes": notes,
            "status": "scheduled",
        })
        doc_str = f"Dr. {doctor_name}" if doctor_name else "appointment"
        date_str = context.user_data["appt_date"][:10]
        await update.message.reply_text(
            f"✅ Appointment added!\n\n"
            f"📅 {date_str}\n"
            f"👨‍⚕️ {doc_str}\n"
            f"🏥 {hospital or '—'}\n\n"
            "You'll get a reminder 14 days before if prerequisites are pending."
        )
    except Exception:
        logger.exception("Failed to add appointment")
        await update.message.reply_text("Sorry, couldn't save the appointment. Please try again.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def get_add_appointment_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("addappointment", add_appointment_start)],
        states={
            ASK_DOCTOR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, got_doctor)],
            ASK_DATE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, got_date)],
            ASK_HOSPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_hospital)],
            ASK_TYPE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, got_type)],
            ASK_NOTES:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_notes)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=180,
    )
