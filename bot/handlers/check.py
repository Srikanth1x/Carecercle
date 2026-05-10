from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, get_active_medications

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔍 Running drug interaction analysis on all active medications...")
    try:
        from ai.drug_interaction import check_drug_interactions
        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        meds = get_active_medications(patient["id"])
        result = await check_drug_interactions(patient, meds)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Sorry, couldn't run drug interaction check. Please try again.")
