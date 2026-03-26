"""
ingest.py – Text chunking and vector-database ingestion.

This module reads scraped pages (produced by scraper.py), splits
them into overlapping chunks with LangChain's
``RecursiveCharacterTextSplitter``, embeds each chunk via OpenAI's
embedding API and persists everything into a local ChromaDB collection.

Usage
-----
    # Build the knowledge base from a website (CLI)
    python ingest.py --url https://example.com --max-pages 50

    # Or call programmatically
    from ingest import ingest_pages
    from scraper import scrape_website

    pages = scrape_website("https://example.com")
    ingest_pages(pages)
"""

import argparse
import logging
import os

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

from scraper import scrape_website

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── Configuration (overridable via environment variables) ─────────────────────
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "website_knowledge")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CHUNK_SIZE = 500          # characters per chunk
CHUNK_OVERLAP = 50        # overlap between consecutive chunks


def _get_collection() -> chromadb.Collection:
    """Return (or create) the ChromaDB collection with the OpenAI embedder."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL,
    )
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_fn,
    )


def ingest_pages(pages: list[dict]) -> int:
    """
    Chunk *pages* and upsert them into ChromaDB.

    Parameters
    ----------
    pages:
        List of ``{"url": str, "text": str}`` dicts (output of
        :func:`scraper.scrape_website`).

    Returns
    -------
    int
        Total number of chunks upserted.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    collection = _get_collection()

    all_ids: list[str] = []
    all_texts: list[str] = []
    all_meta: list[dict] = []

    for page in pages:
        url = page["url"]
        text = page["text"]
        chunks = splitter.split_text(text)

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{url}#chunk{idx}"
            all_ids.append(chunk_id)
            all_texts.append(chunk)
            all_meta.append({"url": url, "chunk_index": idx})

    if not all_ids:
        logger.warning("No chunks to ingest – pages list may be empty.")
        return 0

    # ChromaDB's upsert handles both insert and update in one call.
    collection.upsert(ids=all_ids, documents=all_texts, metadatas=all_meta)
    logger.info("Upserted %d chunks into collection '%s'.", len(all_ids), CHROMA_COLLECTION_NAME)
    return len(all_ids)


# ── CLI entry-point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape a website and ingest its content into ChromaDB."
    )
    parser.add_argument("--url", required=True, help="Root URL to crawl.")
    parser.add_argument(
        "--max-pages", type=int, default=50,
        help="Maximum number of pages to scrape (default: 50)."
    )
    args = parser.parse_args()

    pages = scrape_website(args.url, max_pages=args.max_pages)
    total = ingest_pages(pages)
    print(f"Done. {total} chunks stored in ChromaDB.")
