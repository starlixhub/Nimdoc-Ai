from fastapi import APIRouter, HTTPException, status
from app.models.chat import (
    ChatSessionHistory,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionListResponse,
)
from app.models.common import ErrorResponse
from app.services.session import session_service

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_session(request: SessionCreateRequest = None):
    req = request or SessionCreateRequest()
    sid = session_service.create_session(session_id=req.session_id, title=req.title)
    return SessionCreateResponse(
        session_id=sid,
        title=req.title or "New Conversation",
        message="Chat session created successfully.",
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions():
    summaries = session_service.list_sessions()
    return SessionListResponse(sessions=summaries, total=len(summaries))


@router.get(
    "/{session_id}",
    response_model=ChatSessionHistory,
    responses={404: {"model": ErrorResponse}},
)
async def get_session(session_id: str):
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Session '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
        )
    return session


@router.delete(
    "/{session_id}",
    response_model=SessionDeleteResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_session(session_id: str):
    deleted = session_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Session '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
        )
    return SessionDeleteResponse(session_id=session_id, message="Session deleted successfully.")
