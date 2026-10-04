# NimDoc AI — API Reference

> **Backend REST API contract for the frontend and integration team.**
> This document describes every API endpoint exposed by the FastAPI backend.
> The frontend developer should use this document as the authoritative contract and should not need to read backend source code for standard integration.

---

## Table of Contents

1. [Base URL and Format](#1-base-url-and-format)
2. [Common Response Conventions](#2-common-response-conventions)
3. [Error Handling](#3-error-handling)
4. [Data Models](#4-data-models)
5. [Document Endpoints](#5-document-endpoints)
   - [POST /api/documents/upload](#51-post-apidocumentsupload)
   - [GET /api/documents](#52-get-apidocuments)
   - [GET /api/documents/{document_id}](#53-get-apidocumentsdocument_id)
   - [DELETE /api/documents/{document_id}](#54-delete-apidocumentsdocument_id)
6. [Chat Endpoints](#6-chat-endpoints)
   - [POST /api/chat](#61-post-apichat)
   - [GET /api/chat/{session_id}](#62-get-apichatsession_id)
7. [Summary Endpoint](#7-summary-endpoint)
   - [POST /api/documents/{document_id}/summary](#71-post-apidocumentsdocument_idsummary)
8. [Health Check](#8-health-check)
9. [CORS Configuration](#9-cors-configuration)
10. [Interactive API Docs](#10-interactive-api-docs)

---

## 1. Base URL and Format

| Environment | Base URL |
|---|---|
| Local development | `http://localhost:8000` |
| Staging / production | *(to be configured at deployment)* |

**All request and response bodies use `application/json`**, except file uploads which use `multipart/form-data`.

All timestamps are in **ISO 8601 format** (`2026-10-04T09:52:00Z`).

---

## 2. Common Response Conventions

| Convention | Detail |
|---|---|
| Successful creation | HTTP `201 Created` |
| Successful read | HTTP `200 OK` |
| Successful deletion | HTTP `200 OK` with confirmation body |
| No content (deleted) | HTTP `204 No Content` (alternative, see endpoint) |
| Client error | HTTP `4xx` with error body |
| Server error | HTTP `5xx` with error body |
| Asynchronous processing | Endpoint returns immediately with `status: "processing"` |

---

## 3. Error Handling

All error responses — regardless of endpoint — share the following shape:

```json
{
  "error": "Human-readable description of the problem.",
  "code": "ERROR_CODE_CONSTANT"
}
```

### Standard Error Codes

| HTTP Status | Code | Meaning |
|---|---|---|
| `400` | `INVALID_REQUEST` | Malformed request body or missing required field |
| `400` | `UNSUPPORTED_FILE_TYPE` | Uploaded file is not a supported format |
| `404` | `DOCUMENT_NOT_FOUND` | The requested `document_id` does not exist |
| `404` | `SESSION_NOT_FOUND` | The requested `session_id` does not exist |
| `413` | `FILE_TOO_LARGE` | Uploaded file exceeds the configured size limit |
| `422` | `EXTRACTION_FAILED` | Text could not be extracted (e.g., image-only PDF) |
| `422` | `PROCESSING_FAILED` | General ingestion pipeline failure |
| `429` | `RATE_LIMITED` | LLM or embedding service rate limit hit |
| `502` | `LLM_UNAVAILABLE` | Nebius Token Factory or NVIDIA model is unreachable |
| `504` | `LLM_TIMEOUT` | LLM inference took too long |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

---

## 4. Data Models

### DocumentStatus

The processing state of an uploaded document.

| Value | Meaning |
|---|---|
| `"processing"` | Document has been received; ingestion pipeline is running |
| `"ready"` | Document is fully processed and queryable |
| `"failed"` | Ingestion failed; document cannot be queried |

---

### DocumentMetadata

Returned by document listing and detail endpoints.

```json
{
  "document_id": "doc_abc123",
  "document_name": "project_guidelines.pdf",
  "file_type": "pdf",
  "file_size_bytes": 204800,
  "page_count": 12,
  "status": "ready",
  "uploaded_at": "2026-10-04T09:00:00Z"
}
```

---

### Citation

A single citation referencing the document, page, and source text used to ground an answer.

```json
{
  "document_id": "doc_abc123",
  "document_name": "project_guidelines.pdf",
  "page": 4,
  "text": "All projects must be submitted by October 15."
}
```

| Field | Type | Description |
|---|---|---|
| `document_id` | `string` | Unique document identifier |
| `document_name` | `string` | Original filename of the document |
| `page` | `integer \| null` | Page number in the source document. `null` if unavailable |
| `text` | `string` | The exact source text from the document chunk |

---

### ChatTurn

A single question-answer exchange within a session.

```json
{
  "turn_index": 1,
  "question": "What is the submission deadline?",
  "answer": "The project submission deadline is October 15.",
  "citations": [...],
  "grounded": true,
  "created_at": "2026-10-04T09:05:00Z"
}
```

---

## 5. Document Endpoints

### 5.1 `POST /api/documents/upload`

Upload a document and trigger the ingestion pipeline (text extraction, chunking, embedding, vector storage).

**Method:** `POST`
**URL:** `/api/documents/upload`
**Content-Type:** `multipart/form-data`

#### Request Parameters

| Parameter | In | Type | Required | Description |
|---|---|---|---|---|
| `file` | form-data | `file` | ✅ Yes | The document file to upload |

**Supported file types:** `pdf` *(MVP)* — additional types planned.
**Maximum file size:** Configurable via `MAX_UPLOAD_SIZE_MB` (default: 50 MB).

#### Request Example

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@project_guidelines.pdf"
```

#### Response — `201 Created`

```json
{
  "document_id": "doc_abc123",
  "document_name": "project_guidelines.pdf",
  "status": "processing",
  "message": "Document uploaded successfully. Processing has started.",
  "uploaded_at": "2026-10-04T09:00:00Z"
}
```

> **Note:** The response is returned immediately. The `status` will be `"processing"` while the ingestion pipeline runs in the background. Poll `GET /api/documents/{document_id}` to check when `status` changes to `"ready"`.

#### Error Responses

| Status | Code | Scenario |
|---|---|---|
| `400` | `UNSUPPORTED_FILE_TYPE` | File extension is not `pdf` |
| `413` | `FILE_TOO_LARGE` | File exceeds `MAX_UPLOAD_SIZE_MB` |
| `422` | `EXTRACTION_FAILED` | File is a PDF but text could not be extracted |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

#### Error Example

```json
{
  "error": "File type '.docx' is not supported. Supported types: pdf",
  "code": "UNSUPPORTED_FILE_TYPE"
}
```

---

### 5.2 `GET /api/documents`

List all uploaded documents with their metadata and processing status.

**Method:** `GET`
**URL:** `/api/documents`

#### Request Parameters

None.

#### Request Example

```bash
curl http://localhost:8000/api/documents
```

#### Response — `200 OK`

```json
{
  "documents": [
    {
      "document_id": "doc_abc123",
      "document_name": "project_guidelines.pdf",
      "file_type": "pdf",
      "file_size_bytes": 204800,
      "page_count": 12,
      "status": "ready",
      "uploaded_at": "2026-10-04T09:00:00Z"
    },
    {
      "document_id": "doc_def456",
      "document_name": "team_policy.pdf",
      "file_type": "pdf",
      "file_size_bytes": 98304,
      "page_count": 6,
      "status": "processing",
      "uploaded_at": "2026-10-04T09:10:00Z"
    }
  ],
  "total": 2
}
```

#### Error Responses

| Status | Code | Scenario |
|---|---|---|
| `500` | `INTERNAL_ERROR` | Failed to retrieve document list |

---

### 5.3 `GET /api/documents/{document_id}`

Get metadata and status for a single document.

**Method:** `GET`
**URL:** `/api/documents/{document_id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `document_id` | `string` | ✅ Yes | The unique document identifier |

#### Request Example

```bash
curl http://localhost:8000/api/documents/doc_abc123
```

#### Response — `200 OK`

```json
{
  "document_id": "doc_abc123",
  "document_name": "project_guidelines.pdf",
  "file_type": "pdf",
  "file_size_bytes": 204800,
  "page_count": 12,
  "status": "ready",
  "chunk_count": 47,
  "uploaded_at": "2026-10-04T09:00:00Z"
}
```

| Additional Field | Type | Description |
|---|---|---|
| `chunk_count` | `integer` | Total number of chunks stored in the vector database for this document |

#### Error Responses

| Status | Code | Scenario |
|---|---|---|
| `404` | `DOCUMENT_NOT_FOUND` | No document with this `document_id` exists |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

---

### 5.4 `DELETE /api/documents/{document_id}`

Delete a document and remove all its associated data (file, chunks, vectors).

**Method:** `DELETE`
**URL:** `/api/documents/{document_id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `document_id` | `string` | ✅ Yes | The unique document identifier |

#### Request Example

```bash
curl -X DELETE http://localhost:8000/api/documents/doc_abc123
```

#### Response — `200 OK`

```json
{
  "document_id": "doc_abc123",
  "document_name": "project_guidelines.pdf",
  "message": "Document deleted successfully. All associated data has been removed.",
  "deleted_at": "2026-10-04T10:00:00Z"
}
```

> **Note:** Deletion removes the stored file from disk and all vector chunks from the vector database. This operation is irreversible.

#### Error Responses

| Status | Code | Scenario |
|---|---|---|
| `404` | `DOCUMENT_NOT_FOUND` | No document with this `document_id` exists |
| `500` | `INTERNAL_ERROR` | Failed to complete deletion |

---

## 6. Chat Endpoints

### 6.1 `POST /api/chat`

Ask a natural-language question. The backend retrieves relevant document chunks, constructs a grounded prompt, calls the NVIDIA LLM via Nebius Token Factory, and returns a factual answer with citations.

**Method:** `POST`
**URL:** `/api/chat`
**Content-Type:** `application/json`

#### Request Body

```json
{
  "question": "What is the submission deadline?",
  "document_ids": ["doc_abc123"],
  "session_id": "session_001"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | `string` | ✅ Yes | The natural-language question from the user |
| `document_ids` | `string[]` | ✅ Yes | List of document IDs to search. Must be non-empty. Pass all document IDs to search across all uploaded documents. |
| `session_id` | `string` | ✅ Yes | Session identifier. Use a consistent value across turns to enable follow-up question context. Generate a UUID on the frontend for new sessions. |

#### Request Example

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the submission deadline?",
    "document_ids": ["doc_abc123"],
    "session_id": "session_001"
  }'
```

#### Response — `200 OK` (Answer found)

```json
{
  "session_id": "session_001",
  "answer": "The project submission deadline is October 15.",
  "citations": [
    {
      "document_id": "doc_abc123",
      "document_name": "project_guidelines.pdf",
      "page": 4,
      "text": "All projects must be submitted by October 15."
    }
  ],
  "grounded": true,
  "created_at": "2026-10-04T09:05:00Z"
}
```

#### Response — `200 OK` (Answer not found)

When insufficient evidence is found in the documents, the system returns a "not found" response without calling the LLM.

```json
{
  "session_id": "session_001",
  "answer": "I couldn't find this information in the uploaded documents.",
  "citations": [],
  "grounded": false,
  "created_at": "2026-10-04T09:06:00Z"
}
```

#### Response Fields

| Field | Type | Description |
|---|---|---|
| `session_id` | `string` | Echo of the session ID |
| `answer` | `string` | The generated answer text |
| `citations` | `Citation[]` | List of source citations. Empty if `grounded=false` |
| `grounded` | `boolean` | `true` if the answer is based on retrieved document evidence. `false` if evidence was insufficient |
| `created_at` | `string` | ISO 8601 timestamp of the response |

#### Multi-Document Question Example

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare the submission deadlines in both documents.",
    "document_ids": ["doc_abc123", "doc_def456"],
    "session_id": "session_002"
  }'
```

```json
{
  "session_id": "session_002",
  "answer": "According to the project guidelines, the submission deadline is October 15. The team policy document does not mention a submission deadline.",
  "citations": [
    {
      "document_id": "doc_abc123",
      "document_name": "project_guidelines.pdf",
      "page": 4,
      "text": "All projects must be submitted by October 15."
    }
  ],
  "grounded": true,
  "created_at": "2026-10-04T09:07:00Z"
}
```

#### Follow-Up Question Example

Using the same `session_id` allows the backend to include prior context.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the penalty for late submissions?",
    "document_ids": ["doc_abc123"],
    "session_id": "session_001"
  }'
```

#### Error Responses

| Status | Code | Scenario |
|---|---|---|
| `400` | `INVALID_REQUEST` | `question` is empty or `document_ids` is empty |
| `404` | `DOCUMENT_NOT_FOUND` | One or more `document_ids` do not exist |
| `422` | `DOCUMENT_NOT_READY` | One or more documents are still processing |
| `429` | `RATE_LIMITED` | LLM service rate limit reached |
| `502` | `LLM_UNAVAILABLE` | Nebius Token Factory or NVIDIA model is unreachable |
| `504` | `LLM_TIMEOUT` | LLM inference exceeded timeout |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

#### Error Example

```json
{
  "error": "Document 'doc_xyz999' was not found.",
  "code": "DOCUMENT_NOT_FOUND"
}
```

---

### 6.2 `GET /api/chat/{session_id}`

Retrieve the full conversation history for a session.

**Method:** `GET`
**URL:** `/api/chat/{session_id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `session_id` | `string` | ✅ Yes | The session identifier |

#### Request Example

```bash
curl http://localhost:8000/api/chat/session_001
```

#### Response — `200 OK`

```json
{
  "session_id": "session_001",
  "turns": [
    {
      "turn_index": 1,
      "question": "What is the submission deadline?",
      "answer": "The project submission deadline is October 15.",
      "citations": [
        {
          "document_id": "doc_abc123",
          "document_name": "project_guidelines.pdf",
          "page": 4,
          "text": "All projects must be submitted by October 15."
        }
      ],
      "grounded": true,
      "created_at": "2026-10-04T09:05:00Z"
    },
    {
      "turn_index": 2,
      "question": "What is the penalty for late submissions?",
      "answer": "I couldn't find this information in the uploaded documents.",
      "citations": [],
      "grounded": false,
      "created_at": "2026-10-04T09:08:00Z"
    }
  ],
  "turn_count": 2
}
```

#### Error Responses

| Status | Code | Scenario |
|---|---|---|
| `404` | `SESSION_NOT_FOUND` | No session with this `session_id` exists |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

---

## 7. Summary Endpoint

### 7.1 `POST /api/documents/{document_id}/summary`

Request an AI-generated summary of a document's content. The summary is grounded in the document's text.

> **MVP Status:** This endpoint is in scope for the MVP but is a secondary priority. It will be implemented if time permits after core chat functionality is complete.

**Method:** `POST`
**URL:** `/api/documents/{document_id}/summary`
**Content-Type:** `application/json`

#### Path Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `document_id` | `string` | ✅ Yes | The document to summarize |

#### Request Body

```json
{
  "focus": "key deadlines and requirements"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `focus` | `string` | ❌ No | Optional focus instruction. If omitted, a general summary is generated. |

#### Request Example

```bash
curl -X POST http://localhost:8000/api/documents/doc_abc123/summary \
  -H "Content-Type: application/json" \
  -d '{"focus": "key deadlines and requirements"}'
```

#### Response — `200 OK`

```json
{
  "document_id": "doc_abc123",
  "document_name": "project_guidelines.pdf",
  "summary": "The project guidelines define submission requirements and deadlines. Key points: all projects must be submitted by October 15; late submissions are subject to a 10% penalty per day; projects must include a demo video.",
  "citations": [
    {
      "document_id": "doc_abc123",
      "document_name": "project_guidelines.pdf",
      "page": 4,
      "text": "All projects must be submitted by October 15."
    },
    {
      "document_id": "doc_abc123",
      "document_name": "project_guidelines.pdf",
      "page": 4,
      "text": "Late submissions are subject to a 10% penalty per day."
    }
  ],
  "grounded": true,
  "created_at": "2026-10-04T09:15:00Z"
}
```

#### Error Responses

| Status | Code | Scenario |
|---|---|---|
| `404` | `DOCUMENT_NOT_FOUND` | No document with this `document_id` exists |
| `422` | `DOCUMENT_NOT_READY` | Document is still processing |
| `502` | `LLM_UNAVAILABLE` | Nebius or NVIDIA model is unreachable |
| `504` | `LLM_TIMEOUT` | LLM inference exceeded timeout |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

---

## 8. Health Check

### `GET /health`

Returns the health status of the backend service. Useful for deployment monitoring and local verification.

**Method:** `GET`
**URL:** `/health`

#### Response — `200 OK`

```json
{
  "status": "ok",
  "version": "0.1.0",
  "services": {
    "vector_db": "ok",
    "llm": "ok"
  }
}
```

If a dependent service is unreachable, its status will be `"error"` but the overall API remains operational.

```json
{
  "status": "degraded",
  "version": "0.1.0",
  "services": {
    "vector_db": "ok",
    "llm": "error"
  }
}
```

---

## 9. CORS Configuration

The FastAPI backend is configured to accept requests from the React frontend during local development.

**Allowed origins (development):**
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (alternative React dev server)

Production origins will be configured via environment variable at deployment time.

The Team Lead is responsible for configuring CORS in `app/main.py` and ensuring it is not set to `*` in production.

---

## 10. Interactive API Docs

FastAPI automatically generates interactive API documentation at the following URLs:

| URL | Type |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — interactive, supports request testing |
| `http://localhost:8000/redoc` | ReDoc — clean, read-only reference format |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3.x schema |

During development, the Swagger UI at `/docs` is the fastest way to test endpoints without writing `curl` commands.

---

## Appendix: Full API Summary

| Method | Endpoint | Description | Owner |
|---|---|---|---|
| `POST` | `/api/documents/upload` | Upload a document and start ingestion | Team Lead |
| `GET` | `/api/documents` | List all uploaded documents | Team Lead |
| `GET` | `/api/documents/{document_id}` | Get document metadata and status | Team Lead |
| `DELETE` | `/api/documents/{document_id}` | Delete document and all its data | Team Lead |
| `POST` | `/api/chat` | Ask a question, receive grounded answer + citations | Team Lead + RAG Developer |
| `GET` | `/api/chat/{session_id}` | Get full conversation history for a session | Team Lead |
| `POST` | `/api/documents/{document_id}/summary` | Generate a document summary | Team Lead + RAG Developer |
| `GET` | `/health` | Backend health check | Team Lead |

---

*NimDoc AI — API Reference — Nebius × NVIDIA Global AI Hackathon*
