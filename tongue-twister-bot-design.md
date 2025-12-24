# Tongue Twister Speed Run Discord Bot - Design Document

## Project Overview

### Purpose
A Discord bot that challenges players to say tongue twisters quickly and accurately using voice input. The bot listens to players in voice channels, uses speech-to-text to verify their attempts, and scores them based on accuracy and speed. Features leaderboards, difficulty levels, and competitive modes.

### Target Audience
- Discord communities looking for interactive voice games
- Friend groups who enjoy party games
- Communities wanting voice channel activities
- Players who enjoy quick, skill-based challenges

### Key Goals
1. Create engaging voice-activated gameplay
2. Implement accurate speech recognition and scoring
3. Support both solo practice and competitive modes
4. Track player progress with leaderboards
5. Make the game accessible yet challenging
6. Test entirely solo (for development)
7. Scale to multiplayer competitions

---

## Game Overview

### Core Concept

Players join a voice channel where the bot presents tongue twisters of varying difficulty. Players speak the tongue twister into their microphone, and the bot:
1. Records the audio
2. Converts speech to text
3. Compares spoken text to the target
4. Calculates accuracy score
5. Factors in speed
6. Awards points and updates leaderboards

**Example Round:**
```
Bot: "🎤 Say this tongue twister: 'She sells seashells by the seashore'"
Bot: "Ready? GO!"
[Player speaks into mic]
Bot: "You said: 'She sells seashells by the sea shore'"
Bot: "Accuracy: 95% | Time: 2.3 seconds | Score: 412 points! 🎉"
```

### Game Modes

**Solo Practice Mode:**
- Player vs. themselves
- Try any tongue twister
- No time pressure
- Practice until perfect
- Track personal best

**Timed Challenge Mode:**
- Player vs. clock
- 10 tongue twisters in a row
- 30 seconds per twister
- Cumulative score
- Leaderboard tracking

**Head-to-Head Mode:**
- 2 players compete
- Same tongue twister
- Highest score wins
- Best of 3 or 5 rounds

**Tournament Mode (Phase 3):**
- Multiple players
- Bracket elimination
- Increasing difficulty
- Winner takes all

---

## Core Features

### Phase 1: MVP (Solo Play)
- `/twister join` - Join voice channel and start session
- `/twister start` - Begin a tongue twister challenge
- `/twister practice <id>` - Practice specific twister
- `/twister stop` - End session
- Basic speech-to-text recognition
- Accuracy scoring (text similarity)
- Time tracking
- 20 starter tongue twisters (Easy, Medium, Hard)

### Phase 2: Leaderboards & Stats
- `/twister stats` - View personal statistics
- `/twister leaderboard` - Server-wide rankings
- `/twister challenge` - Timed challenge mode (10 twisters)
- Personal best tracking
- Accuracy percentages by difficulty
- Streak tracking
- Achievement system

### Phase 3: Competitive Play
- `/twister duel @player` - Challenge another player
- `/twister tournament` - Start bracket tournament
- Real-time scoring display
- Spectator mode
- Replay system (save audio)

### Phase 4: Advanced Features
- `/twister custom add` - Add custom tongue twisters
- `/twister daily` - Daily challenge
- Voice effects (optional, for fun)
- Difficulty rating by community
- Multi-language support

---

## Technical Architecture

### High-Level Design

