import json
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

async def extract_prescription_from_photo(image_path: str) -> dict:
    raw = await call_gemini(PROMPT, image_path=image_path)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
