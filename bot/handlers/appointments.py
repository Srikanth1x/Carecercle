from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, get_upcoming_appointments

async def appointments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        appts = get_upcoming_appointments(patient["id"])

        if not appts:
            await update.message.reply_text("No upcoming appointments.")
            return

        lines = ["🗓️ *Upcoming Appointments*\n"]
        for a in appts:
            doc = a.get("doctors", {}) or {}
            prereqs = a.get("prerequisites") or []
            prereq_status = a.get("prerequisite_status", "pending")
            prereq_icon = "✅" if prereq_status == "completed" else "⚠️"
            date_str = a["appointment_date"][:10]

            lines.append(
                f"📅 *{date_str}* — Dr. {doc.get('name', 'N/A')} ({doc.get('specialty', '')})\n"
                f"   🏥 {a.get('hospital', doc.get('hospital', 'N/A'))}\n"
                + (f"   {prereq_icon} Prerequisites: {', '.join(prereqs)}" if prereqs else "")
            )

        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("Sorry, couldn't fetch appointments. Please try again.")
