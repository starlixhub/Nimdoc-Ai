import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "services" in data
    assert "llm" in data["services"]
    assert "vector_db" in data["services"]


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs_url" in data


@pytest.mark.asyncio
async def test_list_documents_initially_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


@pytest.mark.asyncio
async def test_upload_non_pdf_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", b"plain text", "text/plain")},
        )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_chat_empty_question_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"question": "", "document_ids": ["doc_123"], "session_id": "test_session"},
        )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_chat_empty_document_ids_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"question": "What is the project deadline?", "document_ids": [], "session_id": "test_session"},
        )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_chat_and_session_flow():
    session_id = "smoke_test_session_1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Chat query
        response = await client.post(
            "/api/chat",
            json={
                "question": "What is the submission deadline?",
                "document_ids": ["doc_sample_1"],
                "session_id": session_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "answer" in data
        assert "citations" in data
        assert "grounded" in data

        # Check session history retrieval
        hist_response = await client.get(f"/api/chat/{session_id}")
        assert hist_response.status_code == 200
        hist_data = hist_response.json()
        assert hist_data["session_id"] == session_id
        assert hist_data["turn_count"] >= 1
        assert len(hist_data["turns"]) >= 1
