# Common Voice Offline Telegram Bot

A Telegram bot that allows users to contribute voice recordings to Mozilla Common Voice, with offline capability for use in remote areas with limited connectivity.

## Features

- **Offline Recording**: Download sentences, go offline, record voice messages, and upload when back online
- **Scripted Speech**: Contribute to Common Voice by reading sentences aloud
- **Multi-language Support**: English, Spanish, and Puno Quechua (qxp)
- **Persistent Storage**: Sessions survive bot restarts - your recordings are safe
- **Automatic Upload**: Recordings upload automatically when you're online
- **Admin Mode**: Single API credentials manage all contributors

## How It Works

1. **Register**: Users provide email and username
2. **Setup**: Select language and download sentences
3. **Record Offline**: Go to remote areas, record voice messages with sentence numbers
4. **Upload**: When back online, recordings are uploaded to Common Voice

```
User goes offline with sentences in chat history
         ↓
Records voice messages: "#1" + voice, "#2" + voice, etc.
         ↓
Messages queued on phone
         ↓
Returns online → Messages delivered to bot → Uploaded to Common Voice
```

## Prerequisites

- Python 3.10+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Common Voice API credentials (admin account - see below)

## Getting Common Voice API Credentials

1. Go to https://commonvoice.mozilla.org
2. Log in with your Mozilla account
3. Navigate to Settings → API
   - Note: Add `?feature=papi-credentials` to the URL if the API tab isn't visible
4. Create new API credentials
5. Save your **Client ID** and **Client Secret**

These credentials are used by the bot admin. Users don't need their own API credentials.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/common-voice-offline.git
cd common-voice-offline
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create your `.env` file:
```bash
cp .env.example .env
```

5. Edit `.env` with your credentials:
```bash
# Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Get from Common Voice settings (admin credentials)
CV_CLIENT_ID=your_cv_client_id
CV_CLIENT_SECRET=your_cv_client_secret
```

6. (Optional) Edit `config.yaml` to customize languages, sentence limits, etc.

7. Run the bot:
```bash
python -m bot.main
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/login` | Register with email and username |
| `/setup` | Select language and download sentences |
| `/sentences` | View your assigned sentences |
| `/status` | Check your recording progress |
| `/upload` | Manually upload pending recordings |
| `/logout` | Clear your session |
| `/help` | Show help message |

## Detailed Usage Guide

### Step 1: Start the Bot

Open Telegram and search for your bot (the one you created with @BotFather). Send `/start` to see the welcome message.

### Step 2: Register

Send `/login` to begin registration. The bot will ask for:

1. **Email** - Your email for the Common Voice profile
2. **Username** - Your display name in the dataset

```
You: /login
Bot: Please enter your email address:
You: myemail@example.com
Bot: Please enter a username:
You: MyUsername
Bot: ✅ Registration successful!
```

### Step 3: Download Sentences

Send `/setup` to configure your recording session:

1. **Select Language** - Choose from English, Spanish, or Puno Quechua
2. **Choose Sentence Count** - How many sentences to download (10, 25, 50, or 100)

The bot will then send all your sentences as messages in the chat. **These will stay in your chat history so you can see them offline!**

```
You: /setup
Bot: Please select your language:
     [English (en)] [Spanish (es)] [Puno Quechua (qxp)]
You: English (en)
Bot: How many sentences would you like? (max 100)
     [10] [25] [50] [100]
You: 50
Bot: Fetching 50 sentences in English...
Bot: ✅ Downloaded 50 sentences!

Bot: #1 The quick brown fox jumps over the lazy dog.
Bot: #2 She sells seashells by the seashore.
... (all 50 sentences)
```

### Step 4: Record (Can Be Done Offline!)

This is where the offline magic happens. You can now:
- Go to a remote village with no internet
- Open the Telegram chat and scroll through your sentences
- Record voice messages for each sentence

**How to record:**

1. Type `#1` (or any sentence number) and send
2. Bot shows the sentence
3. Send a voice message reading the sentence

```
You: #1
Bot: #1: The quick brown fox jumps over the lazy dog.
     🎤 Send a voice message now to record this sentence.
You: [Voice message]
Bot: ✅ Recorded #1!
```

