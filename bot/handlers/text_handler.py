from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, insert_care_event

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text.startswith("/"):
        return

    await update.message.reply_text("📝 Processing caregiver update...")
    try:
        from ai.text_parser import parse_caregiver_text

        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        pid = patient["id"]

        result = await parse_caregiver_text(text)

        for event in result.get("events", []):
            insert_care_event(pid, {
                "event_type": event["type"],
                "event_description": event["description"],
                "reported_by": "caregiver",
                "source_type": "text_message",
                "source_language": result.get("language", "en"),
                "source_raw_text": text,
                "severity": event.get("severity", "normal"),
            })

        events = result.get("events", [])
        alerts = result.get("alerts", [])

        if not events:
            await update.message.reply_text(
                "I only record health updates.\n\n"
                "Try something like:\n"
                "- \"Dad took Metformin at 8am\"\n"
                "- \"BP was 138/88 this morning\"\n"
                "- \"Skipped evening dose, feeling dizzy\"\n\n"
                "Use /help to see all commands."
            )
            return

        if alerts:
            reply = "Update recorded.\n\n" + "\n".join(alerts)
        else:
            reply = f"Update recorded. {len(events)} event(s) saved."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            "❌ Couldn't process the update. Please try again."
        )
