import json
import re
from ai.gemini_client import call_gemini

PROMPT_TEMPLATE = """You are a health event extractor. Parse this caregiver message and extract structured health events.
Auto-detect language (Hindi/English/Hinglish) and parse accordingly.

If the message contains NO health-related information (e.g. greetings, random words), return:
{{"language": "en", "events": [], "alerts": []}}

Return ONLY valid JSON:
{{
  "language": "en/hi/hinglish",
  "events": [
    {{
      "type": "symptom|meal|medication_taken|medication_missed|vital|observation",
      "description": "plain English description",
      "severity": "normal|attention|urgent"
    }}
  ],
  "alerts": ["plain language alert messages if any events are concerning, empty list if all normal"]
}}

Message: {text}

Rules:
- "attention" if symptom relates to a known condition (diabetes, hypertension, cardiac)
- "urgent" if chest pain, severe dizziness, loss of consciousness, very high/low BP or sugar
- alerts list should be plain language, suitable for a non-medical person"""

def _parse_raw(raw: str) -> dict:
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw).strip()
    start = raw.find("{"); end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return json.loads(raw)

async def parse_caregiver_text(text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(text=text)
    raw = await call_gemini(prompt)
    try:
        return _parse_raw(raw)
    except Exception:
        return {"language": "en", "events": [], "alerts": []}
