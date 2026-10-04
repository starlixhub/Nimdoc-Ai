import asyncio
from fastapi import APIRouter, HTTPException, status
import httpx
from app.core.config import settings
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
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
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
        response = await asyncio.wait_for(
            rag_service.answer_question(
                question=request.question,
                document_ids=request.document_ids,
                session_id=request.session_id,
            ),
            timeout=float(settings.llm_timeout_seconds),
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
    except (asyncio.TimeoutError, httpx.TimeoutException):
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "LLM request timed out. Please try again.", "code": "GATEWAY_TIMEOUT"},
        )
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        if status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "LLM provider authentication failed. Check API key.", "code": "LLM_AUTH_FAILED"},
            )
        elif status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "LLM rate limit reached. Please wait and retry.", "code": "RATE_LIMIT_EXCEEDED"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": f"LLM provider error: {e.response.text}", "code": "UPSTREAM_ERROR"},
            )
    except HTTPException:
        raise
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
