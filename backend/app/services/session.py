import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.models.chat import ChatSessionHistory, ChatTurn, SessionSummary


class SessionService:
    """In-memory session manager for storing chat turns and metadata."""

    def __init__(self):
        self._sessions: Dict[str, List[ChatTurn]] = {}
        self._metadata: Dict[str, dict] = {}

    def create_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> str:
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        if sid not in self._sessions:
            self._sessions[sid] = []
        self._metadata[sid] = {
            "title": title or "New Conversation",
            "created_at": now,
            "updated_at": now,
        }
        return sid

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
        now = datetime.utcnow()
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            self._metadata[session_id] = {
                "title": turn.question[:40] + ("..." if len(turn.question) > 40 else ""),
                "created_at": now,
                "updated_at": now,
            }
        self._sessions[session_id].append(turn)
        if session_id in self._metadata:
            self._metadata[session_id]["updated_at"] = now

    def list_sessions(self) -> List[SessionSummary]:
        summaries = []
        for sid, turns in self._sessions.items():
            meta = self._metadata.get(
                sid,
                {
                    "title": "Conversation",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )
            summaries.append(
                SessionSummary(
                    session_id=sid,
                    title=meta.get("title"),
                    turn_count=len(turns),
                    created_at=meta.get("created_at"),
                    updated_at=meta.get("updated_at"),
                )
            )
        summaries.sort(key=lambda s: s.updated_at, reverse=True)
        return summaries

    def delete_session(self, session_id: str) -> bool:
        if session_id not in self._sessions:
            return False
        del self._sessions[session_id]
        if session_id in self._metadata:
            del self._metadata[session_id]
        return True


session_service = SessionService()
