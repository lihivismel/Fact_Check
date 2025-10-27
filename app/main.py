from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routes import router as api_router

app = FastAPI()


app.include_router(api_router, prefix="/api")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, "webui-react", "dist")
INDEX_HTML_PATH = os.path.join(FRONTEND_DIST_DIR, "index.html")
ASSETS_DIR = os.path.join(FRONTEND_DIST_DIR, "assets")


if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

@app.get("/")
async def serve_index():
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return {"error": "index.html not found"}

@app.get("/{rest_of_path:path}")
async def serve_react_app(rest_of_path: str):
    if rest_of_path.startswith("api/") or rest_of_path.startswith("assets/"):
        return {"detail": "Invalid path"}
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return {"error": "index.html not found"}
