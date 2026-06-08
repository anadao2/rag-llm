from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.ingest import router as ingest_router
from app.api.routes.query import router as query_router

app = FastAPI(title="RAG-LLM API (DDD)", version="0.2.0")
app.include_router(ingest_router)
app.include_router(query_router)