```
┌─────────────────────────────────────────┐
│         Discord Voice Channel           │
│  ┌──────────┐  ┌──────────┐            │
│  │ Player 1 │  │ Player 2 │            │
│  │  Audio   │  │  Audio   │            │
│  └────┬─────┘  └────┬─────┘            │
└───────┼─────────────┼──────────────────┘
        │             │
        └──────┬──────┘
               │ Voice Stream
               ▼
┌──────────────────────────────────────────┐
│         Discord Bot Process              │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │   Voice Handler                    │  │
│  │  - Join/leave voice channel       │  │
│  │  - Record audio streams           │  │
│  │  - Isolate player audio           │  │
│  └──────────┬─────────────────────────┘  │
│             │                            │
│  ┌──────────▼─────────────────────────┐  │
│  │   Speech-to-Text Engine            │  │
│  │  - Google Speech API               │  │
│  │  - OR Whisper (OpenAI)             │  │
│  │  - Convert audio → text            │  │
│  └──────────┬─────────────────────────┘  │
│             │                            │
│  ┌──────────▼─────────────────────────┐  │
│  │   Scoring Engine                   │  │
│  │  - Text similarity (Levenshtein)   │  │
│  │  - Accuracy calculation            │  │
│  │  - Speed bonus                     │  │
│  │  - Final score                     │  │
│  └──────────┬─────────────────────────┘  │
│             │                            │
│  ┌──────────▼─────────────────────────┐  │
│  │   Game State Manager               │  │
│  │  - Active sessions                 │  │
│  │  - Turn management                 │  │
│  │  - Score tracking                  │  │
│  └──────────┬─────────────────────────┘  │
│             │                            │
│  ┌──────────▼─────────────────────────┐  │
│  │   Database Layer                   │  │
│  │  - Player stats                    │  │
│  │  - Leaderboards                    │  │
│  │  - Tongue twister library          │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### Key Components

#### 1. Voice Handler
**Purpose:** Manage voice channel connections and audio recording

**Responsibilities:**
- Join/leave voice channels
- Record player audio streams
- Isolate individual player audio
- Handle disconnections
- Manage audio buffers

**Technology:**
- `discord.py[voice]` - Voice support
- `PyNaCl` - Audio encryption
- `FFmpeg` - Audio processing

#### 2. Speech-to-Text Engine
**Purpose:** Convert recorded audio to text

**Options:**

**Option A: Google Speech-to-Text API** (Recommended for MVP)
- Pros: Very accurate, fast, easy to use
- Cons: Costs money (but cheap), requires internet
- Cost: $0.006 per 15 seconds (~$0.024 per minute)
- Setup: Google Cloud account + API key

**Option B: OpenAI Whisper** (Best long-term)
- Pros: Very accurate, can run locally, no per-use cost
- Cons: Slower, requires more setup, GPU recommended
- Cost: Free (compute cost only)
- Setup: Download Whisper model, run locally or via API

**Option C: SpeechRecognition library** (Quick prototype)
- Pros: Free, easy, no setup
- Cons: Less accurate, limited features
- Cost: Free
- Setup: pip install, uses Google's free tier

**Recommendation for phases:**
- Phase 1: SpeechRecognition (quick start)
- Phase 2+: Whisper local (best quality, no recurring cost)

#### 3. Scoring Engine
**Purpose:** Calculate scores based on accuracy and speed

**Accuracy Calculation:**
```python
from difflib import SequenceMatcher

def calculate_accuracy(spoken: str, target: str) -> float:
    """Calculate similarity between spoken and target text."""
    # Normalize text (lowercase, remove punctuation)
    spoken_normalized = normalize_text(spoken)
    target_normalized = normalize_text(target)
    
    # Calculate similarity ratio (0.0 to 1.0)
    similarity = SequenceMatcher(None, spoken_normalized, target_normalized).ratio()
    
    return similarity * 100  # Return as percentage

def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    import re
    # Lowercase
    text = text.lower()
    # Remove punctuation except spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing spaces
    text = text.strip()
    return text
```

**Score Formula:**
```python
def calculate_score(accuracy: float, time_seconds: float, difficulty: str) -> int:
    """
    Calculate final score based on accuracy, speed, and difficulty.
    
    Base score from accuracy:
    - 100% accuracy = 1000 points
    - 90% accuracy = 900 points
    - etc.
    
    Speed bonus:
    - Under 3 seconds: +500 points
    - Under 5 seconds: +300 points
    - Under 8 seconds: +100 points
    
    Difficulty multiplier:
    - Easy: 1.0x
    - Medium: 1.5x
    - Hard: 2.0x
    - Insane: 3.0x
    """
    # Base score from accuracy (0-1000)
    base_score = accuracy * 10
    
    # Speed bonus
    if time_seconds < 3:
        speed_bonus = 500
    elif time_seconds < 5:
        speed_bonus = 300
    elif time_seconds < 8:
        speed_bonus = 100
    else:
        speed_bonus = 0
    
    # Difficulty multiplier
    difficulty_multipliers = {
        'easy': 1.0,
        'medium': 1.5,
        'hard': 2.0,
        'insane': 3.0
    }
    multiplier = difficulty_multipliers.get(difficulty.lower(), 1.0)
    
    # Calculate final score
    final_score = int((base_score + speed_bonus) * multiplier)
    
    return final_score
```

**Example Scores:**
```
Target: "She sells seashells by the seashore"
Spoken: "She sells seashells by the seashore"
Accuracy: 100% | Time: 2.5s | Difficulty: Easy
Score: (1000 + 500) * 1.0 = 1500 points

