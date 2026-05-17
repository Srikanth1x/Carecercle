import asyncio
import base64
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

# ---------------------------------------------------------------------------
# Primary: Groq (free tier, no billing required)
# Fallback: Gemini (if GEMINI_API_KEY is set and Groq fails)
# ---------------------------------------------------------------------------

GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def _call_groq_sync(prompt: str, image_path: str = None) -> str:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    if image_path:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = image_path.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else "image/jpeg"
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
    else:
        content = prompt

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": content}],
        temperature=0.1,
    )
    return response.choices[0].message.content


def _call_gemini_sync(prompt: str, image_path: str = None) -> str:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    if image_path:
        import PIL.Image
        img = PIL.Image.open(image_path)
        response = model.generate_content([prompt, img])
    else:
        response = model.generate_content(prompt)
    return response.text


async def call_gemini(prompt: str, image_path: str = None) -> str:
    """Call AI — tries Groq first (free), falls back to Gemini if needed."""

    if GROQ_API_KEY:
        for attempt in range(3):
            try:
                return await asyncio.to_thread(_call_groq_sync, prompt, image_path)
            except Exception as e:
                msg = str(e)
                if "429" in msg or "rate_limit" in msg.lower():
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise RuntimeError("Groq API rate limit hit. Try again in a minute.")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

    if GEMINI_API_KEY:
        for attempt in range(3):
            try:
                return await asyncio.to_thread(_call_gemini_sync, prompt, image_path)
            except Exception as e:
                msg = str(e)
                if "429" in msg or "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                    raise RuntimeError("Gemini API quota exceeded. Add a free Groq API key at console.groq.com.")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

    raise RuntimeError("No AI API key configured. Set GROQ_API_KEY in environment variables.")
