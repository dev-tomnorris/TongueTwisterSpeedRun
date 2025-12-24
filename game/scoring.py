"""Scoring calculations for tongue twister attempts."""

import config


def calculate_score(accuracy: float, time_seconds: float, difficulty: str) -> int:
    """
    Calculate final score based on accuracy, speed, and difficulty.
    
    Args:
        accuracy: Accuracy percentage (0-100)
        time_seconds: Time taken in seconds
        difficulty: Difficulty level (easy, medium, hard, insane)
    
    Returns:
        Final score as integer
    """
    # Base score from accuracy (0-1000)
    base_score = accuracy * 10
    
    # Speed bonus
    speed_bonus = 0
    if time_seconds < 3:
        speed_bonus = config.SPEED_BONUSES[3]
    elif time_seconds < 5:
        speed_bonus = config.SPEED_BONUSES[5]
    elif time_seconds < 8:
        speed_bonus = config.SPEED_BONUSES[8]
    
    # Difficulty multiplier
    multiplier = config.DIFFICULTY_MULTIPLIERS.get(difficulty.lower(), 1.0)
    
    # Calculate final score
    final_score = int((base_score + speed_bonus) * multiplier)
    
    return max(0, final_score)  # Ensure non-negative


def is_successful_attempt(accuracy: float) -> bool:
    """Check if an attempt meets the minimum accuracy threshold."""
    return accuracy >= config.MIN_ACCURACY_SUCCESS

