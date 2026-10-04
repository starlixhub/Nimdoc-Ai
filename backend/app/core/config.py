from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Nebius / NVIDIA Configuration
    nebius_api_key: str = "mock_nebius_key"
    nebius_api_base_url: str = "https://api.tokenfactory.nebius.ai/v1"
    llm_model_name: str = "nvidia/meta-llama-3.1-8b-instruct"

    # RAG & Embedding Settings
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_db_url: str = "http://localhost:6333"
    vector_db_collection: str = "nimdoc_documents"
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 5
    min_relevance_score: float = 0.5

    # Storage & Uploads
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # Server & Runtime
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
