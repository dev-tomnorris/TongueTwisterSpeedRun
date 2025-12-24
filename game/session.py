"""Game session data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class TwisterSession:
    """Represents an active tongue twister session."""
    session_id: str
    channel_id: str
    server_id: str
    player_id: str
    player_name: str
    
    # Session type
    mode: str  # 'practice', 'timed_challenge', 'duel', 'tournament'
    
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
    
    # For duels
    opponent_id: Optional[str] = None
    opponent_name: Optional[str] = None
    round_number: int = 0
    player_score: int = 0
    opponent_score: int = 0
    rounds_to_win: int = 2  # Best of 3
    
    # For tournaments
    tournament_id: Optional[str] = None
    bracket_position: Optional[int] = None
    
    # Challenge results
    challenge_results: List[Dict] = field(default_factory=list)
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

