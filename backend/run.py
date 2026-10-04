"""Development startup script for NimDoc AI backend.
Usage:
    python run.py
"""
import sys
import os

# Add backend directory to sys.path to ensure module imports resolve smoothly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
