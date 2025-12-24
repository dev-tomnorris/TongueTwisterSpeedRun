"""Configuration constants for the Tongue Twister Bot."""

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

# Duel settings
DUEL_TIMEOUT = 120  # seconds to accept duel
DUEL_BEST_OF = 3  # best of 3 rounds

# Tournament settings
TOURNAMENT_SIZES = [4, 8, 16]

