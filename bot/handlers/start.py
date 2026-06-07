from telegram import Update
from telegram.ext import ContextTypes

WELCOME = """*Welcome to Aayu* -- AI health coordination for Indian families.

I help you remotely manage your parent's health from anywhere.

*Step 1 -- Create your account*
Go to getaayu.in, register, and set up your patient's profile.

*Step 2 -- Link Telegram*
Send /connect here and enter your email + password.

*Once connected you can:*
- Send a prescription photo -- I extract and store all medicines
- Send a lab report PDF -- I flag abnormal values instantly
- Send a voice note or text -- I parse and record it as a care event
- Type /summary -- get the current health snapshot
- Type /sos -- instant emergency card with meds list and contacts

*Commands*
/connect -- Link your Aayu account
/summary -- Health snapshot: meds, labs, alerts
/meds -- All active medications
/labs -- Recent lab results
/appointments -- Upcoming appointments
/briefing -- Today's AI briefing
/check -- Drug interaction check
/addappointment -- Add a new appointment
/sos -- EMERGENCY crisis card
/disconnect -- Unlink account
/help -- Show this message

You receive a personalised *7 AM daily briefing* automatically once connected.

Questions? Email srikanthkarkampally01@gmail.com"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode="Markdown")
