import google.generativeai as genai
from config.settings import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def get_model(vision: bool = False):
    return genai.GenerativeModel("gemini-1.5-flash")

async def call_gemini(prompt: str, image_path: str = None) -> str:
    model = get_model()
    for attempt in range(2):
        try:
            if image_path:
                import PIL.Image
                img = PIL.Image.open(image_path)
                response = model.generate_content([prompt, img])
            else:
                response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt == 1:
                raise
    return ""
