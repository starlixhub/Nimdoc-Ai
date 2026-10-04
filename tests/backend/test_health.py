import pytest


@pytest.mark.asyncio
async def test_health(client):
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
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs_url" in data


@pytest.mark.asyncio
async def test_response_diagnostic_headers(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-process-time-ms" in response.headers
    duration = float(response.headers["x-process-time-ms"])
    assert duration >= 0.0


@pytest.mark.asyncio
async def test_list_documents_initially(client):
    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


@pytest.mark.asyncio
async def test_upload_non_pdf_rejected(client):
    response = await client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_upload_fake_pdf_magic_bytes_rejected(client):
    response = await client.post(
        "/api/documents/upload",
        files={"file": ("fake.pdf", b"this is not really a pdf file", "application/pdf")},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "magic bytes" in str(data["detail"]).lower()


@pytest.mark.asyncio
async def test_upload_valid_pdf_and_check_status(client):
    # Valid PDF magic bytes: %PDF-1.4
    pdf_content = b"%PDF-1.4 mock pdf document content for testing"
    upload_res = await client.post(
        "/api/documents/upload",
        files={"file": ("sample.pdf", pdf_content, "application/pdf")},
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    assert "document_id" in upload_data
    doc_id = upload_data["document_id"]

    # Poll status endpoint
    status_res = await client.get(f"/api/documents/{doc_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["document_id"] == doc_id
    assert status_data["status"] in ("processing", "ready")
    assert status_data["document_name"] == "sample.pdf"

    # Get single document
    doc_res = await client.get(f"/api/documents/{doc_id}")
    assert doc_res.status_code == 200
    assert doc_res.json()["document_id"] == doc_id


@pytest.mark.asyncio
async def test_document_not_found_404(client):
    response = await client.get("/api/documents/non_existent_doc_id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_delete_document_404(client):
    response = await client.delete("/api/documents/non_existent_doc_id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post(
        "/api/sessions",
        json={"title": "Sprint Planning Q&A"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["title"] == "Sprint Planning Q&A"


@pytest.mark.asyncio
async def test_list_sessions(client):
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
    assert "total" in data


@pytest.mark.asyncio
async def test_get_session_not_found_404(client):
    response = await client.get("/api/sessions/non_existent_session_id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_flow(client):
    # 1. Create a session
    create_res = await client.post("/api/sessions", json={"title": "To be deleted"})
    assert create_res.status_code == 201
    sid = create_res.json()["session_id"]

    # 2. Delete it
    del_res = await client.delete(f"/api/sessions/{sid}")
    assert del_res.status_code == 200
    assert del_res.json()["session_id"] == sid

    # 3. Verify it is gone
    get_res = await client.get(f"/api/sessions/{sid}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_chat_empty_question_rejected(client):
    response = await client.post(
        "/api/chat",
        json={"question": "", "document_ids": ["doc_123"], "session_id": "test_session"},
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_chat_empty_document_ids_rejected(client):
    response = await client.post(
        "/api/chat",
        json={"question": "What is the project deadline?", "document_ids": [], "session_id": "test_session"},
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_chat_and_session_flow(client):
    session_id = "smoke_test_session_1"
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

    # Check session history retrieval via chat router
    hist_response = await client.get(f"/api/chat/{session_id}")
    assert hist_response.status_code == 200
    hist_data = hist_response.json()
    assert hist_data["session_id"] == session_id
    assert hist_data["turn_count"] >= 1
    assert len(hist_data["turns"]) >= 1

    # Check session history retrieval via sessions router
    sess_response = await client.get(f"/api/sessions/{session_id}")
    assert sess_response.status_code == 200
    sess_data = sess_response.json()
    assert sess_data["session_id"] == session_id
    assert len(sess_data["turns"]) >= 1


@pytest.mark.asyncio
async def test_get_document_file_endpoint(client):
    pdf_content = b"%PDF-1.4 file content for preview test"
    upload_res = await client.post(
        "/api/documents/upload",
        files={"file": ("preview_test.pdf", pdf_content, "application/pdf")},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    file_res = await client.get(f"/api/documents/{doc_id}/file")
    assert file_res.status_code == 200
    assert file_res.headers["content-type"] == "application/pdf"
    assert "preview_test.pdf" in file_res.headers.get("content-disposition", "")
    assert file_res.content == pdf_content

    # 404 for invalid ID
    missing_file_res = await client.get("/api/documents/non_existent_doc_id/file")
    assert missing_file_res.status_code == 404


@pytest.mark.asyncio
async def test_chat_stream_flow(client):
    session_id = "test_stream_session_1"
    response = await client.post(
        "/api/chat/stream",
        json={
            "question": "What are the rules?",
            "document_ids": ["doc_sample_1"],
            "session_id": session_id,
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    text = response.text
    assert "event: metadata" in text
    assert "event: token" in text
    assert "event: done" in text

    # Verify session history was saved
    sess_res = await client.get(f"/api/sessions/{session_id}")
    assert sess_res.status_code == 200
    turns = sess_res.json()["turns"]
    assert len(turns) >= 1


@pytest.mark.asyncio
async def test_sqlite_session_persistence(tmp_path):
    from app.models.chat import ChatTurn
    from app.services.session import SessionService

    test_db = str(tmp_path / "test_sessions.db")
    service1 = SessionService(db_path=test_db)
    sid = service1.create_session(title="Persistent Session")
    service1.add_turn(
        sid,
        ChatTurn(
            turn_index=1,
            question="Persisted question?",
            answer="Persisted answer.",
            citations=[],
            grounded=True,
        ),
    )

    # Instantiate new service instance simulating server restart
    service2 = SessionService(db_path=test_db)
    loaded = service2.get_session(sid)
    assert loaded is not None
    assert loaded.session_id == sid
    assert loaded.turn_count == 1
    assert loaded.turns[0].question == "Persisted question?"
    assert loaded.turns[0].answer == "Persisted answer."
