import json
import os
import re
import tempfile
import fitz  # PyMuPDF
from ai.gemini_client import call_gemini

PROMPT = """You are a medical document parser. Extract all measurable values from this document.

This may be a lab report, echocardiogram, imaging report, or any hospital document with test results.

Return ONLY valid JSON, no other text:
{
  "tests": [
    {
      "test_name": "e.g., EF%, Fasting Blood Sugar, LV Dimensions",
      "value": "e.g., 55, 180, 4.8",
      "unit": "e.g., %, mg/dL, cm",
      "reference_range": "e.g., 55-70%, 70-110 mg/dL",
      "is_abnormal": true/false
    }
  ],
  "date": "YYYY-MM-DD if found, else null",
  "lab_name": "hospital or lab name if found, else null",
  "patient_name": "patient name if found, else null",
  "document_type": "lab_report / echocardiogram / imaging / discharge_summary / other",
  "confidence": 0.0,
  "notes": "anything unclear or important not captured above"
}

If no measurable values are found, return an empty tests array with a note explaining what the document contains.
Never guess values — if unclear, set is_abnormal to false and add a note."""


def _sparse(text: str) -> bool:
    return len(text.strip()) < 150


def _parse_raw(raw: str) -> dict:
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


async def _parse_text(text: str) -> dict:
    prompt = PROMPT + f"\n\nDocument text:\n{text[:5000]}"
    raw = await call_gemini(prompt)
    return _parse_raw(raw)


async def _parse_as_images(doc: fitz.Document) -> dict:
    results = []
    tmp_paths = []
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            pix.save(tmp.name)
            tmp.close()
            tmp_paths.append(tmp.name)

        # Send first page (most info is usually on page 1)
        raw = await call_gemini(PROMPT, image_path=tmp_paths[0])
        result = _parse_raw(raw)

        # If multi-page and first page returned few tests, try page 2
        if len(tmp_paths) > 1 and len(result.get("tests", [])) < 2:
            raw2 = await call_gemini(PROMPT, image_path=tmp_paths[1])
            result2 = _parse_raw(raw2)
            result["tests"] = result.get("tests", []) + result2.get("tests", [])
            if not result.get("notes") and result2.get("notes"):
                result["notes"] = result2["notes"]

        return result
    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass


async def extract_lab_report_from_pdf(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    try:
        text = "\n".join(page.get_text() for page in doc)
        if _sparse(text):
            return await _parse_as_images(doc)
        return await _parse_text(text)
    finally:
        doc.close()
