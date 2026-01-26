# Common Voice Offline

A Telegram bot for contributing voice recordings to Mozilla Common Voice, designed for areas with limited connectivity. Includes a public dashboard for viewing contribution stats.

**Bot**: [@cv_offline_bot](https://t.me/cv_offline_bot)

## Features

- **Offline Recording**: Download sentences, go offline, record, upload when back online
- **Multi-language**: English, Spanish, Puno Quechua (configurable)
- **Bot Interface**: English and Spanish UI
- **No Duplicates**: Tracks uploaded sentences so each `/setup` gives fresh ones
- **Public Dashboard**: View aggregate stats and personal contribution history
- **Persistent**: Sessions survive bot restarts

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram Bot   │────▶│    Supabase     │◀────│    Dashboard    │
│  (Python)       │     │   (Postgres)    │     │    (React)      │
│  Railway        │     │                 │     │    Vercel       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Start

### 1. Get Credentials

**Telegram Bot Token:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow prompts
3. Copy the token

**Common Voice API:**
1. Go to https://commonvoice.mozilla.org/settings
2. Create API credentials (add `?feature=papi-credentials` to URL if not visible)
3. Save Client ID and Client Secret

**Supabase:**
1. Create a project at [supabase.com](https://supabase.com)
2. Go to Settings → API
3. Copy the Project URL and both keys (anon + service_role)

### 2. Set Up Database

1. In Supabase, go to SQL Editor
2. Paste contents of `supabase/schema.sql`
3. Click Run

### 3. Install Bot

```bash
git clone https://github.com/Adriatogi/common-voice-offline.git
cd common-voice-offline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure

Create `.env` in the project root:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Common Voice API
CV_CLIENT_ID=your_client_id
CV_CLIENT_SECRET=your_client_secret

# Supabase (bot uses service_role key)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

# Dashboard (uses anon key - safe to expose)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

### 5. Run Locally

**Bot:**
```bash
python -m bot.main
```

**Dashboard:**
```bash
cd dashboard
npm install
npm run dev
```

## Deployment

### Bot → Railway (~$5/month)

1. Push code to GitHub
2. Create project at [railway.app](https://railway.app)
3. Connect your GitHub repo
4. Add environment variables (Settings → Variables)
5. Railway auto-deploys on every push

### Dashboard → Vercel (free)

1. Create project at [vercel.com](https://vercel.com)
2. Connect your GitHub repo
3. Set root directory to `dashboard`
4. Add environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
5. Deploy

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/login` | Register with email and username |
| `/setup` | Select language and download sentences |
| `/status` | Check recording progress + your User ID |
| `/sentences` | View sentences (`/sentences left` for unrecorded) |
| `/resend` | Resend unrecorded sentences |
| `/upload` | Upload pending recordings |
| `/skip 1,3,5-10` | Skip sentences |
| `/clear` | Clear session and start fresh |
| `/language` | Change bot interface language |
| `/logout` | Clear your data |

## Recording Workflow

1. `/login` → enter email → enter username (save your User ID!)
2. `/setup` → pick language → pick count
3. Go offline with sentences in chat history
4. Reply to sentence messages with voice recordings
5. Come online → `/upload` to submit

## Project Structure

```
common-voice-offline/
├── bot/
│   ├── main.py          # Entry point
│   ├── config.py        # Config loader
│   ├── handlers/        # Command handlers
│   ├── services/        # CV API client
│   ├── database/        # Supabase operations
│   └── i18n/            # Translations (en, es)
├── dashboard/           # React + Vite
│   ├── src/
│   │   ├── pages/       # Home, UserStats
│   │   └── lib/         # Supabase client
│   └── package.json
├── supabase/
│   └── schema.sql       # Database schema
├── config.yaml          # Languages, limits
├── requirements.txt
└── .env                 # Secrets (gitignored)
```

## Database (Supabase)

### Tables

- `users` - Registered bot users
- `sessions` - Active recording sessions
- `sentences` - Sentences assigned to users
- `recordings` - Voice recordings
- `seen_sentences` - Tracks completed sentences

### Security (Row Level Security)

| Data | Public (Dashboard) | Private |
|------|-------------------|---------|
| User ID | ✅ | |
| Username | ✅ | |
| Recording counts | ✅ | |
| Email | | ✅ |
| Telegram ID | | ✅ |

- **Bot** uses `service_role` key (bypasses RLS)
- **Dashboard** uses `anon` key (read-only via RLS)

## Adding Languages

Edit `config.yaml`:

```yaml
languages:
  en: English
  es: Spanish (Español)
  qxp: Puno Quechua (Qhichwa)
  # add more language codes here
```

## License

MIT
