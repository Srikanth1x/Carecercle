import json
import os
import re
import tempfile
from ai.gemini_client import call_gemini

PROMPT = """You are a medical document parser. Extract medication information from this prescription image.

Return ONLY valid JSON, no other text:
{
  "medications": [
    {
      "drug_name": "exact drug name as written",
      "dosage": "e.g., 500mg",
      "frequency": "e.g., twice daily",
      "timing": "e.g., after meals",
      "duration": "e.g., 30 days or ongoing",
      "route": "oral/injection/topical"
    }
  ],
  "doctor_name": "name if visible",
  "doctor_specialty": "if visible",
  "hospital_name": "if visible",
  "date": "prescription date if visible, YYYY-MM-DD",
  "confidence": 0.0,
  "notes": "anything unclear or partially readable"
}

If any field is unclear or unreadable, set it to null.
Never guess a drug name — if unsure, write what you see and add a note."""


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    # Strip markdown code fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    raw = raw.strip()
    # Find outermost JSON object
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    return json.loads(raw)


async def _pdf_first_page_image(pdf_path: str) -> str:
    import fitz
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        pix.save(tmp.name)
        tmp.close()
        return tmp.name
    finally:
        doc.close()


async def extract_prescription_from_photo(file_path: str) -> dict:
    ext = os.path.splitext(file_path)[1].lower()
    tmp_image = None
    try:
        if ext == ".pdf":
            tmp_image = await _pdf_first_page_image(file_path)
            image_path = tmp_image
        else:
            image_path = file_path

        raw = await call_gemini(PROMPT, image_path=image_path)
        try:
            return _extract_json(raw)
        except Exception:
            return {"medications": [], "notes": f"Could not parse AI response: {raw[:200]}"}
    finally:
        if tmp_image:
            try:
                os.unlink(tmp_image)
            except OSError:
                pass
