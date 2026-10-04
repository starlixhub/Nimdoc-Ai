from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.core.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NimDoc AI starting — environment=%s", settings.environment)
    logger.info("LLM model configured: %s", settings.llm_model_name)
    logger.info("Vector DB configured: %s (collection: %s)", settings.vector_db_url, settings.vector_db_collection)
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("Upload directory verified: %s", settings.upload_dir)
    yield
    logger.info("NimDoc AI shutting down...")


app = FastAPI(
    title="NimDoc AI API",
    description="Backend API for NimDoc AI - Private Document Q&A with Grounded Citations. Built for Nebius x NVIDIA Hackathon.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents_router)
app.include_router(chat_router)



@app.get("/health", tags=["Health"])
async def health_check():
    llm_status = "ok" if settings.nebius_api_key and not settings.nebius_api_key.startswith("mock_") else "mock_mode"
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.environment,
        "services": {
            "vector_db": "mock_mode",  # Replaced with live check once Vector DB is connected by RAG Developer
            "llm": llm_status,
        },
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to NimDoc AI API. Visit /docs for interactive Swagger API documentation.",
        "docs_url": "/docs",
    }

