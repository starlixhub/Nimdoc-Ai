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

## Frontend Quickstart

### Prerequisites
- Node.js 18+
- npm / yarn / pnpm

### Run Frontend Development Server
```bash
# Install dependencies
npm install

# Run Vite dev server
npm run dev
```

The frontend app will be available at `http://localhost:5173`.

---

## Backend Quickstart

### Prerequisites
- Python 3.11+
- Git
- Docker & Docker Compose (optional, for containerized run)

### 1. Local Environment Setup

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
| `POST` | `/api/documents/upload` | Upload PDF file (multipart form) with magic-byte validation |
| `GET` | `/api/documents/{doc_id}/status` | Check extraction/indexing status of a document |
| `GET` | `/api/documents` | List all ingested documents |
| `DELETE` | `/api/documents/{doc_id}` | Delete document and remove its embeddings |
| `POST` | `/api/documents/{doc_id}/summarize` | Generate document summary and key points |

### Chat API (`/api/chat`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Send question, retrieve relevant chunks, and return grounded answer with citations |

### Sessions API (`/api/sessions`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/sessions` | Initialize new conversation session |
| `GET` | `/api/sessions` | List active sessions |
| `GET` | `/api/sessions/{session_id}/history` | Retrieve full multi-turn history |
| `DELETE` | `/api/sessions/{session_id}` | Clear conversation session |

---

## Error Handling & Status Codes

All errors follow a unified response shape:
```json
{
  "error": "ErrorType",
  "detail": "Human-readable explanation",
  "request_id": "req-uuid"
}
```

Specific HTTP status codes mapped:
- `400 Bad Request`: Invalid file type, corrupt PDF, or malformed request payload
- `404 Not Found`: Document or session not found
- `422 Unprocessable Entity`: Validation failure on input parameters
- `502 Bad Gateway`: Upstream LLM provider authentication or connectivity failure
- `504 Gateway Timeout`: LLM inference timeout guard triggered (`LLM_TIMEOUT_SECONDS`)
- `500 Internal Server Error`: Unhandled server exception
