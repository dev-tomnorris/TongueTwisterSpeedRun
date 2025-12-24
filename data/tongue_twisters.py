"""Tongue twister library with 20 starter twisters."""

from typing import List, Dict, Optional
import random

# All 20 tongue twisters
TWISTERS = [
    # Easy (1-7)
    {
        'id': 1,
        'text': 'She sells seashells by the seashore',
        'difficulty': 'easy',
        'word_count': 6,
        'focus_sounds': 'S sounds'
    },
    {
        'id': 2,
        'text': 'Rubber baby buggy bumpers',
        'difficulty': 'easy',
        'word_count': 4,
        'focus_sounds': 'B sounds'
    },
    {
        'id': 3,
        'text': 'Unique New York',
        'difficulty': 'easy',
        'word_count': 3,
        'focus_sounds': 'U/Y sounds'
    },
    {
        'id': 4,
        'text': 'Toy boat toy boat',
        'difficulty': 'easy',
        'word_count': 4,
        'focus_sounds': 'T/B sounds'
    },
    {
        'id': 5,
        'text': 'Red lorry yellow lorry',
        'difficulty': 'easy',
        'word_count': 4,
        'focus_sounds': 'L/R sounds'
    },
    {
        'id': 6,
        'text': 'Greek grapes Greek grapes',
        'difficulty': 'easy',
        'word_count': 4,
        'focus_sounds': 'GR sounds'
    },
    {
        'id': 7,
        'text': 'Which witch is which',
        'difficulty': 'easy',
        'word_count': 4,
        'focus_sounds': 'WH sounds'
    },
    # Medium (8-14)
    {
        'id': 8,
        'text': 'Peter Piper picked a peck of pickled peppers',
        'difficulty': 'medium',
        'word_count': 8,
        'focus_sounds': 'P sounds'
    },
    {
        'id': 9,
        'text': 'How much wood would a woodchuck chuck',
        'difficulty': 'medium',
        'word_count': 7,
        'focus_sounds': 'W/CH sounds'
    },
    {
        'id': 10,
        'text': 'Red leather yellow leather red leather yellow leather',
        'difficulty': 'medium',
        'word_count': 8,
        'focus_sounds': 'L/R sounds'
    },
    {
        'id': 11,
        'text': "Betty Botter bought some butter but she said the butter's bitter",
        'difficulty': 'medium',
        'word_count': 11,
        'focus_sounds': 'B/T sounds'
    },
    {
        'id': 12,
        'text': 'I scream you scream we all scream for ice cream',
        'difficulty': 'medium',
        'word_count': 10,
        'focus_sounds': 'SCR sounds'
    },
    {
        'id': 13,
        'text': 'Fuzzy Wuzzy was a bear Fuzzy Wuzzy had no hair',
        'difficulty': 'medium',
        'word_count': 10,
        'focus_sounds': 'F/Z sounds'
    },
    {
        'id': 14,
        'text': 'Six slippery snails slid slowly seaward',
        'difficulty': 'medium',
        'word_count': 6,
        'focus_sounds': 'S/SL sounds'
    },
    # Hard (15-18)
    {
        'id': 15,
        'text': "The sixth sick sheik's sixth sheep's sick",
        'difficulty': 'hard',
        'word_count': 7,
        'focus_sounds': 'S/SH/TH sounds'
    },
    {
        'id': 16,
        'text': 'I saw Susie sitting in a shoeshine shop',
        'difficulty': 'hard',
        'word_count': 9,
        'focus_sounds': 'S/SH sounds'
    },
    {
        'id': 17,
        'text': 'Lesser leather never weathered wetter weather better',
        'difficulty': 'hard',
        'word_count': 7,
        'focus_sounds': 'L/W/TH sounds'
    },
    {
        'id': 18,
        'text': 'Brisk brave brigadiers brandished broad bright blades',
        'difficulty': 'hard',
        'word_count': 7,
        'focus_sounds': 'BR/BL sounds'
    },
    # Insane (19-20)
    {
        'id': 19,
        'text': 'Pad kid poured curd pulled cod',
        'difficulty': 'insane',
        'word_count': 6,
        'focus_sounds': 'Multiple clusters'
    },
    {
        'id': 20,
        'text': 'The seething sea ceaseth and thus the seething sea sufficeth us',
        'difficulty': 'insane',
        'word_count': 11,
        'focus_sounds': 'S/TH/C sounds'
    },
]


def get_twister_by_id(twister_id: int) -> Optional[Dict]:
    """Get a tongue twister by its ID."""
    for twister in TWISTERS:
        if twister['id'] == twister_id:
            return twister
    return None


def get_twisters_by_difficulty(difficulty: str) -> List[Dict]:
    """Get all tongue twisters of a specific difficulty."""
    return [t for t in TWISTERS if t['difficulty'].lower() == difficulty.lower()]


def get_random_twister(difficulty: Optional[str] = None) -> Dict:
    """Get a random tongue twister, optionally filtered by difficulty."""
    if difficulty:
        twisters = get_twisters_by_difficulty(difficulty)
        if not twisters:
            # Fallback to all twisters if difficulty not found
            twisters = TWISTERS
    else:
        twisters = TWISTERS
    
    return random.choice(twisters)


def get_all_twisters() -> List[Dict]:
    """Get all tongue twisters."""
    return TWISTERS


def get_twister_count() -> int:
    """Get the total number of tongue twisters."""
    return len(TWISTERS)

