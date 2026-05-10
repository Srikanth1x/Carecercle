from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, get_recent_lab_reports

async def labs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔬 Fetching recent lab results...")
    try:
        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        reports = get_recent_lab_reports(patient["id"])

        if not reports:
            await update.message.reply_text("No recent lab reports found.")
            return

        lines = ["🔬 *Recent Lab Results*\n"]
        for r in reports:
            flag = "⚠️" if r["is_abnormal"] else "✅"
            lines.append(
                f"{flag} *{r['test_name']}*: {r['test_value']} {r.get('unit', '')}\n"
                f"   Ref: {r.get('reference_range', 'N/A')} | Date: {r['test_date']}"
            )

        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("Sorry, couldn't fetch lab results. Please try again.")
