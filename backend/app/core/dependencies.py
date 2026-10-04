"""FastAPI dependency injection providers.
Owned by: System Architecture

These dependencies are injected into route handlers using FastAPI's Depends() system.
They provide access to singleton service instances and enforce request validation.
"""
from fastapi import Depends, HTTPException, status
from app.models.document import DocumentMetadata
from app.services.ingestion import IngestionService, ingestion_service
from app.services.rag import RAGService, rag_service
from app.services.session import SessionService, session_service


def get_ingestion_service() -> IngestionService:
    return ingestion_service


def get_rag_service() -> RAGService:
    return rag_service


def get_session_service() -> SessionService:
    return session_service


def require_document(
    document_id: str,
    ing: IngestionService = Depends(get_ingestion_service),
) -> DocumentMetadata:
    """Dependency that 404s if document_id does not exist in the store."""
    doc = ing.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Document '{document_id}' not found.", "code": "DOCUMENT_NOT_FOUND"},
        )
    return doc
