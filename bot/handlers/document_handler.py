import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, insert_lab_report

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Please send lab reports as PDF files.")
        return

    await update.message.reply_text("🔬 Processing lab report...")
    try:
        from ai.pdf_parser import extract_lab_report_from_pdf

        file = await context.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        try:
            result = await extract_lab_report_from_pdf(tmp_path)
        finally:
            os.unlink(tmp_path)

        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        pid = patient["id"]

        saved, abnormal = [], []
        for test in result.get("tests", []):
            insert_lab_report(pid, {
                "test_name": test["test_name"],
                "test_value": str(test["value"]),
                "unit": test.get("unit"),
                "reference_range": test.get("reference_range"),
                "is_abnormal": test.get("is_abnormal", False),
                "test_date": result.get("date") or __import__("datetime").date.today().isoformat(),
                "lab_name": result.get("lab_name"),
                "source_type": "pdf_extract",
                "source_raw_text": str(result),
            })
            saved.append(test["test_name"])
            if test.get("is_abnormal"):
                abnormal.append(f"⚠️ {test['test_name']}: {test['value']} {test.get('unit', '')} (ref: {test.get('reference_range', 'N/A')})")

        lines = [f"🔬 Lab Report Processed: {len(saved)} test(s) saved.\n"]
        for s in saved:
            icon = "⚠️" if s in [a.split(":")[0].replace("⚠️ ", "") for a in abnormal] else "✅"
            lines.append(f"{icon} {s}")

        if abnormal:
            lines.append("\n⚠️ Flagged for review — please discuss with the relevant doctor.")

        await update.message.reply_text("\n".join(lines))

    except Exception as e:
        await update.message.reply_text(
            "❌ I couldn't process this PDF automatically. "
            "I've saved the receipt. Please try again or enter values manually."
        )
