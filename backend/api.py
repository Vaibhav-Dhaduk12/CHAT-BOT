"""
api.py – FastAPI server exposing the RAG chatbot as a REST API.

Endpoints
---------
POST /ingest
    Scrape a given URL and ingest its content into ChromaDB.

POST /chat
    Accept a user message and return an AI-generated answer grounded
    in the ingested website content.

GET  /health
    Simple health-check.

Running
-------
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from ingest import ingest_pages
from rag_chain import answer_question
from scraper import scrape_website

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS: list[str] = (
    ["*"] if _raw_origins.strip() == "*"
    else [o.strip() for o in _raw_origins.split(",") if o.strip()]
)


# ── Pydantic models ───────────────────────────────────────────────────────────
class IngestRequest(BaseModel):
    url: HttpUrl
    max_pages: int = 50


class IngestResponse(BaseModel):
    message: str
    pages_scraped: int
    chunks_stored: int


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


# ── App lifecycle ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG Chatbot API is starting up.")
    yield
    logger.info("RAG Chatbot API is shutting down.")


app = FastAPI(
    title="RAG Chatbot API",
    description=(
        "A Retrieval-Augmented Generation chatbot that learns from any website "
        "and answers questions grounded in its content."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Utility"])
def health_check():
    """Quick liveness probe."""
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse, tags=["Knowledge Base"])
def ingest_website(req: IngestRequest):
    """
    Crawl *url* (up to *max_pages* pages) and store the extracted text
    as vector embeddings in ChromaDB.
    """
    url_str = str(req.url)
    logger.info("Ingestion requested for %s (max_pages=%d)", url_str, req.max_pages)

    try:
        pages = scrape_website(url_str, max_pages=req.max_pages)
    except Exception as exc:
        logger.exception("Scraping failed for %s", url_str)
        raise HTTPException(status_code=502, detail=f"Scraping failed: {exc}") from exc

    if not pages:
        raise HTTPException(
            status_code=404,
            detail="No pages could be scraped from the provided URL.",
        )

    try:
        chunks = ingest_pages(pages)
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return IngestResponse(
        message="Ingestion complete.",
        pages_scraped=len(pages),
        chunks_stored=chunks,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(req: ChatRequest):
    """
    Answer a user *message* using the RAG pipeline.

    Optionally pass prior conversation *history* to maintain context.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    history = [{"role": m.role, "content": m.content} for m in req.history]

    try:
        reply = answer_question(req.message, chat_history=history or None)
    except Exception as exc:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc

    return ChatResponse(reply=reply)
