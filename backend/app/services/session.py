from typing import Dict, List, Optional
from app.models.chat import ChatSessionHistory, ChatTurn


class SessionService:
    """In-memory session manager for storing chat turns during the MVP."""

    def __init__(self):
        self._sessions: Dict[str, List[ChatTurn]] = {}

    def get_session(self, session_id: str) -> Optional[ChatSessionHistory]:
        if session_id not in self._sessions:
            return None
        turns = self._sessions[session_id]
        return ChatSessionHistory(
            session_id=session_id,
            turns=turns,
            turn_count=len(turns),
        )

    def add_turn(self, session_id: str, turn: ChatTurn) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(turn)

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())


session_service = SessionService()
