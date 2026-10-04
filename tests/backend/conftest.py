import os
import sys
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    """Async test client for FastAPI application."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
