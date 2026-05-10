import json
from ai.gemini_client import call_gemini

PROMPT_TEMPLATE = """You are a health event extractor. Parse this caregiver message and extract structured health events.
Auto-detect language (Hindi/English/Hinglish) and parse accordingly.

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

async def parse_caregiver_text(text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(text=text)
    raw = await call_gemini(prompt)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
