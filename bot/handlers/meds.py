from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, get_active_medications

async def meds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💊 Fetching medications...")
    try:
        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        meds_list = get_active_medications(patient["id"])

        if not meds_list:
            await update.message.reply_text("No active medications found.")
            return

        lines = ["💊 *Active Medications*\n"]
        for i, med in enumerate(meds_list, 1):
            doctor_name = med.get("doctors", {}).get("name", "Unknown") if med.get("doctors") else "Unknown"
            lines.append(
                f"{i}. *{med['drug_name']}* {med['dosage']}\n"
                f"   {med['frequency']}, {med.get('timing', '')}\n"
                f"   Purpose: {med.get('purpose', 'N/A')} | Dr. {doctor_name}"
            )

        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Sorry, couldn't fetch medications. Please try again.")
