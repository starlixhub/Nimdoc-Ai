from typing import Any, Dict, List
from app.models.chat import Citation


class CitationService:
    """Service to create clean, structured Citation objects from retrieved chunk metadata."""

    @staticmethod
    def build_citations_from_chunks(chunks: List[Dict[str, Any]]) -> List[Citation]:
        citations: List[Citation] = []
        seen_keys = set()

        for chunk in chunks:
            doc_id = chunk.get("document_id", "unknown_doc")
            doc_name = chunk.get("document_name", "Unknown Document")
            page = chunk.get("page")
            text = chunk.get("text", "")

            # Deduplicate citations if the exact same page & doc appears
            key = (doc_id, page, text[:60])
            if key not in seen_keys:
                seen_keys.add(key)
                citations.append(
                    Citation(
                        document_id=doc_id,
                        document_name=doc_name,
                        page=page,
                        text=text.strip(),
                    )
                )

        return citations
