from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

# The built frontend lives in /app/static (copied there by the Dockerfile)
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


def init_frontend(app: FastAPI) -> None:
    """
    Serve the Vue SPA from the static directory.

    In production the Dockerfile copies the built frontend into /app/static.
    In development this directory doesn't exist, so we skip silently.
    """
    if not STATIC_DIR.is_dir():
        return

    # Let FastAPI efficiently serve JS/CSS bundles under /assets
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """
        Catch-all route that makes the SPA work:

        1. If the path points to a real file (e.g. favicon.ico) -> serve it
        2. Otherwise -> serve index.html so Vue Router handles the route
        """
        # Resolve the path and guard against directory traversal (e.g. ../../etc/passwd)
        requested_file = (STATIC_DIR / full_path).resolve()
        if not requested_file.is_relative_to(STATIC_DIR):
            return FileResponse(INDEX_HTML)

        # Serve the file directly if it exists (favicon.ico, robots.txt, etc.)
        if requested_file.is_file():
            return FileResponse(requested_file)

        # For everything else, serve index.html and let Vue Router handle it
        if INDEX_HTML.is_file():
            return FileResponse(INDEX_HTML)

        return PlainTextResponse(
            "Frontend not built or index.html missing",
            status_code=status.HTTP_404_NOT_FOUND,
        )
