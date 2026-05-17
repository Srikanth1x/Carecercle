import json
import os
import tempfile
import fitz
from ai.gemini_client import call_gemini

CLASSIFY_PROMPT = """Look at this medical document and classify it.

Return ONLY valid JSON, no other text:
{
  "type": "prescription" | "lab_report" | "imaging_report" | "discharge_summary" | "vaccination_record" | "other",
  "confidence": 0.0,
  "description": "one short sentence describing the document"
}

Types:
- prescription: doctor's prescription slip with medication names
- lab_report: blood test, urine test, or any quantitative lab results
- imaging_report: echocardiogram, ECG, X-ray, CT, MRI, ultrasound report
- discharge_summary: hospital discharge or admission summary
- vaccination_record: vaccination or immunization certificate
- other: any other medical document"""


async def classify(file_path: str) -> dict:
    """Classify a medical document. file_path can be image or PDF."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        image_path = await _pdf_first_page_image(file_path)
        try:
            raw = await call_gemini(CLASSIFY_PROMPT, image_path=image_path)
        finally:
            try:
                os.unlink(image_path)
            except OSError:
                pass
    else:
        raw = await call_gemini(CLASSIFY_PROMPT, image_path=file_path)

    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"type": "other", "confidence": 0.5, "description": "Could not classify document"}


async def _pdf_first_page_image(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        pix.save(tmp.name)
        tmp.close()
        return tmp.name
    finally:
        doc.close()
