import os
import shutil
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.core.config import settings
from app.models.common import ErrorResponse
from app.models.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentSummaryRequest,
    DocumentSummaryResponse,
    DocumentUploadResponse,
)
from app.services.ingestion import ingestion_service

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def upload_document(file: UploadFile = File(...)):
    # 1. Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "File type is not supported. Supported types: pdf", "code": "UNSUPPORTED_FILE_TYPE"},
        )

    # 2. Ensure upload dir exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    temp_path = os.path.join(settings.upload_dir, file.filename)

    # 3. Save file locally
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(temp_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to save uploaded file: {str(e)}", "code": "INTERNAL_ERROR"},
        )

    # 4. Check file size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": f"File size exceeds maximum limit of {settings.max_upload_size_mb}MB", "code": "FILE_TOO_LARGE"},
        )

    # 5. Ingest document
    try:
        doc_meta = await ingestion_service.ingest_document(
            file_name=file.filename,
            file_path=temp_path,
            file_size=file_size,
        )
        return DocumentUploadResponse(
            document_id=doc_meta.document_id,
            document_name=doc_meta.document_name,
            status=doc_meta.status,
            message="Document uploaded successfully. Processing has started.",
            uploaded_at=doc_meta.uploaded_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": f"Document processing failed: {str(e)}", "code": "PROCESSING_FAILED"},
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    docs = ingestion_service.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    responses={404: {"model": ErrorResponse}},
)
async def get_document(document_id: str):
    doc = ingestion_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Document '{document_id}' not found.", "code": "DOCUMENT_NOT_FOUND"},
        )
    return doc


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_document(document_id: str):
    doc = ingestion_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Document '{document_id}' not found.", "code": "DOCUMENT_NOT_FOUND"},
        )
    ingestion_service.delete_document(document_id)
    return DocumentDeleteResponse(
        document_id=doc.document_id,
        document_name=doc.document_name,
    )


@router.post(
    "/{document_id}/summary",
    response_model=DocumentSummaryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def summarize_document(document_id: str, request: DocumentSummaryRequest = None):
    doc = ingestion_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Document '{document_id}' not found.", "code": "DOCUMENT_NOT_FOUND"},
        )

    # Mock summary output for MVP scaffolding
    return DocumentSummaryResponse(
        document_id=doc.document_id,
        document_name=doc.document_name,
        summary=f"This document '{doc.document_name}' contains {doc.page_count or 1} pages detailing project specifications, guidelines, and deadlines.",
        citations=[],
        grounded=True,
    )
