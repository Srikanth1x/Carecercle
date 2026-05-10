import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, insert_medication, insert_alert

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🖼️ Processing prescription photo...")
    try:
        from ai.ocr import extract_prescription_from_photo
        from ai.drug_interaction import check_drug_interactions
        from database.queries import get_active_medications, get_doctor_by_name

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        try:
            result = await extract_prescription_from_photo(tmp_path)
        finally:
            os.unlink(tmp_path)

        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        pid = patient["id"]

        saved, skipped = [], []
        for med in result.get("medications", []):
            doctor_id = None
            if result.get("doctor_name"):
                doc = get_doctor_by_name(result["doctor_name"])
                doctor_id = doc["id"] if doc else None

            outcome = insert_medication(pid, doctor_id, {
                "drug_name": med["drug_name"],
                "dosage": med.get("dosage", ""),
                "frequency": med.get("frequency", ""),
                "timing": med.get("timing"),
                "route": med.get("route", "oral"),
                "source_type": "photo_ocr",
                "source_raw_text": str(result),
            })
            if outcome["action"] == "duplicate":
                skipped.append(med["drug_name"])
            else:
                saved.append(med["drug_name"])

        msg_lines = []
        if saved:
            msg_lines.append(f"✅ Prescription recorded: {', '.join(saved)} added to Dad's medication list.")
        if skipped:
            msg_lines.append(f"ℹ️ Already on file (no change): {', '.join(skipped)}")

        if not msg_lines:
            msg_lines.append("⚠️ No medications could be extracted. Please check the photo quality.")

        if result.get("notes"):
            msg_lines.append(f"\n📝 Note: {result['notes']}")

        await update.message.reply_text("\n".join(msg_lines))

        if saved:
            all_meds = get_active_medications(pid)
            interaction_result = await check_drug_interactions(patient, all_meds)
            if "INTERACTION" in interaction_result.upper() or "⚠️" in interaction_result:
                await update.message.reply_text(interaction_result, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(
            "❌ I couldn't process this prescription automatically. "
            "I've noted the receipt and will try again. Please also consider entering the medicines manually via text."
        )