**When offline:** Your messages queue on your phone. When you return to an area with connectivity, Telegram automatically delivers them to the bot.

### Step 5: Check Progress

Use `/status` to see your recording progress:

```
You: /status
Bot: 📊 Your Status

     User: MyUsername
     Language: English
     Sentences: 50

     Recording Progress:
     • Total recorded: 32/50
     • Pending upload: 5
     • Uploaded: 26
     • Failed: 1
```

Use `/sentences` to see all your sentences with their recording status.

### Step 6: Upload Pending Recordings

If some recordings are pending (maybe you recorded offline and just came online), use `/upload`:

```
You: /upload
Bot: 📤 Uploading 5 recordings...
Bot: ✅ Successfully uploaded 5 recordings to Common Voice!
```

### Step 7: Logout (Optional)

When you're done, use `/logout` to clear your data:

```
You: /logout
Bot: ✅ You have been logged out.
```

**Tip:** To re-record a sentence, just send a new voice message with the same `#N` - it will replace the previous recording.

## Project Structure

```
common-voice-offline/
├── requirements.txt
├── .env.example             # Secrets template
├── config.yaml              # Application settings (languages, limits, etc.)
├── README.md
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Loads .env and config.yaml
│   ├── handlers/
│   │   ├── __init__.py      # Auto-imports all handlers
│   │   ├── registry.py      # Handler registration with priority
│   │   ├── start.py         # /start, /help
│   │   ├── login.py         # /login conversation
│   │   ├── setup.py         # /setup conversation
│   │   ├── recording.py     # Voice message handling
│   │   └── status.py        # /status, /sentences, /upload, /logout
│   ├── services/
│   │   └── cv_api.py        # Common Voice API client
│   └── database/
│       └── db.py            # SQLite operations
└── data/                    # Database files (gitignored)
```

## Handler Registration

Handlers use a decorator-based auto-discovery system. Each handler registers itself with a priority:

```python
from bot.handlers.registry import handler

handler(priority=0)(CommandHandler("start", start_command))
```

**Priority ranges** (lower = checked first):
- `0-19`: Core commands (start, help)
- `20-39`: Conversations (login, setup)
- `40-59`: Other commands (status, upload, logout)
- `60-79`: Message handlers (voice, text)

Order matters because `python-telegram-bot` uses the first matching handler. Generic message handlers must be registered last, or they'd catch everything.

## Configuration

**`.env`** - Secrets only (gitignored):
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
CV_CLIENT_ID=your_cv_client_id
CV_CLIENT_SECRET=your_cv_client_secret
```

**`config.yaml`** - Application settings:
```yaml
cv_api:
  base_url: https://api.commonvoice.mozilla.org
  token_expiry_buffer_seconds: 300

languages:
  en: English
  es: Spanish (Español)
  qxp: Puno Quechua (Qhichwa)

sentences:
  max: 100
  default: 50
```

## Security Notes

- Bot uses **admin API credentials** to upload on behalf of all users
- Users only provide email + username (no passwords)
- The `userId` returned by Common Voice is used to attribute contributions
- All uploads go through the community validation process

## Supported Languages

- English (`en`)
- Spanish (`es`)
- Puno Quechua (`qxp`)

To add more languages, edit `languages` in `config.yaml`.

## Troubleshooting

### "Failed to create user" error
- Email or username may already exist in Common Voice
- Try a different email/username combination

### "No sentences available" for my language
- The language may not have sentences in Common Voice yet
- Check if the language code is correct in `config.yaml`
- Try a different language to test the bot

### Recordings show as "failed"
- Check `/status` for error messages
- Common issues:
  - Audio too long
  - Token expired (use `/upload` to retry with fresh token)
  - Network issues (retry when connection is stable)

### Bot doesn't respond
- Make sure the bot is running (`python -m bot.main`)
- Check the terminal for error messages
- Verify your `TELEGRAM_BOT_TOKEN` in `.env`

### Lost my sentences after bot restart
- Sentences are stored in SQLite and persist across restarts
- If truly lost, use `/setup` to download again
- Check that `data/bot.db` exists and isn't corrupted

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
