"""
rag_chain.py – Retrieval-Augmented Generation query engine.

Given a user question this module:
  1. Embeds the question using the same OpenAI embedding model that
     was used during ingestion.
  2. Queries ChromaDB for the *top-k* most semantically similar
     text chunks.
  3. Builds a strict, brand-safe prompt and calls the OpenAI Chat API
     to generate a concise, grounded answer.

Usage
-----
    from rag_chain import answer_question

    reply = answer_question("What products do you sell?")
    print(reply)
"""

import os

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "website_knowledge")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))

_SYSTEM_PROMPT = """You are a helpful brand assistant.
Answer the user's question using ONLY the information provided in the context below.
If the context does not contain enough information to answer the question, say:
"I'm sorry, I don't have that information. Please contact our support team."
Keep your response under 4 sentences. Use bullet points where appropriate.
Do NOT reveal that you are reading from a document or database."""


def _get_collection() -> chromadb.Collection:
    """Return the ChromaDB collection (must already be populated via ingest.py)."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL,
    )
    return client.get_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_fn,
    )


def retrieve_chunks(question: str, top_k: int = RAG_TOP_K) -> list[dict]:
    """
    Retrieve the *top_k* most relevant document chunks for *question*.

    Returns
    -------
    list of ``{"text": str, "url": str}`` dicts.
    """
    collection = _get_collection()
    results = collection.query(
        query_texts=[question],
        n_results=top_k,
        include=["documents", "metadatas"],
    )
    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": doc, "url": meta.get("url", "")})
    return chunks


def answer_question(question: str, chat_history: list[dict] | None = None) -> str:
    """
    Generate a grounded answer for *question* using RAG.

    Parameters
    ----------
    question:
        The user's message.
    chat_history:
        Optional list of prior ``{"role": str, "content": str}`` turns
        to maintain conversational context.

    Returns
    -------
    str
        The assistant's reply.
    """
    chunks = retrieve_chunks(question)
    context = "\n\n---\n\n".join(
        f"Source: {c['url']}\n{c['text']}" for c in chunks
    )

    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]

    if chat_history:
        messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {question}",
    })

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()
