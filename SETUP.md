# Tongue Twister Bot - Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg**
   - Windows: Download from https://ffmpeg.org/download.html and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

3. **Create .env file**
   Create a `.env` file in the project root with:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   WHISPER_MODEL=base
   DATABASE_PATH=./data/twister.db
   RECORDING_TIMEOUT=30
   MIN_ACCURACY_FOR_SUCCESS=80
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## Features Implemented

### Phase 1: Core MVP ✅
- `/twister join` - Join voice channel
- `/twister leave` - Leave voice channel
- `/twister start` - Random tongue twister challenge
- `/twister practice <id>` - Practice specific twister
- `/twister list` - View all tongue twisters
- Speech recognition with Whisper
- Accuracy scoring
- Time tracking

### Phase 2: Stats & Leaderboards ✅
- `/twister stats` - View player statistics
- `/twister leaderboard` - Server/global leaderboards
- `/twister challenge` - Timed challenge (10 twisters)
- Database persistence
- Personal best tracking

### Phase 3: Competitive Play ✅
- `/twister duel @player` - Challenge another player
- `/twister accept` - Accept duel challenge
- Best-of-3 duels
- Real-time scoring

### Phase 4: Advanced Features ✅
- `/twister custom add` - Add custom tongue twisters
- `/twister custom list` - View custom twisters
- `/twister daily` - Daily challenge mode
- Achievement system (database ready)

## Project Structure

```
twister-bot/
├── main.py                 # Entry point
├── config.py              # Configuration constants
├── requirements.txt       # Dependencies
├── README.md              # Documentation
│
├── bot/                   # Discord bot setup
│   ├── client.py         # Bot client
│   └── events.py         # Event handlers
│
├── cogs/                  # Command modules
│   └── game_commands.py   # All game commands
│
├── game/                  # Game logic
│   ├── session.py        # Session data
│   ├── session_manager.py # Session management
│   └── scoring.py        # Scoring calculations
│
├── voice/                 # Voice handling
│   ├── handler.py        # Voice channel management
│   ├── recorder.py       # Audio recording
│   └── speech_to_text.py # Whisper integration
│
├── data/                  # Data files
│   └── tongue_twisters.py # 20 starter twisters
│
├── database/              # Database layer
│   ├── models.py         # SQL schemas
│   ├── migrations.py     # Database initialization
│   └── manager.py        # Database operations
│
└── utils/                 # Utilities
    ├── embeds.py         # Discord embeds
    ├── formatters.py     # Text formatting
    └── text_similarity.py # Accuracy calculations
```

## Notes

- Whisper model downloads automatically on first run (~500MB for base model)
- Database is created automatically on first run
- Audio files are saved temporarily and cleaned up after processing
- All 20 starter tongue twisters are included

