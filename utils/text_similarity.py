"""Text normalization and similarity calculations."""

import re
from typing import List, Set, Dict
from difflib import SequenceMatcher

# Number to word mappings - handles when Whisper transcribes numbers as digits
NUMBER_TO_WORD: Dict[str, str] = {
    '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
    '10': 'ten', '11': 'eleven', '12': 'twelve', '13': 'thirteen',
    '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
    '18': 'eighteen', '19': 'nineteen', '20': 'twenty',
    '30': 'thirty', '40': 'forty', '50': 'fifty', '60': 'sixty',
    '70': 'seventy', '80': 'eighty', '90': 'ninety',
    '100': 'hundred', '1000': 'thousand',
}

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
    'seaward': {'seaward', 'seward'},
    'seward': {'seaward', 'seward'},
    'six': {'six', '6'},
    '6': {'six', '6'},
    'sixth': {'sixth', '6th'},
    '6th': {'sixth', '6th'},
}

# Create reverse lookup: word -> canonical form (first word in group)
HOMOPHONE_MAP: Dict[str, str] = {}
for canonical, group in HOMOPHONE_GROUPS.items():
    for word in group:
        HOMOPHONE_MAP[word] = canonical


def convert_numbers_to_words(text: str) -> str:
    """
    Convert numeric digits to their word equivalents.
    
    Handles standalone numbers like "6" -> "six"
    """
    words = text.split()
    converted_words = []
    
    for word in words:
        # Check if word is a pure number (digits only)
        if word.isdigit():
            # Convert number to word if we have a mapping
            word_lower = word.lower()
            if word_lower in NUMBER_TO_WORD:
                converted_words.append(NUMBER_TO_WORD[word_lower])
            else:
                # For numbers not in our mapping, try to keep as-is
                # but we could add more sophisticated number-to-word conversion
                converted_words.append(word)
        else:
            # Check for numbers with suffixes like "6th" -> "sixth"
            # Match pattern: digits followed by letters (like "6th", "1st", etc.)
            match = re.match(r'^(\d+)([a-z]+)$', word.lower())
            if match:
                num_part = match.group(1)
                suffix = match.group(2)
                if num_part in NUMBER_TO_WORD:
                    # Convert "6th" -> "sixth", "1st" -> "first", etc.
                    base_word = NUMBER_TO_WORD[num_part]
                    # Handle common ordinal suffixes
                    if suffix in ['th', 'st', 'nd', 'rd']:
                        if base_word.endswith('y'):
                            # "twenty" -> "twentieth"
                            ordinal = base_word[:-1] + 'ieth'
                        elif base_word.endswith('one'):
                            ordinal = base_word[:-3] + 'first'
                        elif base_word.endswith('two'):
                            ordinal = base_word[:-3] + 'second'
                        elif base_word.endswith('three'):
                            ordinal = base_word[:-5] + 'third'
                        elif base_word.endswith('five'):
                            ordinal = base_word[:-4] + 'fifth'
                        elif base_word.endswith('eight'):
                            ordinal = base_word[:-1] + 'h'
                        elif base_word.endswith('nine'):
                            ordinal = base_word[:-1]
                        else:
                            ordinal = base_word + suffix
                        converted_words.append(ordinal)
                    else:
                        converted_words.append(base_word + suffix)
                else:
                    converted_words.append(word)
            else:
                converted_words.append(word)
    
    return ' '.join(converted_words)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    
    - Convert to lowercase
    - Convert numbers to words (6 -> six)
    - Remove punctuation (except spaces)
    - Collapse multiple spaces
    - Strip leading/trailing spaces
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Convert numbers to words BEFORE removing punctuation
    # This way "6" becomes "six" before we strip it
    text = convert_numbers_to_words(text)
    
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

