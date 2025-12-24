"""Manages active game sessions."""

from typing import Optional, Dict
from game.session import TwisterSession
import uuid


class SessionManager:
    """Manages active tongue twister sessions."""
    
    def __init__(self):
        # Dictionary mapping (user_id, channel_id) to session
        self._sessions: Dict[tuple, TwisterSession] = {}
        # Dictionary mapping session_id to session
        self._sessions_by_id: Dict[str, TwisterSession] = {}
    
    def create_session(
        self,
        channel_id: str,
        server_id: str,
        player_id: str,
        player_name: str,
        mode: str = 'practice',
        **kwargs
    ) -> TwisterSession:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        
        session = TwisterSession(
            session_id=session_id,
            channel_id=channel_id,
            server_id=server_id,
            player_id=player_id,
            player_name=player_name,
            mode=mode,
            **kwargs
        )
        
        key = (player_id, channel_id)
        self._sessions[key] = session
        self._sessions_by_id[session_id] = session
        
        return session
    
    def get_session(self, user_id: str, channel_id: str) -> Optional[TwisterSession]:
        """Get an active session for a user in a channel."""
        key = (user_id, channel_id)
        session = self._sessions.get(key)
        
        if session and session.active:
            return session
        
        return None
    
    def get_session_by_id(self, session_id: str) -> Optional[TwisterSession]:
        """Get a session by its ID."""
        return self._sessions_by_id.get(session_id)
    
    def end_session(self, user_id: str, channel_id: str) -> Optional[TwisterSession]:
        """End a session."""
        key = (user_id, channel_id)
        session = self._sessions.get(key)
        
        if session:
            session.active = False
            from datetime import datetime
            session.ended_at = datetime.utcnow()
            del self._sessions[key]
            # Keep in _sessions_by_id for reference
        
        return session
    
    def is_active(self, user_id: str, channel_id: str) -> bool:
        """Check if a user has an active session."""
        session = self.get_session(user_id, channel_id)
        return session is not None
    
    def get_all_sessions(self) -> list[TwisterSession]:
        """Get all active sessions."""
        return [s for s in self._sessions.values() if s.active]


# Global session manager instance
session_manager = SessionManager()