Target: "Red leather yellow leather"
Spoken: "Red lether yellow leather"
Accuracy: 95% | Time: 1.8s | Difficulty: Medium
Score: (950 + 500) * 1.5 = 2175 points

Target: "The sixth sick sheik's sixth sheep's sick"
Spoken: "The sixth sick sheik's sixth sheep sick"
Accuracy: 97% | Time: 4.2s | Difficulty: Hard
Score: (970 + 300) * 2.0 = 2540 points
```

#### 4. Game State Manager
**Purpose:** Track active game sessions and player states

**Session State:**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TwisterSession:
    """Represents an active tongue twister session."""
    session_id: str
    channel_id: str
    server_id: str
    player_id: str
    player_name: str
    
    # Session type
    mode: str  # 'practice', 'timed_challenge', 'duel'
    
    # Current state
    active: bool = True
    current_twister_id: Optional[int] = None
    waiting_for_attempt: bool = False
    attempt_started_at: Optional[datetime] = None
    
    # Stats for this session
    attempts: int = 0
    successful_attempts: int = 0
    total_score: int = 0
    
    # For timed challenges
    twisters_completed: int = 0
    twisters_total: int = 10
```

---

## Tongue Twister Library

### Difficulty Categories

**Easy (Level 1-3):**
- Short phrases (5-8 words)
- Common words
- Simple consonant patterns
- Example: "She sells seashells"

**Medium (Level 4-6):**
- Longer phrases (8-12 words)
- More complex patterns
- Repeated consonants
- Example: "Red leather yellow leather"

**Hard (Level 7-9):**
- Long phrases (12-15 words)
- Difficult consonant clusters
- Unusual word combinations
- Example: "The sixth sick sheik's sixth sheep's sick"

**Insane (Level 10):**
- Very long or extremely difficult
- Multiple patterns combined
- Nearly impossible to say perfectly
- Example: "Pad kid poured curd pulled cod"

### Starter Tongue Twisters (20 Total)

#### Easy (7 twisters)

| ID | Tongue Twister | Difficulty | Words | Focus |
|----|---------------|------------|-------|-------|
| 1 | She sells seashells by the seashore | Easy | 6 | S sounds |
| 2 | Rubber baby buggy bumpers | Easy | 4 | B sounds |
| 3 | Unique New York | Easy | 3 | U/Y sounds |
| 4 | Toy boat toy boat | Easy | 4 | T/B sounds |
| 5 | Red lorry yellow lorry | Easy | 4 | L/R sounds |
| 6 | Greek grapes Greek grapes | Easy | 4 | GR sounds |
| 7 | Which witch is which | Easy | 4 | WH sounds |

#### Medium (7 twisters)

| ID | Tongue Twister | Difficulty | Words | Focus |
|----|----------------|------------|-------|-------|
| 8 | Peter Piper picked a peck of pickled peppers | Medium | 8 | P sounds |
| 9 | How much wood would a woodchuck chuck | Medium | 7 | W/CH sounds |
| 10 | Red leather yellow leather red leather yellow leather | Medium | 8 | L/R sounds |
| 11 | Betty Botter bought some butter but she said the butter's bitter | Medium | 11 | B/T sounds |
| 12 | I scream you scream we all scream for ice cream | Medium | 10 | SCR sounds |
| 13 | Fuzzy Wuzzy was a bear Fuzzy Wuzzy had no hair | Medium | 10 | F/Z sounds |
| 14 | Six slippery snails slid slowly seaward | Medium | 6 | S/SL sounds |

#### Hard (4 twisters)

| ID | Tongue Twister | Difficulty | Words | Focus |
|----|----------------|------------|-------|-------|
| 15 | The sixth sick sheik's sixth sheep's sick | Hard | 7 | S/SH/TH sounds |
| 16 | I saw Susie sitting in a shoeshine shop | Hard | 9 | S/SH sounds |
| 17 | Lesser leather never weathered wetter weather better | Hard | 7 | L/W/TH sounds |
| 18 | Brisk brave brigadiers brandished broad bright blades | Hard | 7 | BR/BL sounds |

#### Insane (2 twisters)

| ID | Tongue Twister | Difficulty | Words | Focus |
|----|----------------|------------|-------|-------|
| 19 | Pad kid poured curd pulled cod | Insane | 6 | Multiple clusters |
| 20 | The seething sea ceaseth and thus the seething sea sufficeth us | Insane | 11 | S/TH/C sounds |

---

## Commands & User Interactions

### Setup Commands

#### `/twister join`
**Description:** Join voice channel and start a session

