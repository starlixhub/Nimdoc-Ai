from abc import ABC, abstractmethod
from typing import List
from app.core.config import settings


class BaseEmbeddingService(ABC):
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of text strings."""
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate an embedding vector for a single query."""
        pass


class EmbeddingService(BaseEmbeddingService):
    """
    Embedding service to be finalized by the RAG Developer.
    Provides dummy vector generator for initial API scaffolding.
    """

    def __init__(self):
        self.model_name = settings.embedding_model_name

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # TODO: RAG Developer replaces with sentence-transformers or embedding model API
        return [[0.0] * 384 for _ in texts]

    async def embed_query(self, query: str) -> List[float]:
        return [0.0] * 384


embedding_service = EmbeddingService()
