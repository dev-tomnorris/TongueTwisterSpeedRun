# Tongue Twister Speed Run Discord Bot

A Discord bot that challenges players to say tongue twisters quickly and accurately using voice input. The bot listens to players in voice channels, uses speech-to-text to verify their attempts, and scores them based on accuracy and speed.

## Features

- **Voice Recognition**: Uses OpenAI Whisper for accurate speech-to-text conversion
- **Scoring System**: Calculates scores based on accuracy, speed, and difficulty
- **Multiple Game Modes**: Solo practice, timed challenges, duels, and tournaments
- **Leaderboards**: Track your progress and compete with others
- **Statistics**: Detailed stats on your performance
- **Custom Tongue Twisters**: Add your own tongue twisters
- **Achievements**: Unlock achievements as you play

## Prerequisites

- Python 3.10 or higher
- Discord Bot Token
- Discord Server with Voice Channels

**Note:** FFmpeg functionality is included via the `ffmpeg4discord` package, so no separate installation is needed.

## Installation

1. Clone this repository or download the files

2. Install Python dependencies (includes FFmpeg via ffmpeg4discord):
```bash
pip install -r requirements.txt
```

**Note:** The `ffmpeg4discord` package bundles FFmpeg functionality, so you don't need to install FFmpeg separately. If you prefer to install FFmpeg manually instead, you can remove `ffmpeg4discord` from requirements.txt and install FFmpeg separately:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - **Linux**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`

3. Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

4. Edit `.env` and add your Discord bot token:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

5. Create the data directory:
```bash
mkdir -p data
```

## Setting Up a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token and add it to your `.env` file
5. Enable the following Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent (if needed)
6. Go to OAuth2 > URL Generator
7. Select scopes: `bot` and `applications.commands`
8. Select bot permissions:
   - Send Messages
   - Embed Links
   - Use Slash Commands
   - Connect (Voice)
   - Speak (Voice)
   - Use Voice Activity
9. Copy the generated URL and open it in your browser to invite the bot to your server

## Running the Bot

```bash
python main.py
```

The bot will:
- Download the Whisper model on first run (can be large, ~500MB for base model)
- Initialize the database
- Connect to Discord
- Be ready to use!

## Commands

### Basic Commands
- `/twister join` - Join voice channel and start a session
- `/twister leave` - End session and leave voice channel
- `/twister start [difficulty]` - Start a random tongue twister challenge
- `/twister practice <id>` - Practice a specific tongue twister
- `/twister list [difficulty]` - View all tongue twisters

### Stats & Leaderboards
- `/twister stats [user]` - View player statistics
- `/twister leaderboard [scope] [difficulty]` - View leaderboards
- `/twister challenge` - Start a timed challenge (10 twisters)

### Competitive
- `/twister duel @player` - Challenge another player
- `/twister accept` - Accept a pending duel
- `/twister tournament start [players]` - Start a tournament

### Advanced
- `/twister custom add <text> [difficulty]` - Add a custom tongue twister
- `/twister custom list` - View custom tongue twisters
- `/twister daily` - Start the daily challenge

## Configuration

Edit `config.py` to customize:
- Difficulty multipliers
- Speed bonus thresholds
- Challenge settings
- Voice recording settings

## Troubleshooting

**Bot can't join voice channel:**
- Make sure the bot has "Connect" and "Speak" permissions
- Check that you're in a voice channel when using `/twister join`

**Speech recognition not working:**
- The `ffmpeg4discord` package should handle FFmpeg automatically
- If issues persist, try installing FFmpeg manually (see installation step 2)
- Check that your microphone is working in Discord
- Try using a different Whisper model (edit `.env`)

**Database errors:**
- Make sure the `data` directory exists
- Check file permissions

## License

This project is open source and available for personal use.

