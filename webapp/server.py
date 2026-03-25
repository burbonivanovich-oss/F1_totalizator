"""
FastAPI web server for F1 Totalizator Mini App.

Serves:
  GET  /              → index.html
  GET  /static/*      → static files
  GET  /api/drivers   → list of drivers (JSON)
  GET  /api/races     → open races (JSON)
  GET  /api/prediction → current user prediction
  GET  /api/race/{id} → race details
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from webapp.api.routes import router as api_router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="F1 Totalizator WebApp", docs_url=None, redoc_url=None)

# API routes
app.include_router(api_router)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))
