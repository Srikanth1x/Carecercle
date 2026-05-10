from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, get_active_medications, get_recent_lab_reports, get_upcoming_appointments

async def sos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # No AI delay — pre-cached data only, must respond instantly
    try:
        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        pid = patient["id"]
        meds = get_active_medications(pid)
        labs = get_recent_lab_reports(pid, days=60)

        cardiac_labs = [l for l in labs if "cardiac" in l["test_name"].lower() or "ecg" in l["test_name"].lower()]

        med_lines = "\n".join(
            f"{i}. {m['drug_name']} {m['dosage']} — {m['frequency']}"
            for i, m in enumerate(meds, 1)
        )

        conditions = ", ".join(patient.get("known_conditions") or [])

        card = (
            "🚨 *EMERGENCY INFO — Rajesh Sharma*\n\n"
            "🏥 *NEAREST HOSPITAL:* City Heart Hospital, Lucknow\n\n"
            "📞 *EMERGENCY CONTACTS:*\n"
            "• Dr. Anil Kapoor (Cardiologist): +91-9800000010\n"
            "• Dr. Priya Mehta (Endocrinologist): +91-9800000011\n"
            "• Dr. Suresh Verma (GP): +91-9800000012\n"
            "• Ambulance: 108\n\n"
            f"💊 *CURRENT MEDICATIONS:*\n{med_lines}\n\n"
            f"⚕️ *KNOWN CONDITIONS:* {conditions}\n"
            f"🩸 *BLOOD GROUP:* {patient.get('blood_group', 'N/A')}\n\n"
            "⏱️ Share this with the ER doctor."
        )

        await update.message.reply_text(card, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            "🚨 EMERGENCY\nAmbulance: 108\nCity Heart Hospital, Lucknow\n"
            "Emergency contact: Meera +91-9800000002"
        )
