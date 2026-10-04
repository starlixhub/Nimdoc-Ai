from fastapi import APIRouter, HTTPException, status
from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionHistory,
    ChatTurn,
)
from app.models.common import ErrorResponse
from app.services.rag import rag_service
from app.services.session import session_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Question cannot be empty.", "code": "INVALID_REQUEST"},
        )
    if not request.document_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "At least one document_id must be provided.", "code": "INVALID_REQUEST"},
        )

    try:
        response = await rag_service.answer_question(
            question=request.question,
            document_ids=request.document_ids,
            session_id=request.session_id,
        )

        # Record conversation turn in session history
        turn_index = 1
        existing_session = session_service.get_session(request.session_id)
        if existing_session:
            turn_index = len(existing_session.turns) + 1

        session_service.add_turn(
            request.session_id,
            ChatTurn(
                turn_index=turn_index,
                question=request.question,
                answer=response.answer,
                citations=response.citations,
                grounded=response.grounded,
            ),
        )

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to process chat query: {str(e)}", "code": "INTERNAL_ERROR"},
        )


@router.get(
    "/{session_id}",
    response_model=ChatSessionHistory,
    responses={404: {"model": ErrorResponse}},
)
async def get_session_history(session_id: str):
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Session '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
        )
    return session
