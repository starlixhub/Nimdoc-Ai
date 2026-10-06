from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    document_name: str
    page: Optional[int] = None
    text: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The natural-language question from the user")
    document_ids: List[str] = Field(..., min_length=1, description="List of document IDs to query against")
    session_id: str = Field(..., min_length=1, description="Unique session identifier for multi-turn conversation")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation] = []
    grounded: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatTurn(BaseModel):
    turn_index: int
    question: str
    answer: str
    citations: List[Citation] = []
    grounded: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSessionHistory(BaseModel):
    session_id: str
    turns: List[ChatTurn] = []
    turn_count: int = 0


class SessionSummary(BaseModel):
    session_id: str
    title: Optional[str] = None
    turn_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionCreateRequest(BaseModel):
    title: Optional[str] = None
    session_id: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: str = "Chat session created successfully."


class SessionListResponse(BaseModel):
    sessions: List[SessionSummary]
    total: int


class SessionDeleteResponse(BaseModel):
    session_id: str
    message: str = "Session deleted successfully."
