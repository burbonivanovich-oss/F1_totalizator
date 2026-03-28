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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from webapp.api.routes import router as api_router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="F1 Totalizator WebApp", docs_url=None, redoc_url=None)


# Middleware to set proper cache headers
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Don't cache HTML (always fetch fresh)
        if request.url.path == "/" or request.url.path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Cache CSS/JS for 1 hour, but with must-revalidate
        # (so if server has new version, browser will check)
        elif request.url.path.endswith((".css", ".js")):
            response.headers["Cache-Control"] = "public, max-age=3600, must-revalidate"

        # Cache other static files (images, fonts) for 7 days
        elif request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=604800"

        return response


app.add_middleware(CacheControlMiddleware)

# API routes
app.include_router(api_router)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))
