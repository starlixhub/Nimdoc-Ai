from typing import Any, Dict, List
from app.core.config import settings


class ChunkingService:
    """Splits extracted text into overlapping chunks with metadata."""

    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

    def chunk_pages(
        self,
        document_id: str,
        document_name: str,
        pages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        chunks = []
        chunk_index = 0

        for page_data in pages:
            page_num = page_data.get("page")
            text = page_data.get("text", "")
            if not text.strip():
                continue

            # Simple character/word sliding window
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]

                chunks.append({
                    "chunk_id": f"{document_id}_{chunk_index}",
                    "chunk_index": chunk_index,
                    "document_id": document_id,
                    "document_name": document_name,
                    "page": page_num,
                    "text": chunk_text,
                })
                chunk_index += 1
                start += self.chunk_size - self.chunk_overlap

        return chunks


chunking_service = ChunkingService()
