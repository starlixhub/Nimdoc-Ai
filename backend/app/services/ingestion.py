import os
import uuid
from typing import Dict, List, Optional
from app.core.config import settings
from app.models.document import DocumentMetadata
from app.services.chunking import chunking_service
from app.services.embedding import embedding_service
from app.services.extraction import extraction_service


class IngestionService:
    """Coordinates the document ingestion pipeline: extraction -> chunking -> embedding -> vector store."""

    def __init__(self):
        # In-memory document metadata store for MVP
        self._documents: Dict[str, DocumentMetadata] = {}

    async def ingest_document(self, file_name: str, file_path: str, file_size: int) -> DocumentMetadata:
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"

        doc_meta = DocumentMetadata(
            document_id=doc_id,
            document_name=file_name,
            file_size_bytes=file_size,
            file_path=file_path,
            status="processing",
        )
        self._documents[doc_id] = doc_meta

        try:
            # 1. Extract text
            pages = extraction_service.extract_text_from_pdf(file_path)
            doc_meta.page_count = len(pages)

            # 2. Chunk text
            chunks = chunking_service.chunk_pages(doc_id, file_name, pages)
            doc_meta.chunk_count = len(chunks)

            # 3. Embed chunks
            chunk_texts = [c["text"] for c in chunks]
            vectors = await embedding_service.embed_texts(chunk_texts)

            # 4. TODO: RAG developer stores vectors into Vector DB

            doc_meta.status = "ready"
        except Exception as e:
            doc_meta.status = "failed"
            raise e

        return doc_meta

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._documents.get(document_id)

    def list_documents(self) -> List[DocumentMetadata]:
        return list(self._documents.values())

    def delete_document(self, document_id: str) -> bool:
        if document_id in self._documents:
            del self._documents[document_id]
            # TODO: Vector DB chunk deletion
            return True
        return False


ingestion_service = IngestionService()
