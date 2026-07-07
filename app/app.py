from fastapi import FastAPI
from app.api.routes import router


app = FastAPI(
    title="Travel AI GraphRAG API",
    version="1.0.0"
)


app.include_router(router)


@app.get("/")
def health():

    return {
        "status": "ok",
        "message": "Travel AI Assistant API running"
    }