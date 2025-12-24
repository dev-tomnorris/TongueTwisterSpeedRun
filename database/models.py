"""Database models and schemas."""

# SQL schemas for all tables

CREATE_PLAYERS_TABLE = """
CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    best_score INTEGER DEFAULT 0,
    best_score_twister_id INTEGER,
    fastest_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP
);
"""

CREATE_ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS attempts (
    attempt_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    twister_id INTEGER NOT NULL,
    spoken_text TEXT,
    accuracy REAL,
    time_seconds REAL,
    score INTEGER,
    difficulty TEXT,
    session_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES players(user_id)
);
"""

CREATE_TONGUE_TWISTERS_TABLE = """
CREATE TABLE IF NOT EXISTS tongue_twisters (
    twister_id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    word_count INTEGER,
    focus_sounds TEXT,
    times_attempted INTEGER DEFAULT 0,
    average_accuracy REAL DEFAULT 0.0,
    created_by TEXT,
    is_official BOOLEAN DEFAULT TRUE
);
"""

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    server_id TEXT,
    channel_id TEXT,
    session_type TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_attempts INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES players(user_id)
);
"""

CREATE_DAILY_CHALLENGES_TABLE = """
CREATE TABLE IF NOT EXISTS daily_challenges (
    challenge_date DATE PRIMARY KEY,
    twister_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_DAILY_CHALLENGE_ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS daily_challenge_attempts (
    attempt_id TEXT PRIMARY KEY,
    challenge_date DATE NOT NULL,
    user_id TEXT NOT NULL,
    score INTEGER,
    accuracy REAL,
    time_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES players(user_id),
    FOREIGN KEY (challenge_date) REFERENCES daily_challenges(challenge_date)
);
"""

CREATE_ACHIEVEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS achievements (
    achievement_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT
);
"""

CREATE_PLAYER_ACHIEVEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS player_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES players(user_id),
    FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id),
    UNIQUE(user_id, achievement_id)
);
"""

CREATE_DUELS_TABLE = """
CREATE TABLE IF NOT EXISTS duels (
    duel_id TEXT PRIMARY KEY,
    challenger_id TEXT NOT NULL,
    opponent_id TEXT NOT NULL,
    winner_id TEXT,
    rounds_to_win INTEGER DEFAULT 2,
    challenger_wins INTEGER DEFAULT 0,
    opponent_wins INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (challenger_id) REFERENCES players(user_id),
    FOREIGN KEY (opponent_id) REFERENCES players(user_id)
);
"""

CREATE_TOURNAMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    bracket_size INTEGER,
    winner_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
"""

# Indexes for performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempts_twister ON attempts(twister_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempts_score ON attempts(score DESC);",
    "CREATE INDEX IF NOT EXISTS idx_attempts_created ON attempts(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_daily_attempts_date ON daily_challenge_attempts(challenge_date);",
    "CREATE INDEX IF NOT EXISTS idx_daily_attempts_user ON daily_challenge_attempts(user_id);",
]

