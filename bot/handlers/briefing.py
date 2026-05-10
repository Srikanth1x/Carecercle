from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user

async def briefing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📋 Generating today's briefing...")
    try:
        from ai.briefing_generator import generate_briefing
        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        result = await generate_briefing(patient["id"])
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("Sorry, couldn't generate briefing. Please try again.")
