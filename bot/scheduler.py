import asyncio
import logging
import pytz

from config.settings import TIMEZONE, DAILY_BRIEFING_HOUR
from database.auth_queries import get_all_linked_users, get_patient_by_user_id

logger = logging.getLogger(__name__)

_bot = None

def set_bot(bot):
    global _bot
    _bot = bot

async def _send_one_briefing(b, profile):
    try:
        patient = get_patient_by_user_id(profile["user_id"])
        if not patient:
            return
        from ai.briefing_generator import generate_briefing
        text = await generate_briefing(patient)
        await b.send_message(
            chat_id=profile["telegram_chat_id"],
            text=text,
            parse_mode="Markdown"
        )
    except Exception:
        logger.exception("Daily briefing failed for user %s", profile["user_id"])

async def send_daily_briefing(bot=None):
    b = bot or _bot
    if not b:
        return
    users = get_all_linked_users()
    await asyncio.gather(*[_send_one_briefing(b, p) for p in users], return_exceptions=True)

async def _send_one_nudge(b, profile):
    try:
        from datetime import date
        patient = get_patient_by_user_id(profile["user_id"])
        if not patient:
            return
        from database.queries import get_upcoming_appointments
        appts = get_upcoming_appointments(patient["id"])
        tz = pytz.timezone(TIMEZONE)
        today = date.today()
        for appt in appts:
            appt_date = date.fromisoformat(appt["appointment_date"][:10])
            days_away = (appt_date - today).days
            if days_away <= 14 and appt.get("prerequisite_status") == "pending" and appt.get("prerequisites"):
                prereqs = ", ".join(appt["prerequisites"])
                msg = (
                    f"📌 TASK REMINDER\n\n"
                    f"Dr. {appt.get('doctors', {}).get('name', 'appointment')} is in {days_away} days.\n"
                    f"Prerequisites needed: {prereqs}\n\n"
                    "These haven't been done yet. Please schedule them soon."
                )
                await b.send_message(chat_id=profile["telegram_chat_id"], text=msg)
    except Exception:
        logger.exception("Nudge check failed for user %s", profile["user_id"])

async def check_task_nudges(bot=None):
    b = bot or _bot
    if not b:
        return
    users = get_all_linked_users()
    await asyncio.gather(*[_send_one_nudge(b, p) for p in users], return_exceptions=True)

async def _check_one_silence(b, profile):
    try:
        patient = get_patient_by_user_id(profile["user_id"])
        if not patient:
            return
        from database.queries import get_recent_care_events
        events = get_recent_care_events(patient["id"], hours=48)
        if not events:
            await b.send_message(
                chat_id=profile["telegram_chat_id"],
                text="⚠️ No caregiver updates in 48+ hours. Please check in with the caregiver."
            )
    except Exception:
        logger.exception("Silence check failed for user %s", profile["user_id"])

async def check_silence(bot=None):
    b = bot or _bot
    if not b:
        return
    users = get_all_linked_users()
    await asyncio.gather(*[_check_one_silence(b, p) for p in users], return_exceptions=True)

def start_scheduler(bot):
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    set_bot(bot)
    tz = pytz.timezone(TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(send_daily_briefing, CronTrigger(hour=DAILY_BRIEFING_HOUR, minute=0, timezone=tz))
    scheduler.add_job(check_task_nudges, CronTrigger(hour=9, minute=0, timezone=tz))
    scheduler.add_job(check_silence, CronTrigger(hour=20, minute=0, timezone=tz))
    scheduler.start()
    return scheduler
