from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.core.config import settings


class BaseRetrievalService(ABC):
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        document_ids: List[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve the top-K relevant chunks matching the query filtered by document_ids."""
        pass


class RetrievalService(BaseRetrievalService):
    """
    Retrieval service interfacing with Vector DB.
    Owned and finalized by the RAG Developer.
    """

    def __init__(self):
        self.vector_db_url = settings.vector_db_url
        self.collection = settings.vector_db_collection

    async def retrieve(
        self,
        query: str,
        document_ids: List[str],
        top_k: int = settings.top_k_retrieval,
    ) -> List[Dict[str, Any]]:
        # TODO: RAG Developer hooks up actual Vector Database search (Qdrant / Chroma)
        # Mocking retrieved chunk for development & testing
        return [
            {
                "document_id": document_ids[0] if document_ids else "doc_123",
                "document_name": "project_guidelines.pdf",
                "page": 4,
                "text": "All projects must be submitted by October 15. Late submissions will receive penalties.",
                "score": 0.89,
            }
        ]


retrieval_service = RetrievalService()
