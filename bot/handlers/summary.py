from telegram import Update
from telegram.ext import ContextTypes
from database.queries import (
    get_patient_for_telegram_user, get_active_medications,
    get_recent_lab_reports, get_active_alerts, get_recent_care_events
)

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📊 Getting current snapshot...")
    try:
        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        pid = patient["id"]

        meds = get_active_medications(pid)
        labs = get_recent_lab_reports(pid, days=30)
        alerts = get_active_alerts(pid)
        events = get_recent_care_events(pid, hours=24)

        abnormal_labs = [l for l in labs if l["is_abnormal"]]
        status_icon = "🚨" if alerts else ("⚠️" if abnormal_labs else "✅")

        lines = [
            f"{status_icon} *Summary -- {patient['full_name']}*\n",
            f"💊 Active medications: {len(meds)}",
            f"🔬 Abnormal lab values: {len(abnormal_labs)}",
            f"🔔 Active alerts: {len(alerts)}",
            f"📝 Events (last 24h): {len(events)}",
        ]

        if alerts:
            lines.append("\n⚠️ *Active Alerts:*")
            for a in alerts[:3]:
                lines.append(f"  • {a['title']}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("Sorry, couldn't get summary. Please try again.")
