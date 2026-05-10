import json
import fitz  # PyMuPDF
from ai.gemini_client import call_gemini

PROMPT_TEMPLATE = """You are a medical lab report parser. Extract all test results from the following lab report text.

Return ONLY valid JSON, no other text:
{{
  "tests": [
    {{
      "test_name": "e.g., Fasting Blood Sugar",
      "value": "e.g., 180",
      "unit": "e.g., mg/dL",
      "reference_range": "e.g., 70-110 mg/dL",
      "is_abnormal": true/false
    }}
  ],
  "date": "YYYY-MM-DD if found",
  "lab_name": "lab or hospital name if found",
  "patient_name": "if found",
  "confidence": 0.0,
  "notes": "anything unclear"
}}

Lab report text:
{text}"""

async def extract_lab_report_from_pdf(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    prompt = PROMPT_TEMPLATE.format(text=text[:4000])
    raw = await call_gemini(prompt)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
