from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import TELEGRAM_BOT_TOKEN
from bot.handlers.start import start, help_command
from bot.handlers.summary import summary
from bot.handlers.meds import meds
from bot.handlers.labs import labs
from bot.handlers.appointments import appointments
from bot.handlers.check import check
from bot.handlers.sos import sos
from bot.handlers.briefing import briefing
from bot.handlers.connect import get_connect_conversation, disconnect
from bot.handlers.add_appointment import get_add_appointment_conversation
from bot.handlers.photo_handler import handle_photo
from bot.handlers.document_handler import handle_document
from bot.handlers.voice_handler import handle_voice
from bot.handlers.text_handler import handle_text

def create_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handlers must be registered before generic text handler
    app.add_handler(get_connect_conversation())
    app.add_handler(get_add_appointment_conversation())
    app.add_handler(CommandHandler("disconnect", disconnect))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("meds", meds))
    app.add_handler(CommandHandler("labs", labs))
    app.add_handler(CommandHandler("appointments", appointments))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("sos", sos))
    app.add_handler(CommandHandler("briefing", briefing))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.PDF | filters.Document.IMAGE, handle_document))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app

def run_bot():
    app = create_app()
    print("Aayu bot is running...")
    app.run_polling(drop_pending_updates=True)