**Usage:**
```
/twister join
```

**Requirements:**
- User must be in a voice channel
- Bot has permission to join voice channel

**Response:**
```
🎤 **Tongue Twister Session Started!**

Joined voice channel: General Voice
Player: @Username

Available modes:
• `/twister start` - Random twister
• `/twister practice <id>` - Practice specific twister
• `/twister challenge` - Timed challenge (10 twisters)

Use `/twister list` to see all tongue twisters!
```

#### `/twister leave`
**Description:** Leave voice channel and end session

**Response:**
```
👋 **Session Ended**

Thanks for playing!

**Your Stats This Session:**
Attempts: 15
Success rate: 80% (12/15)
Total score: 18,450 points
Best score: 2,540 points (Twister #15)

See you next time! 🎉
```

---

### Gameplay Commands

#### `/twister start [difficulty]`
**Description:** Start a random tongue twister

**Options:**
- `difficulty` (optional) - easy, medium, hard, insane, random

**Usage:**
```
/twister start
/twister start difficulty:hard
```

**Response:**
```
🎤 **Tongue Twister Challenge!**

Difficulty: Medium
Ready? Say this as fast as you can:

"Red leather yellow leather red leather yellow leather"

Say it clearly when you're ready! ⏱️
I'm listening... (30 second timer)
```

**After player speaks:**
```
✅ **Nice Try!**

You said: "Red lether yellow leather red lether yellow leather"
Target: "Red leather yellow leather red leather yellow leather"

**Accuracy:** 95% (2 small mistakes)
**Time:** 3.2 seconds
**Difficulty:** Medium (1.5x multiplier)

**Score:** 1,913 points! 🎉

Mistakes:
- "lether" → "leather" (x2)

Try again? Use `/twister start` for another!
```

#### `/twister practice <id>`
**Description:** Practice a specific tongue twister

**Parameters:**
- `id` (required) - Twister ID (1-20)

**Usage:**
```
/twister practice 15
```

**Response:**
```
🎯 **Practice Mode**

Twister #15 - Hard Difficulty
"The sixth sick sheik's sixth sheep's sick"

No score tracking in practice mode.
Take your time and say it clearly!

I'm listening...
```

#### `/twister list [difficulty]`
**Description:** View all tongue twisters

**Options:**
- `difficulty` (optional) - Filter by difficulty

**Response:**
```
📜 **Tongue Twister Library**

**Easy (1-7):**
1. She sells seashells by the seashore
2. Rubber baby buggy bumpers
3. Unique New York
...

**Medium (8-14):**
8. Peter Piper picked a peck of pickled peppers
...

Use `/twister practice <id>` to practice!
Use `/twister start difficulty:hard` for a random hard twister!
```

#### `/twister challenge`
**Description:** Start timed challenge (10 random twisters)

**Response:**
```
⚡ **TIMED CHALLENGE MODE** ⚡

Complete 10 tongue twisters as fast and accurately as possible!

Rules:
• 30 seconds per twister
• Mixed difficulties
• Cumulative score
• Results added to leaderboard

Ready? Starting in 3... 2... 1... GO!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Twister 1/10**

Difficulty: Easy
"Toy boat toy boat toy boat"

I'm listening...
```

**After all 10 completed:**
```
🏆 **CHALLENGE COMPLETE!** 🏆

**Final Stats:**
Total Score: 21,450 points
Average Accuracy: 92%
Fastest Time: 1.8 seconds (Twister #3)
Slowest Time: 6.2 seconds (Twister #9)

**Breakdown:**
1. Toy boat (Easy): 1,200 pts | 98% | 2.1s
2. Red leather (Medium): 2,300 pts | 94% | 3.5s
...

🎖️ New Personal Best! (Previous: 19,800)
📊 Server Rank: #7 (+2)

Great job! 🎉
```

---

### Stats & Leaderboard Commands

#### `/twister stats [user]`
**Description:** View statistics

**Options:**
- `user` (optional) - View another user's stats

**Usage:**
```
/twister stats
/twister stats @Player2
```

**Response:**
```
📊 **@Username's Statistics**

**Overall Performance:**
Total Attempts: 347
Success Rate: 87% (302/347)
Total Score: 426,890 points
Average Score: 1,230 points per attempt

**Personal Bests:**
Highest Score: 4,850 points (Twister #20 - Insane)
Best Accuracy: 100% (achieved 47 times)
Fastest Time: 1.2 seconds (Twister #3)

**By Difficulty:**
Easy: 98% accuracy (234 attempts)
Medium: 89% accuracy (78 attempts)
Hard: 73% accuracy (28 attempts)
Insane: 57% accuracy (7 attempts)

**Achievements Unlocked:** 8/15
```

