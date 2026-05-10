from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config.settings import TIMEZONE, DAILY_BRIEFING_HOUR
from database.auth_queries import get_all_linked_users, get_patient_by_user_id

_bot = None

def set_bot(bot):
    global _bot
    _bot = bot

async def send_daily_briefing():
    if not _bot:
        return
    from ai.briefing_generator import generate_briefing
    for profile in get_all_linked_users():
        try:
            patient = get_patient_by_user_id(profile["user_id"])
            if not patient:
                continue
            text = await generate_briefing(patient["id"])
            await _bot.send_message(
                chat_id=profile["telegram_chat_id"],
                text=text,
                parse_mode="Markdown"
            )
        except Exception:
            pass

async def check_task_nudges():
    if not _bot:
        return
    from database.queries import get_upcoming_appointments
    from datetime import datetime
    for profile in get_all_linked_users():
        try:
            patient = get_patient_by_user_id(profile["user_id"])
            if not patient:
                continue
            appts = get_upcoming_appointments(patient["id"])
            for appt in appts:
                days_away = (datetime.fromisoformat(appt["appointment_date"][:10]) - datetime.now()).days
                if days_away <= 14 and appt.get("prerequisite_status") == "pending" and appt.get("prerequisites"):
                    prereqs = ", ".join(appt["prerequisites"])
                    msg = (
                        f"📌 TASK REMINDER\n\n"
                        f"Dr. {appt.get('doctors', {}).get('name', 'appointment')} is in {days_away} days.\n"
                        f"Prerequisites needed: {prereqs}\n\n"
                        "These haven't been done yet. Please schedule them soon."
                    )
                    await _bot.send_message(chat_id=profile["telegram_chat_id"], text=msg)
        except Exception:
            pass

async def check_silence():
    if not _bot:
        return
    from database.queries import get_recent_care_events
    for profile in get_all_linked_users():
        try:
            patient = get_patient_by_user_id(profile["user_id"])
            if not patient:
                continue
            events = get_recent_care_events(patient["id"], hours=48)
            if not events:
                await _bot.send_message(
                    chat_id=profile["telegram_chat_id"],
                    text="⚠️ No caregiver updates in 48+ hours. Please check in with the caregiver."
                )
        except Exception:
            pass

def start_scheduler(bot):
    set_bot(bot)
    tz = pytz.timezone(TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(send_daily_briefing, CronTrigger(hour=DAILY_BRIEFING_HOUR, minute=0, timezone=tz))
    scheduler.add_job(check_task_nudges, CronTrigger(hour=9, minute=0, timezone=tz))
    scheduler.add_job(check_silence, CronTrigger(hour=20, minute=0, timezone=tz))
    scheduler.start()
    return scheduler
