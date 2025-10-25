from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routes import router as api_router

app = FastAPI()

# 1️⃣ API routes
app.include_router(api_router, prefix="/api")

# 2️⃣ Frontend build directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, "webui-react", "dist")
INDEX_HTML_PATH = os.path.join(FRONTEND_DIST_DIR, "index.html")
ASSETS_DIR = os.path.join(FRONTEND_DIST_DIR, "assets")

print(f"FRONTEND_DIST_DIR: {FRONTEND_DIST_DIR}")
print(f"INDEX_HTML_PATH exists: {os.path.exists(INDEX_HTML_PATH)}")
print(f"ASSETS_DIR exists: {os.path.exists(ASSETS_DIR)}")

# 3️⃣ Serve static assets (JS, CSS, etc.)
if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# 4️⃣ Serve main React page
@app.get("/")
async def serve_index():
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return {"error": "index.html not found"}

# 5️⃣ Catch-all route (for client-side routing)
@app.get("/{rest_of_path:path}")
async def serve_react_app(rest_of_path: str):
    if rest_of_path.startswith("api/") or rest_of_path.startswith("assets/"):
        return {"detail": "Invalid path"}
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return {"error": "index.html not found"}
