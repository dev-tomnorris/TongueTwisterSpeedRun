# Quick Start Checklist

## ✅ Step 1: Discord Developer Portal Setup

1. Go to https://discord.com/developers/applications
2. Click "New Application" → Give it a name → Create
3. Go to the **"Bot"** section (left sidebar)
4. Click **"Add Bot"** → Confirm
5. Under **"Privileged Gateway Intents"**, enable:
   - ✅ **Message Content Intent** (REQUIRED)
   - ✅ **Server Members Intent** (optional but recommended)
6. Click **"Reset Token"** → Copy the token (you'll need it)
7. Go to **"OAuth2"** → **"URL Generator"**
8. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
9. Select bot permissions:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Use Slash Commands
   - ✅ Connect (Voice)
   - ✅ Speak (Voice)
   - ✅ Use Voice Activity
10. Copy the generated URL and open it in your browser to invite the bot to your server

## ✅ Step 2: Create .env File

Create a `.env` file in the project root with:

```
DISCORD_TOKEN=your_bot_token_here
WHISPER_MODEL=base
DATABASE_PATH=./data/twister.db
RECORDING_TIMEOUT=30
MIN_ACCURACY_FOR_SUCCESS=80
```

**Replace `your_bot_token_here` with the token you copied from step 6 above.**

## ✅ Step 3: Run the Bot

```bash
python main.py
```

The bot will:
- ✅ Create the database automatically
- ✅ Download Whisper model on first run (~500MB, one-time)
- ✅ Connect to Discord
- ✅ Be ready to use!

## 🎮 First Test

1. Join a voice channel in your Discord server
2. Use `/twister join` in a text channel
3. Use `/twister start` to try your first tongue twister!

## ⚠️ Troubleshooting

**Bot doesn't start:**
- Check that `.env` file exists and has `DISCORD_TOKEN=`
- Make sure you copied the token correctly (no extra spaces)

**Bot can't join voice:**
- Make sure you're in a voice channel when using `/twister join`
- Check bot has "Connect" and "Speak" permissions in your server

**Commands not showing:**
- Slash commands can take up to 1 hour to register globally
- For faster testing, restart Discord or wait a few minutes

