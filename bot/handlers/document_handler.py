import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from database.queries import get_patient_for_telegram_user, insert_lab_report, insert_medication, get_or_create_doctor

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    ext = os.path.splitext(doc.file_name or "")[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        await update.message.reply_text(
            "I can process PDFs and images (JPG, PNG).\n"
            "Send lab reports, prescriptions, or discharge summaries in those formats."
        )
        return

    await update.message.reply_text("Analysing document...")
    try:
        from ai.document_classifier import classify_document
        from ai.ocr import extract_prescription_from_photo
        from ai.pdf_parser import extract_lab_report_from_pdf

        patient = get_patient_for_telegram_user(str(update.effective_chat.id))
        if not patient:
            await update.message.reply_text("Your Telegram is not linked yet. Use /connect to get started.")
            return
        pid = patient["id"]

        file = await context.bot.get_file(doc.file_id)
        suffix = ext if ext else ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        try:
            doc_type = await classify_document(tmp_path)

            if doc_type == "prescription":
                result = await extract_prescription_from_photo(tmp_path)
                saved, skipped = [], []
                for med in result.get("medications", []):
                    doctor_id = None
                    if result.get("doctor_name"):
                        doc_row = get_or_create_doctor(result["doctor_name"])
                        doctor_id = doc_row["id"] if doc_row else None
                    outcome = insert_medication(pid, doctor_id, {
                        "drug_name": med["drug_name"],
                        "dosage": med.get("dosage", ""),
                        "frequency": med.get("frequency") or "as directed",
                        "timing": med.get("timing"),
                        "route": med.get("route", "oral"),
                        "source_type": "telegram_doc_ocr",
                        "source_raw_text": str(result),
                    })
                    if outcome.get("action") == "duplicate":
                        skipped.append(med["drug_name"])
                    else:
                        saved.append(med["drug_name"])

                lines = []
                if saved:
                    lines.append(f"Prescription saved: {', '.join(saved)}")
                if skipped:
                    lines.append(f"Already on file: {', '.join(skipped)}")
                if not lines:
                    lines.append("No medications found. Check photo quality and try again.")
                await update.message.reply_text("\n".join(lines))

            elif doc_type in ("lab_report", "imaging_report"):
                result = await extract_lab_report_from_pdf(tmp_path)
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
                        "source_type": "telegram_doc_pdf",
                        "source_raw_text": str(result),
                    })
                    saved.append(test["test_name"])
                    if test.get("is_abnormal"):
                        abnormal.append(f"{test['test_name']}: {test['value']} {test.get('unit', '')}")

                lines = [f"{len(saved)} test(s) saved."]
                if abnormal:
                    lines.append("Flagged: " + ", ".join(abnormal))
                    lines.append("Please discuss flagged values with the relevant doctor.")
                await update.message.reply_text("\n".join(lines))

            else:
                await update.message.reply_text(
                    f"Document type detected: {doc_type}. Saved as a reference.\n"
                    "For prescriptions or lab reports, the AI will extract values automatically."
                )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await update.message.reply_text(
            "Couldn't process this document. Check the file quality and try again, "
            "or enter the values manually on getaayu.in."
        )
