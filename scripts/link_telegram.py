"""
Pre-flight fix: link your real Telegram chat_id to your CareCircle account.

How to get your Telegram chat_id:
  1. Open Telegram
  2. Message @userinfobot
  3. It replies instantly with "Id: 123456789" — that number is your chat_id

Usage:
  python scripts/link_telegram.py <your_telegram_chat_id>

Example:
  python scripts/link_telegram.py 987654321
"""

import sys
from supabase import create_client

SUPABASE_URL = "https://ajcawktfrjbtvhlehffb.supabase.co"
SUPABASE_SERVICE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFqY2F3a3RmcmpidHZobGVoZmZiIiwicm9sZSI6"
    "InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3ODM5OTU2MSwiZXhwIjoyMDkzOTc1NTYxfQ."
    "SLlNYli9pjw_fh0A5PPuUJpwEy6Xa7QbUYeME8MjPBI"
)
USER_ID = "9dbd49ff-acdf-480c-81e2-59b0ed776270"

if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(1)

chat_id = sys.argv[1].strip()
if not chat_id.lstrip("-").isdigit():
    print(f"Error: '{chat_id}' doesn't look like a valid Telegram chat_id (should be a number)")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Check if user_profile exists
existing = client.table("user_profiles").select("*").eq("user_id", USER_ID).execute()

if existing.data:
    result = client.table("user_profiles").update(
        {"telegram_chat_id": chat_id}
    ).eq("user_id", USER_ID).execute()
    print(f"Updated telegram_chat_id to {chat_id} for user {USER_ID}")
else:
    result = client.table("user_profiles").insert(
        {"user_id": USER_ID, "telegram_chat_id": chat_id}
    ).execute()
    print(f"Created user_profile with telegram_chat_id={chat_id} for user {USER_ID}")

# Verify
verify = client.table("user_profiles").select("telegram_chat_id").eq("user_id", USER_ID).execute()
print(f"Verified in DB: telegram_chat_id = {verify.data[0]['telegram_chat_id']}")
print("\nDone. Now send /summary to @GetAayuBot to test.")
