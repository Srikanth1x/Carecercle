import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, insert_care_event

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🎤 Transcribing voice note...")
    try:
        from ai.speech_to_text import transcribe_and_parse

        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        try:
            result = await transcribe_and_parse(tmp_path)
        finally:
            os.unlink(tmp_path)

        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        pid = patient["id"]

        for event in result.get("events", []):
            insert_care_event(pid, {
                "event_type": event["type"],
                "event_description": event["description"],
                "reported_by": "caregiver",
                "source_type": "voice_note",
                "source_language": result.get("language", "en"),
                "source_raw_text": result.get("transcription", ""),
                "severity": event.get("severity", "normal"),
            })

        reply = f"🎤 Transcription: '{result.get('transcription', '')}'\n\nExtracted: {len(result.get('events', []))} event(s) recorded."

        alerts = result.get("alerts", [])
        if alerts:
            reply += "\n\n" + "\n".join(alerts)

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            "❌ Couldn't process the voice note. Please try sending it as text instead."
        )
