import asyncio
import google.generativeai as genai
from config.settings import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def get_model():
    return genai.GenerativeModel("gemini-2.0-flash")

async def call_gemini(prompt: str, image_path: str = None) -> str:
    model = get_model()

    def _sync_call():
        if image_path:
            import PIL.Image
            img = PIL.Image.open(image_path)
            return model.generate_content([prompt, img])
        return model.generate_content(prompt)

    for attempt in range(3):
        try:
            response = await asyncio.to_thread(_sync_call)
            return response.text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                raise RuntimeError("Gemini API quota exceeded. Please enable billing at aistudio.google.com to continue using AI features.")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    return ""
