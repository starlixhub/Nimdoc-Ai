from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    document_name: str
    file_type: str = "pdf"
    file_size_bytes: int
    page_count: Optional[int] = None
    status: str = Field(..., description="'processing', 'ready', or 'failed'")
    chunk_count: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentUploadResponse(BaseModel):
    document_id: str
    document_name: str
    status: str = "processing"
    message: str = "Document uploaded successfully. Processing has started."
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total: int


class DocumentDeleteResponse(BaseModel):
    document_id: str
    document_name: str
    message: str = "Document deleted successfully. All associated data has been removed."
    deleted_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentSummaryRequest(BaseModel):
    focus: Optional[str] = None


class DocumentSummaryResponse(BaseModel):
    document_id: str
    document_name: str
    summary: str
    citations: List["Citation"] = []
    grounded: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Forward ref resolution
from app.models.chat import Citation  # noqa: E402
DocumentSummaryResponse.model_rebuild()
