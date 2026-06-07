import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# AI APIs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# App
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
DAILY_BRIEFING_HOUR = int(os.getenv("DAILY_BRIEFING_HOUR", "7"))
CRON_SECRET = os.getenv("CRON_SECRET")

SESSION_SECRET = os.getenv("SESSION_SECRET", "")
if not SESSION_SECRET:
    import logging
    logging.getLogger(__name__).critical("SESSION_SECRET env var is not set — sessions will not work")

# ABDM Sandbox (Sprint 2)
ABDM_CLIENT_ID = os.getenv("ABDM_CLIENT_ID", "")
ABDM_CLIENT_SECRET = os.getenv("ABDM_CLIENT_SECRET", "")
ABDM_BASE_URL = os.getenv("ABDM_BASE_URL", "https://sandbox.abdm.gov.in/api/v3")
