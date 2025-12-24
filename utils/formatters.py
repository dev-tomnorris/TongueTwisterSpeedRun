"""Text formatting helpers."""

from typing import List


def format_time(seconds: float) -> str:
    """Format time in seconds to readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def format_score(score: int) -> str:
    """Format score with commas."""
    return f"{score:,}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage."""
    return f"{value:.{decimals}f}%"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_list(items: List[str], separator: str = ", ", last_separator: str = " and ") -> str:
    """Format a list of items with proper separators."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]}{last_separator}{items[1]}"
    
    return separator.join(items[:-1]) + f"{last_separator}{items[-1]}"

