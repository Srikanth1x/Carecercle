# CareCircle MVP

AI-powered care coordination for remote family caregivers.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 3. Set up Supabase database
1. Create a free project at supabase.com
2. Go to SQL Editor
3. Run `database/schema.sql` (copy-paste and execute)
4. Run `database/seed.sql` (copy-paste and execute)
5. Copy your project URL and anon key into `.env`

### 4. Get your API keys
- **Telegram Bot Token**: Message @BotFather on Telegram → /newbot
- **Telegram Chat ID**: Message @userinfobot on Telegram to get your chat ID
- **Gemini API Key**: aistudio.google.com (free tier)
- **Anthropic API Key**: console.anthropic.com (existing subscription)

### 5. Run
```bash
python run.py
```

- Telegram bot starts polling
- Web dashboard: http://localhost:8000

## What it does

**Telegram Bot Commands:**
- `/start` — Welcome + setup
- `/summary` — Current health snapshot
- `/meds` — Active medications list
- `/labs` — Recent lab results
- `/appointments` — Upcoming appointments + prerequisites
- `/check` — Drug interaction analysis (Claude AI)
- `/briefing` — Generate today's daily briefing now
- `/sos` — Instant emergency crisis card

**Send anything:**
- 📷 Prescription photo → extracts medications, checks interactions
- 📄 Lab report PDF → extracts values, flags abnormals
- 💬 Text update → parses health events (Hindi/English/Hinglish)
- 🎤 Voice note → transcribes and parses events

**Automated:**
- 7:00 AM daily briefing sent to Telegram
- Smart alerts on drug interactions, abnormal labs, concerning symptoms
- Task nudges for upcoming appointment prerequisites

**Web Dashboard:** http://localhost:8000
- Full health picture: medications, labs, timeline, alerts, appointments