#### `/twister leaderboard [scope] [difficulty]`
**Description:** View leaderboards

**Options:**
- `scope` (optional) - server (default), global
- `difficulty` (optional) - Filter by difficulty

**Usage:**
```
/twister leaderboard
/twister leaderboard scope:global difficulty:hard
```

**Response:**
```
🏆 **Server Leaderboard - All Difficulties**

**Top 10 Players:**

1. 👑 @Player1 - 1,247,890 points
   Best: 4,980 pts | Attempts: 892 | Accuracy: 91%

2. 🥈 @Player2 - 987,650 points
   Best: 4,720 pts | Attempts: 745 | Accuracy: 93%

3. 🥉 @Player3 - 876,430 points
   Best: 4,850 pts | Attempts: 678 | Accuracy: 89%

4. @Player4 - 654,320 points
5. @Player5 - 543,210 points
...
15. @You - 426,890 points

Your rank: #15
```

---

### Competitive Commands (Phase 3)

#### `/twister duel @player`
**Description:** Challenge another player to head-to-head

**Parameters:**
- `player` (required) - Player to challenge

**Usage:**
```
/twister duel @Player2
```

**Response:**
```
⚔️ **DUEL CHALLENGE!** ⚔️

@Player1 has challenged @Player2!

Format: Best of 3 rounds
- Same tongue twister for both players
- Highest score wins each round
- First to 2 round wins overall

@Player2, use `/twister accept` to accept!
Challenge expires in 2 minutes.
```

**During duel:**
```
⚔️ **ROUND 1/3** ⚔️

Both players will say:
"Peter Piper picked a peck of pickled peppers"

@Player1, you're up first!
I'm listening...

[After Player 1]

@Player1: 2,340 points (96% accuracy, 2.8s)

Now @Player2's turn!
I'm listening...

[After Player 2]

@Player2: 2,510 points (98% accuracy, 2.6s)

🎉 @Player2 wins Round 1!

Score: Player1: 0 | Player2: 1

Next round in 5 seconds...
```

---

## Database Schema

### Tables

#### players
```sql
CREATE TABLE players (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    best_score INTEGER DEFAULT 0,
    best_score_twister_id INTEGER,
    fastest_time REAL,  -- Seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP
);
```

#### attempts
```sql
CREATE TABLE attempts (
    attempt_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    twister_id INTEGER NOT NULL,
    spoken_text TEXT,
    accuracy REAL,  -- 0-100
    time_seconds REAL,
    score INTEGER,
    difficulty TEXT,
    session_type TEXT,  -- 'practice', 'challenge', 'duel'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES players(user_id)
);
```

#### tongue_twisters
```sql
CREATE TABLE tongue_twisters (
    twister_id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    difficulty TEXT NOT NULL,  -- easy, medium, hard, insane
    word_count INTEGER,
    focus_sounds TEXT,  -- e.g., "S, SH sounds"
    times_attempted INTEGER DEFAULT 0,
    average_accuracy REAL DEFAULT 0.0,
    created_by TEXT,  -- For custom twisters (Phase 4)
    is_official BOOLEAN DEFAULT TRUE
);
```

#### sessions
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    server_id TEXT,
    channel_id TEXT,
    session_type TEXT,  -- 'solo', 'challenge', 'duel', 'tournament'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_attempts INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES players(user_id)
);
```

#### leaderboards (computed view)
```sql
CREATE VIEW leaderboard_overall AS
SELECT 
    user_id,
    username,
    total_score,
    total_attempts,
    ROUND(CAST(successful_attempts AS REAL) / total_attempts * 100, 1) as success_rate,
    best_score
FROM players
ORDER BY total_score DESC
LIMIT 100;

CREATE VIEW leaderboard_by_difficulty AS
SELECT 
    user_id,
    username,
    difficulty,
    SUM(score) as total_score,
    COUNT(*) as attempts,
    ROUND(AVG(accuracy), 1) as avg_accuracy
