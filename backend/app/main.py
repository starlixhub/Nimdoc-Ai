from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.core.config import settings

app = FastAPI(
    title="NimDoc AI API",
    description="Backend API for NimDoc AI - Private Document Q&A with Grounded Citations. Built for Nebius x NVIDIA Hackathon.",
    version="0.1.0",
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
    return {
        "status": "ok",
        "version": "0.1.0",
        "services": {
            "vector_db": "ok",
            "llm": "ok",
        },
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to NimDoc AI API. Visit /docs for interactive Swagger API documentation.",
        "docs_url": "/docs",
    }
