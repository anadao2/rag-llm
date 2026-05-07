from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.ingest import router as ingest_router

app = FastAPI(title="RAG-LLM API", version="0.1.0")
app.include_router(ingest_router)
