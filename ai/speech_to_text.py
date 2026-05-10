import json
import base64
from ai.gemini_client import call_gemini
from ai.text_parser import parse_caregiver_text

async def transcribe_and_parse(audio_path: str) -> dict:
    # Gemini Flash supports audio — send as inline data
    import google.generativeai as genai
    from config.settings import GEMINI_API_KEY

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    audio_part = {
        "inline_data": {
            "mime_type": "audio/ogg",
            "data": base64.b64encode(audio_data).decode()
        }
    }

    transcription_prompt = (
        "Transcribe this voice note exactly. It may be in Hindi, English, or Hinglish. "
        "Return ONLY the transcription text, nothing else."
    )

    for attempt in range(2):
        try:
            response = model.generate_content([transcription_prompt, audio_part])
            transcription = response.text.strip()
            break
        except Exception:
            if attempt == 1:
                transcription = "[Could not transcribe audio]"

    parsed = await parse_caregiver_text(transcription)
    parsed["transcription"] = transcription
    return parsed