FROM attempts
GROUP BY user_id, difficulty
ORDER BY total_score DESC;
```

---

## Project Structure

```
twister-bot/
├── main.py                     # Entry point
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── .env                        # Environment variables
├── .env.example                # Example env file
├── README.md                   # Setup instructions
│
├── bot/
│   ├── __init__.py
│   ├── client.py              # Discord bot client
│   └── events.py              # Event handlers
│
├── cogs/
│   ├── __init__.py
│   ├── game_commands.py       # Main game commands
│   ├── stats_commands.py      # Stats and leaderboards
│   └── competitive_commands.py # Duels, tournaments (Phase 3)
│
├── game/
│   ├── __init__.py
│   ├── session.py             # TwisterSession class
│   ├── session_manager.py     # Manages active sessions
│   └── scoring.py             # Scoring calculations
│
├── voice/
│   ├── __init__.py
│   ├── handler.py             # Voice channel management
│   ├── recorder.py            # Audio recording
│   └── speech_to_text.py      # Speech recognition
│
├── data/
│   ├── __init__.py
│   └── tongue_twisters.py     # Twister library
│
├── database/
│   ├── __init__.py
│   ├── models.py              # Database models
│   └── manager.py             # Database operations
│
├── utils/
│   ├── __init__.py
│   ├── formatters.py          # Message formatting
│   ├── embeds.py              # Discord embed builders
│   └── text_similarity.py     # Accuracy calculations
│
└── data/
    └── twister.db             # SQLite database
```

---

## Implementation Phases

### Phase 1: Core Functionality (Week 1)

**Goal:** Basic working game with speech recognition

**Day 1-2: Foundation**
- [ ] Project setup
- [ ] Discord bot with voice support
- [ ] Voice channel join/leave
- [ ] Audio recording from voice channel

**Day 3-4: Speech Recognition**
- [ ] Integrate speech-to-text (SpeechRecognition library)
- [ ] Test audio quality and recognition accuracy
- [ ] Handle audio preprocessing

**Day 5-6: Game Logic**
- [ ] Load 20 tongue twisters
- [ ] `/twister join` command
- [ ] `/twister start` command
- [ ] Text similarity scoring
- [ ] Time tracking

**Day 7: Polish MVP**
- [ ] `/twister practice` command
- [ ] `/twister list` command
- [ ] Error handling
- [ ] Basic embeds for responses

**Deliverable:** Working solo game with speech recognition and scoring

---

### Phase 2: Stats & Leaderboards (Week 2)

**Goal:** Track progress and add competitive elements

**Tasks:**
- [ ] Database setup (players, attempts, sessions)
- [ ] `/twister stats` command
- [ ] `/twister leaderboard` command
- [ ] `/twister challenge` (timed mode)
- [ ] Personal best tracking
- [ ] Success rate calculations
- [ ] Rich embeds for all responses

**Deliverable:** Full stats tracking and leaderboards

---

### Phase 3: Competitive Play (Week 3)

**Goal:** Add multiplayer competitive modes

**Tasks:**
- [ ] `/twister duel` command
- [ ] Head-to-head match system
- [ ] Turn management
- [ ] Real-time score display
- [ ] Tournament bracket system
- [ ] Spectator notifications

**Deliverable:** Competitive multiplayer modes

---

### Phase 4: Advanced Features (Week 4+)

**Goal:** Community features and customization

**Tasks:**
- [ ] Custom tongue twisters
- [ ] Daily challenges
- [ ] Achievement system
- [ ] Audio replay system
- [ ] Multi-language support
- [ ] Difficulty rating by community

---

## Tech Stack

### Core Dependencies
```
python >= 3.10
discord.py[voice] >= 2.3.0
PyNaCl >= 1.5.0              # Voice encryption
python-dotenv >= 1.0.0
```

### Audio Processing
```
FFmpeg                        # Audio codec (system install)
pydub >= 0.25.0              # Audio manipulation
```

### Speech Recognition
```
# Option 1: Quick start (Phase 1)
SpeechRecognition >= 3.10.0

# Option 2: Best quality (Phase 2+)
openai-whisper >= 20230314
OR
google-cloud-speech >= 2.20.0
```

### Text Processing
```
python-Levenshtein >= 0.21.0  # Fast string similarity
difflib (built-in)            # Text comparison
```

### Database
```
aiosqlite >= 0.19.0          # Async SQLite
```

---

## Configuration

### Environment Variables (.env)
```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token_here

# Speech Recognition
SPEECH_ENGINE=whisper  # Options: whisper, google, speechrecognition
GOOGLE_CLOUD_API_KEY=your_google_api_key  # If using Google
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large

# Audio Settings
AUDIO_SAMPLE_RATE=48000
AUDIO_CHANNELS=2
RECORDING_TIMEOUT=30  # Seconds

