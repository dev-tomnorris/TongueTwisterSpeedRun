"""Text normalization and similarity calculations."""

import re
from typing import List
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    
    - Convert to lowercase
    - Remove punctuation (except spaces)
    - Collapse multiple spaces
    - Strip leading/trailing spaces
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation except spaces
    text = re.sub(r'[^\w\s]', '', text)
    
    # Collapse multiple spaces into single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing spaces
    text = text.strip()
    
    return text


def calculate_accuracy(spoken: str, target: str) -> float:
    """
    Calculate similarity between spoken and target text.
    
    Returns accuracy as a percentage (0.0 to 100.0).
    """
    if not spoken or not target:
        return 0.0
    
    # Normalize both texts
    spoken_normalized = normalize_text(spoken)
    target_normalized = normalize_text(target)
    
    if not spoken_normalized or not target_normalized:
        return 0.0
    
    # Calculate similarity ratio (0.0 to 1.0)
    similarity = SequenceMatcher(None, spoken_normalized, target_normalized).ratio()
    
    # Return as percentage
    return similarity * 100.0


def find_differences(spoken: str, target: str) -> List[str]:
    """
    Find word-level differences between spoken and target text.
    
    Returns a list of mistake descriptions.
    """
    spoken_normalized = normalize_text(spoken)
    target_normalized = normalize_text(target)
    
    spoken_words = spoken_normalized.split()
    target_words = target_normalized.split()
    
    mistakes = []
    
    # Simple word-by-word comparison
    max_len = max(len(spoken_words), len(target_words))
    for i in range(max_len):
        if i >= len(spoken_words):
            mistakes.append(f"Missing word: '{target_words[i]}'")
        elif i >= len(target_words):
            mistakes.append(f"Extra word: '{spoken_words[i]}'")
        elif spoken_words[i] != target_words[i]:
            mistakes.append(f"'{spoken_words[i]}' → '{target_words[i]}'")
    
    return mistakes

