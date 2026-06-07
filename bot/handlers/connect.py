from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)
from web.auth import supabase_login
from database.auth_queries import set_telegram_chat_id, get_user_profile, get_patient_by_user_id

ASK_EMAIL, ASK_PASSWORD = range(2)

async def connect_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_chat.id)
    profile = get_user_profile(chat_id)
    if profile:
        patient = get_patient_by_user_id(profile["user_id"])
        name = patient["full_name"] if patient else "your patient"
        await update.message.reply_text(
            f"You're already connected and managing {name}.\n"
            "Send /disconnect to unlink this account."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Let's link your Telegram to your Aayu web account.\n\n"
        "First, register at the web dashboard if you haven't yet.\n\n"
        "Please send your email address:"
    )
    return ASK_EMAIL

async def got_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["email"] = update.message.text.strip()
    await update.message.reply_text("Now send your password:")
    return ASK_PASSWORD

async def got_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = context.user_data.get("email")
    password = update.message.text.strip()
    chat_id = str(update.effective_chat.id)

    try:
        await update.message.delete()
    except Exception:
        pass

    await update.message.reply_text("Verifying...")

    result = await supabase_login(email, password)
    if not result:
        await update.message.reply_text(
            "Invalid email or password. Please try /connect again."
        )
        return ConversationHandler.END

    user_id = result["user"]["id"]
    patient = get_patient_by_user_id(user_id)
    if not patient:
        await update.message.reply_text(
            "Account verified, but no patient is linked to it yet.\n"
            "Please log into the web dashboard and add your patient profile first."
        )
        return ConversationHandler.END

    set_telegram_chat_id(user_id, chat_id)
    await update.message.reply_text(
        f"Connected! You're now managing {patient['full_name']} via this bot.\n\n"
        "Try /summary to see the current health status."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Connection cancelled.")
    return ConversationHandler.END

async def disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from database.supabase_client import get_client
    chat_id = str(update.effective_chat.id)
    get_client().table("user_profiles").update(
        {"telegram_chat_id": None}
    ).eq("telegram_chat_id", chat_id).execute()
    await update.message.reply_text("Disconnected. Use /connect to link again.")

def get_connect_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("connect", connect_start)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_email)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=120,
    )
