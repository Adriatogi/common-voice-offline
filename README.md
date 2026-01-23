# Common Voice Offline Telegram Bot

A Telegram bot for contributing voice recordings to Mozilla Common Voice, designed for areas with limited connectivity.

## Features

- **Offline Recording**: Download sentences, go offline, record, upload when back online
- **Multi-language**: English, Spanish, Puno Quechua (configurable)
- **Bot Interface**: English and Spanish UI
- **No Duplicates**: Tracks uploaded sentences so each `/setup` gives fresh ones
- **Persistent**: Sessions survive bot restarts

## Quick Start

### 1. Get Credentials

**Telegram Bot Token:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow prompts
3. Copy the token

**Common Voice API:**
1. Go to https://commonvoice.mozilla.org/settings (add `?feature=papi-credentials` if needed)
2. Create API credentials
3. Save Client ID and Client Secret

### 2. Install

```bash
git clone https://github.com/yourusername/common-voice-offline.git
cd common-voice-offline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

Create `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
CV_CLIENT_ID=your_client_id
CV_CLIENT_SECRET=your_client_secret
```

Edit `config.yaml` to customize languages/limits (optional).

### 4. Run

```bash
python -m bot.main
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/login` | Register with email and username |
| `/setup` | Select language and download sentences |
| `/sentences` | View sentences (`/sentences left` for unrecorded) |
| `/resend` | Resend unrecorded sentences for offline use |
| `/status` | Check recording progress |
| `/upload` | Upload pending recordings |
| `/skip 1,3,5-10` | Skip sentences |
| `/clear` | Clear session and start fresh |
| `/language` | Change bot interface language |
| `/logout` | Clear your data |

## Recording Workflow

1. **Register**: `/login` → enter email → enter username
2. **Get sentences**: `/setup` → pick language → pick count
3. **Go offline** with sentences in your chat history
4. **Record**: Reply to any sentence message with a voice recording
5. **Come online**: Messages auto-deliver, recordings upload

**Re-record**: Just send another voice reply to the same sentence.

## Project Structure

```
common-voice-offline/
├── .env                 # Secrets (gitignored)
├── config.yaml          # Settings (languages, limits)
├── requirements.txt
├── bot/
│   ├── main.py          # Entry point
│   ├── config.py        # Config loader
│   ├── handlers/        # Command handlers
│   ├── services/        # API client
│   ├── database/        # SQLite operations
│   └── i18n/            # Translations
└── data/                # Database (gitignored)
```

## Adding Languages

Edit `config.yaml`:
```yaml
languages:
  en: English
  es: Spanish (Español)
  qxp: Puno Quechua (Qhichwa)
  # add more here
```

## License

MIT
