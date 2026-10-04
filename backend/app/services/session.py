import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.core.config import settings
from app.models.chat import ChatSessionHistory, ChatTurn, Citation, SessionSummary

logger = logging.getLogger(__name__)


class SessionService:
    """
    Session manager backed by SQLite persistence with an in-memory cache
    for sub-millisecond retrieval and restart survival.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._sessions: Dict[str, List[ChatTurn]] = {}
        self._metadata: Dict[str, dict] = {}
        self.db_path = db_path or os.path.join(settings.upload_dir, "nimdoc_sessions.db")
        self._init_db()
        self._load_from_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        title TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_turns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        turn_index INTEGER,
                        question TEXT,
                        answer TEXT,
                        grounded INTEGER,
                        citations_json TEXT,
                        created_at TEXT,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
                    );
                    """
                )
                conn.commit()
        except Exception as e:
            logger.warning("Could not initialize SQLite session database (%s). Running in-memory mode.", e)

    def _load_from_db(self) -> None:
        try:
            if not os.path.exists(self.db_path):
                return
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Load sessions
                cursor.execute("SELECT session_id, title, created_at, updated_at FROM sessions")
                for sid, title, cat, uat in cursor.fetchall():
                    self._sessions[sid] = []
                    self._metadata[sid] = {
                        "title": title or "Conversation",
                        "created_at": datetime.fromisoformat(cat) if cat else datetime.utcnow(),
                        "updated_at": datetime.fromisoformat(uat) if uat else datetime.utcnow(),
                    }

                # Load turns
                cursor.execute(
                    "SELECT session_id, turn_index, question, answer, grounded, citations_json, created_at "
                    "FROM chat_turns ORDER BY turn_index ASC"
                )
                for sid, t_idx, q, a, gr, cit_json, cat in cursor.fetchall():
                    citations = []
                    if cit_json:
                        try:
                            cit_list = json.loads(cit_json)
                            citations = [Citation(**c) for c in cit_list]
                        except Exception:
                            citations = []
                    turn = ChatTurn(
                        turn_index=t_idx,
                        question=q,
                        answer=a,
                        citations=citations,
                        grounded=bool(gr),
                        created_at=datetime.fromisoformat(cat) if cat else datetime.utcnow(),
                    )
                    if sid in self._sessions:
                        self._sessions[sid].append(turn)
        except Exception as e:
            logger.warning("Failed loading sessions from SQLite (%s). Starting fresh.", e)

    def create_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> str:
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        session_title = title or "New Conversation"

        # Update in-memory
        if sid not in self._sessions:
            self._sessions[sid] = []
        self._metadata[sid] = {
            "title": session_title,
            "created_at": now,
            "updated_at": now,
        }

        # Persist to SQLite
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO sessions (session_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (sid, session_title, now.isoformat(), now.isoformat()),
                )
                conn.commit()
        except Exception as e:
            logger.warning("Error persisting session creation to SQLite: %s", e)

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

        # Persist to SQLite
        try:
            with self._get_connection() as conn:
                # Ensure session row exists
                conn.execute(
                    "INSERT OR IGNORE INTO sessions (session_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (session_id, self._metadata[session_id]["title"], now.isoformat(), now.isoformat()),
                )
                # Update session timestamp
                conn.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    (now.isoformat(), session_id),
                )
                # Insert turn
                citations_json = json.dumps([c.model_dump() for c in turn.citations])
                conn.execute(
                    """
                    INSERT INTO chat_turns (session_id, turn_index, question, answer, grounded, citations_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        turn.turn_index,
                        turn.question,
                        turn.answer,
                        1 if turn.grounded else 0,
                        citations_json,
                        turn.created_at.isoformat(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.warning("Error persisting chat turn to SQLite: %s", e)

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

        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM chat_turns WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
        except Exception as e:
            logger.warning("Error deleting session from SQLite: %s", e)

        return True


session_service = SessionService()
