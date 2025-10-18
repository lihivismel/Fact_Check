from fastapi import FastAPI
from app import routes

app = FastAPI(title="FactCheck API", version="1.0")

app.include_router(routes.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Server is running!"}