# Database
DATABASE_PATH=./data/twister.db

# Game Settings
MIN_ACCURACY_FOR_SUCCESS=80  # Percentage
MAX_ATTEMPT_TIME=30  # Seconds
```

### Constants (config.py)
```python
# Difficulty multipliers
DIFFICULTY_MULTIPLIERS = {
    'easy': 1.0,
    'medium': 1.5,
    'hard': 2.0,
    'insane': 3.0
}

# Speed bonus thresholds (seconds: bonus points)
SPEED_BONUSES = {
    3: 500,
    5: 300,
    8: 100
}

# Accuracy thresholds
MIN_ACCURACY_SUCCESS = 80  # Consider attempt "successful"
PERFECT_ACCURACY = 100

# Challenge mode
CHALLENGE_TWISTER_COUNT = 10
CHALLENGE_TIME_PER_TWISTER = 30  # seconds

# Voice settings
VOICE_RECORDING_TIMEOUT = 30  # seconds
VOICE_SILENCE_THRESHOLD = 0.5  # seconds of silence ends recording
```

---

## Voice Integration Details

### Discord Permissions Required

**Bot Permissions:**
```
Voice Permissions:
✅ Connect
✅ Speak
✅ Use Voice Activity

Text Permissions:
✅ Send Messages
✅ Embed Links
✅ Use Slash Commands
```

**Gateway Intents:**
```python
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
```

### Audio Recording Flow

```python
# Pseudocode for audio recording

async def record_player_audio(voice_client, player_id, timeout=30):
    """Record audio from a specific player in voice channel."""
    
    # Start recording
    audio_buffer = []
    start_time = time.time()
    
    # Listen to voice channel
    @voice_client.sink
    async def audio_callback(user, audio_data):
        if user.id == player_id:
            audio_buffer.append(audio_data)
    
    # Wait for speech (max timeout seconds)
    while time.time() - start_time < timeout:
        if len(audio_buffer) > 0:
            # Check for silence (end of speech)
            if detect_silence(audio_buffer[-10:]):
                break
        await asyncio.sleep(0.1)
    
    # Stop recording
    voice_client.stop_listening()
    
    # Convert audio buffer to file
    audio_file = combine_audio_chunks(audio_buffer)
    
    return audio_file
```

### Speech-to-Text Integration

**Option 1: SpeechRecognition (Quick Start)**
```python
import speech_recognition as sr

def transcribe_audio(audio_file_path):
    """Convert audio to text using SpeechRecognition."""
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return None  # Could not understand audio
    except sr.RequestError as e:
        print(f"Error: {e}")
        return None
```

**Option 2: OpenAI Whisper (Best Quality)**
```python
import whisper

# Load model once at startup
model = whisper.load_model("base")

def transcribe_audio(audio_file_path):
    """Convert audio to text using Whisper."""
    result = model.transcribe(audio_file_path)
    return result["text"]
```

**Option 3: Google Cloud Speech-to-Text**
```python
from google.cloud import speech

def transcribe_audio(audio_file_path):
    """Convert audio to text using Google Cloud."""
    client = speech.SpeechClient()
    
    with open(audio_file_path, 'rb') as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code="en-US",
    )
    
    response = client.recognize(config=config, audio=audio)
    
    if response.results:
        return response.results[0].alternatives[0].transcript
    return None
