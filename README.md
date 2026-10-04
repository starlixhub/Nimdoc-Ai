# NimDoc AI

**NimDoc AI** is an AI-powered document intelligence assistant that enables users to upload PDF documents, ask natural language questions, and receive grounded, citation-backed answers, document summaries, and key insights. Built for the Nebius × NVIDIA Hackathon.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Frontend Client (React)   |
                      +--------------+--------------+
                                     | HTTP / REST
                                     v
+------------------------------------+------------------------------------+
|                         FastAPI Backend                                 |
|                                                                         |
|  [Middleware: RequestLogging (Latency/ReqID) + GlobalExceptionHandler]  |
|                                                                         |
|  +-------------------+  +--------------------+  +--------------------+  |
|  | /api/documents    |  | /api/chat          |  | /api/sessions      |  |
|  | - Upload (PDF/MIME|  | - Multi-turn Q&A   |  | - Create session   |  |
|  | - Status polling  |  | - Timeout guard    |  | - List sessions    |  |
|  | - List & Delete   |  | - Error classifier |  | - Get turn history |  |
|  | - Summarize       |  | - Citation return  |  | - Delete session   |  |
|  +---------+---------+  +---------+----------+  +---------+----------+  |
|            |                      |                       |             |
|            v                      v                       v             |
|   Ingestion Service          RAG Service           Session Service      |
|   (PyMuPDF extract +        (Nebius LLM +         (In-Memory Store)     |
|    Recursive chunking)       Qdrant Vector DB)                          |
+------------------------------------+------------------------------------+
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 v                                       v
      +----------------------+               +-----------------------+
      |  Nebius / NVIDIA LLM |               |   Qdrant Vector DB    |
      |  (Llama-3.1-8B)      |               |   (Port 6333 / 6334)  |
      +----------------------+               +-----------------------+
```

---

## Backend Quickstart

### Prerequisites
- Python 3.11+
- Git
- Docker & Docker Compose (optional, for containerized run)

### 1. Local Environment Setup

Clone repository and checkout the `Backend` branch:
```bash
git clone https://github.com/starlixhub/Nimdoc-Ai.git
cd Nimdoc-Ai
git checkout Backend
```

Create a virtual environment and install dependencies:
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration

Copy or create `backend/.env`:
```ini
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Nebius / NVIDIA LLM Configuration
NEBIUS_API_KEY=your_nebius_api_key_here
NEBIUS_API_BASE_URL=https://api.tokenfactory.nebius.ai/v1
LLM_MODEL_NAME=nvidia/meta-llama-3.1-8b-instruct
LLM_TIMEOUT_SECONDS=30

# Vector DB
VECTOR_DB_URL=http://localhost:6333
VECTOR_DB_COLLECTION=nimdoc_documents
```

> **Note:** When `NEBIUS_API_KEY` starts with `mock_` or is omitted, the backend runs in mock mode for local testing without external API credentials.

### 3. Run Development Server

```bash
# From the backend directory:
python run.py

# Or directly with uvicorn:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server starts at `http://localhost:8000`.
- Interactive Swagger API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative ReDoc documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Running Automated Tests

Run the automated test suite from the repository root:
```bash
python -m pytest -p no:cacheprovider tests/backend/ -v
```

---

## Docker & Containerization

Run the complete backend stack (FastAPI backend + Qdrant vector database) with Docker Compose:

```bash
# Build and start services
docker compose up --build

# Run in background
docker compose up -d

# Stop services
docker compose down
```

Services exposed:
- Backend API: `http://localhost:8000`
- Qdrant Web UI / REST: `http://localhost:6333/dashboard`

---

## API Specification

### Health & Diagnostics
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health status of system, LLM service, and Vector DB |
| `GET` | `/` | Root endpoint with welcome message and docs link |

### Documents API (`/api/documents`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload PDF file (validates MIME `%PDF-` signature & file size limit) |
| `GET` | `/api/documents` | List all uploaded documents with metadata |
| `GET` | `/api/documents/{id}` | Get single document metadata |
| `GET` | `/api/documents/{id}/status` | Poll document processing status (`processing`, `ready`, `failed`) |
| `GET` | `/api/documents/{id}/file` | Stream raw PDF for in-browser preview or download |
| `DELETE` | `/api/documents/{id}` | Delete document and associated chunks |
| `POST` | `/api/documents/{id}/summary` | Generate grounded summary of a document |

### Sessions API (`/api/sessions`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/sessions` | Create a new chat session with optional title |
| `GET` | `/api/sessions` | List all active chat sessions with turn counts & timestamps |
| `GET` | `/api/sessions/{session_id}` | Retrieve full conversation turn history for a session |
| `DELETE` | `/api/sessions/{session_id}` | Delete a conversation session |

### Chat API (`/api/chat`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Send question + document IDs; returns grounded answer + citations (JSON) |
| `POST` | `/api/chat/stream` | Real-time Server-Sent Events (SSE) streaming (`metadata`, `token`, `done`, `error`) |
| `GET` | `/api/chat/{session_id}` | Get turn history for a session (alias for backward compatibility) |

---

## Error Handling & Diagnostic Headers

All responses include diagnostic headers:
- `X-Request-ID`: Unique tracking UUID for distributed request tracing
- `X-Process-Time-Ms`: Round-trip request processing latency in milliseconds

Error responses adhere to standard JSON error format:
```json
{
  "error": "Error description",
  "detail": "Detailed context or validation failure",
  "code": "ERROR_CODE",
  "status_code": 400
}
```
Specific HTTP status codes mapped:
- `400 Bad Request`: Validation failure (empty question, missing document IDs, invalid magic bytes)
- `404 Not Found`: Document or session not found
- `413 Payload Too Large`: Upload exceeds maximum file size limit (`MAX_UPLOAD_SIZE_MB`)
- `429 Too Many Requests`: Upstream LLM rate limit exceeded
- `502 Bad Gateway`: Upstream LLM provider authentication or connectivity failure
- `504 Gateway Timeout`: LLM inference timeout guard triggered (`LLM_TIMEOUT_SECONDS`)
- `500 Internal Server Error`: Unhandled server exception
