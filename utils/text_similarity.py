"""Text normalization and similarity calculations."""

import re
from typing import List, Set, Dict
from difflib import SequenceMatcher

# Homophone mappings - words that sound the same but are spelled differently
# This helps handle transcription errors where Whisper picks the wrong spelling
HOMOPHONE_GROUPS: Dict[str, Set[str]] = {
    'lorry': {'lorry', 'lori', 'lory', 'lowry'},
    'lori': {'lorry', 'lori', 'lory', 'lowry'},
    'lory': {'lorry', 'lori', 'lory', 'lowry'},
    'lowry': {'lorry', 'lori', 'lory', 'lowry'},
    'red': {'red', 'read'},
    'read': {'red', 'read'},
    'yellow': {'yellow', 'yello'},
    'yello': {'yellow', 'yello'},
    'she': {'she', 'shee'},
    'shee': {'she', 'shee'},
    'sells': {'sells', 'sels', 'cells'},
    'sels': {'sells', 'sels', 'cells'},
    'cells': {'sells', 'sels', 'cells'},
    'seashells': {'seashells', 'sea shells', 'seashell', 'sea shell'},
    'seashell': {'seashells', 'sea shells', 'seashell', 'sea shell'},
    'sea shells': {'seashells', 'sea shells', 'seashell', 'sea shell'},
    'sea shell': {'seashells', 'sea shells', 'seashell', 'sea shell'},
    'by': {'by', 'buy', 'bye'},
    'buy': {'by', 'buy', 'bye'},
    'bye': {'by', 'buy', 'bye'},
    'the': {'the', 'thee'},
    'thee': {'the', 'thee'},
    'seashore': {'seashore', 'sea shore', 'seashor'},
    'sea shore': {'seashore', 'sea shore', 'seashor'},
    'seashor': {'seashore', 'sea shore', 'seashor'},
}

# Create reverse lookup: word -> canonical form (first word in group)
HOMOPHONE_MAP: Dict[str, str] = {}
for canonical, group in HOMOPHONE_GROUPS.items():
    for word in group:
        HOMOPHONE_MAP[word] = canonical


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


def are_homophones(word1: str, word2: str) -> bool:
    """
    Check if two words are homophones (sound the same).
    
    Args:
        word1: First word (normalized, lowercase)
        word2: Second word (normalized, lowercase)
    
    Returns:
        True if words are homophones
    """
    if word1 == word2:
        return True
    
    # Check if both words are in the same homophone group
    canonical1 = HOMOPHONE_MAP.get(word1, word1)
    canonical2 = HOMOPHONE_MAP.get(word2, word2)
    
    if canonical1 == canonical2:
        return True
    
    # Check if they're in the same group
    group1 = HOMOPHONE_GROUPS.get(canonical1, set())
    group2 = HOMOPHONE_GROUPS.get(canonical2, set())
    
    return bool(group1 & group2)  # Intersection is non-empty


def calculate_accuracy(spoken: str, target: str) -> float:
    """
    Calculate similarity between spoken and target text.
    
    Uses word-level matching with homophone awareness for better accuracy.
    Returns accuracy as a percentage (0.0 to 100.0).
    """
    if not spoken or not target:
        return 0.0
    
    # Normalize both texts
    spoken_normalized = normalize_text(spoken)
    target_normalized = normalize_text(target)
    
    if not spoken_normalized or not target_normalized:
        return 0.0
    
    # Word-level matching with homophone awareness
    spoken_words = spoken_normalized.split()
    target_words = target_normalized.split()
    
    if not spoken_words or not target_words:
        # Fallback to string similarity if no words
        similarity = SequenceMatcher(None, spoken_normalized, target_normalized).ratio()
        return similarity * 100.0
    
    # Count matching words (including homophones)
    matches = 0
    max_len = max(len(spoken_words), len(target_words))
    
    for i in range(max_len):
        if i >= len(spoken_words) or i >= len(target_words):
            # Missing or extra word
            continue
        
        spoken_word = spoken_words[i]
        target_word = target_words[i]
        
        if spoken_word == target_word:
            matches += 1
        elif are_homophones(spoken_word, target_word):
            matches += 1  # Homophones count as matches
    
    # Word-level accuracy
    word_accuracy = matches / max_len if max_len > 0 else 0.0
    
    # Also calculate character-level similarity for fine-tuning
    char_similarity = SequenceMatcher(None, spoken_normalized, target_normalized).ratio()
    
    # Weighted combination: 70% word accuracy, 30% character similarity
    # This gives more weight to getting words right (including homophones)
    final_accuracy = (word_accuracy * 0.7) + (char_similarity * 0.3)
    
    return final_accuracy * 100.0


def find_differences(spoken: str, target: str) -> List[str]:
    """
    Find word-level differences between spoken and target text.
    
    Returns a list of mistake descriptions.
    Homophones are not counted as mistakes.
    """
    spoken_normalized = normalize_text(spoken)
    target_normalized = normalize_text(target)
    
    spoken_words = spoken_normalized.split()
    target_words = target_normalized.split()
    
    mistakes = []
    
    # Word-by-word comparison with homophone awareness
    max_len = max(len(spoken_words), len(target_words))
    for i in range(max_len):
        if i >= len(spoken_words):
            mistakes.append(f"Missing word: '{target_words[i]}'")
        elif i >= len(target_words):
            mistakes.append(f"Extra word: '{spoken_words[i]}'")
        else:
            spoken_word = spoken_words[i]
            target_word = target_words[i]
            
            if spoken_word != target_word:
                if are_homophones(spoken_word, target_word):
                    # Homophone - note it but don't count as mistake
                    mistakes.append(f"'{spoken_word}' (homophone of '{target_word}') ✓")
                else:
                    mistakes.append(f"'{spoken_word}' → '{target_words[i]}'")
    
    return mistakes