```

---

## Testing Strategy

### Manual Testing Checklist

**Voice Setup:**
- [ ] Bot joins voice channel
- [ ] Bot leaves voice channel
- [ ] Bot can hear player audio
- [ ] Multiple players in channel (bot isolates correct player)
- [ ] Handle disconnections gracefully

**Speech Recognition:**
- [ ] Clear speech transcribed correctly
- [ ] Fast speech transcribed
- [ ] Mumbled speech handled (low accuracy score)
- [ ] Background noise filtered
- [ ] Multiple accents tested

**Scoring:**
- [ ] 100% accuracy = full points
- [ ] Small mistakes = reduced accuracy
- [ ] Speed bonuses calculated correctly
- [ ] Difficulty multipliers applied
- [ ] Edge cases (empty audio, timeout)

**Game Flow:**
- [ ] Start session
- [ ] Complete twister
- [ ] Practice mode
- [ ] Challenge mode (10 twisters)
- [ ] Stats tracked correctly
- [ ] Leaderboard updates

### Testing with Multiple Accounts

**Setup:**
- Create test Discord server
- Invite 2-3 test accounts (or use friends)
- Test competitive modes

**Scenarios:**
- Two players in same voice channel
- Bot correctly identifies who spoke
- Duel mode works between two players
- Spectators can see real-time scores

---

## Common Issues & Solutions

### Issue: Speech Recognition Inaccurate

**Causes:**
- Poor audio quality
- Background noise
- Fast/unclear speech

**Solutions:**
- Use noise cancellation
- Require clear speech
- Use better speech engine (Whisper)
- Show what was heard to player
- Allow retry

### Issue: Bot Can't Hear Player

**Causes:**
- Player muted in Discord
- Bot missing Voice Activity permission
- Audio encoding issues

**Solutions:**
- Check player isn't muted
- Verify bot permissions
- Test with different audio settings
- Provide clear error messages

### Issue: High Latency

**Causes:**
- Speech recognition is slow
- Large audio files
- Network delays

**Solutions:**
- Use local Whisper model
- Optimize audio file size
- Show "Processing..." message
- Stream audio instead of file upload

---

## Performance Considerations

### Audio Processing

**Optimization:**
- Use efficient audio codecs
- Limit recording duration
- Process audio asynchronously
- Cache speech models in memory

**Example:**
```python
# Load model once at startup (not per request)
WHISPER_MODEL = whisper.load_model("base")

async def process_audio_async(audio_file):
    """Process audio without blocking."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        WHISPER_MODEL.transcribe,
        audio_file
    )
    return result["text"]
```

### Database Optimization

**Indexes:**
```sql
CREATE INDEX idx_attempts_user ON attempts(user_id);
CREATE INDEX idx_attempts_twister ON attempts(twister_id);
CREATE INDEX idx_attempts_score ON attempts(score DESC);
```

### Concurrent Sessions

**Handle Multiple Games:**
- Use session IDs to track separate games
- Isolate audio streams per player
- Queue speech recognition requests
- Limit concurrent sessions per server (e.g., max 3)

---

## Future Enhancements

### Phase 5+: Advanced Features

**Custom Twisters:**
- Players submit custom tongue twisters
- Community voting on quality
- Difficulty rating by attempts
- Report inappropriate submissions

**Achievements:**
- "Perfect Score" - 100% accuracy
- "Speed Demon" - Under 2 seconds
- "Persistent" - 100 attempts
- "Master" - Beat all insane twisters
- "Champion" - #1 on leaderboard

**Social Features:**
- Team challenges
- Guild vs Guild competitions
- Shared practice sessions
- Coach mode (spectate and give feedback)

**Advanced Scoring:**
- Pronunciation analysis
- Accent detection
- Speech clarity metrics
- Rhythm/pace scoring

---

## Appendix

### Example Session Flow

```
User: /twister join
Bot: "🎤 Joined voice channel! Use /twister start to begin!"

User: /twister start difficulty:medium
Bot: "Say: 'Peter Piper picked a peck of pickled peppers'"

[Player speaks into mic]

Bot: [Records 3 seconds of audio]
Bot: [Converts to text: "Peter Piper picked a peck of pickled peepers"]
Bot: [Calculates: 95% accuracy, 2.8 seconds]
Bot: [Scores: (950 + 500) * 1.5 = 2175 points]

Bot: "✅ Nice! 95% accuracy | 2.8s | 2,175 points
      Mistake: 'peepers' → 'peppers'
      Try again or /twister start for new challenge!"

User: /twister start
[Repeat...]

User: /twister challenge
Bot: "⚡ CHALLENGE MODE! 10 twisters, let's go!"
[10 rounds...]
Bot: "🏆 Total: 21,450 points! New personal best!"

User: /twister stats
Bot: [Shows detailed stats]

User: /twister leave
Bot: "👋 Thanks for playing! See you next time!"
```

---

## Resources

### Speech Recognition
- [SpeechRecognition Library](https://github.com/Uberi/speech_recognition)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text)

### Discord.py Voice
- [discord.py Voice Guide](https://discordpy.readthedocs.io/en/stable/api.html#voice-related)
- [Voice Receive Example](https://github.com/Rapptz/discord.py/blob/master/examples/voice_receive.py)

### Audio Processing
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [pydub Documentation](https://github.com/jiaaro/pydub)

---

## Version History

- **v0.1** - Initial design document
- **v1.0** - Phase 1 completion (core game + speech recognition)
- **v2.0** - Phase 2 completion (stats & leaderboards)
- **v3.0** - Phase 3 completion (competitive modes)

---

**End of Design Document**
