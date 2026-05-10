from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Welcome to CareCircle!\n\n"
        "I help you remotely manage a loved one's health.\n\n"
        "To get started:\n"
        "1. Register at the CareCircle website\n"
        "2. Send /connect here to link your Telegram account\n\n"
        "Once connected, you can:\n"
        "• Send a prescription photo → I'll extract and store the medicines\n"
        "• Send a lab report PDF → I'll extract values and flag abnormals\n"
        "• Send a text update from the caregiver → I'll parse and store it\n"
        "• Send a voice note → I'll transcribe and store it\n\n"
        "Type /help to see all commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 *CareCircle Commands*\n\n"
        "/connect — Link your Telegram to your web account\n"
        "/disconnect — Unlink your account\n\n"
        "/summary — Current snapshot: meds, vitals, recent events\n"
        "/meds — List all active medications\n"
        "/labs — Recent lab results\n"
        "/appointments — Upcoming appointments\n"
        "/check — Run drug interaction analysis\n"
        "/briefing — Get today's daily briefing now\n"
        "/sos — EMERGENCY: instant crisis card\n"
        "/help — Show this help\n\n"
        "Or just send me a photo, PDF, voice note, or text!",
        parse_mode="Markdown"
    )
