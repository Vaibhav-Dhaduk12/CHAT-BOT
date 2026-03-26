# RAG Chat-Bot 🤖

A full-stack, **Retrieval-Augmented Generation (RAG)** chatbot that automatically learns any website and lets you embed an AI assistant on any page via a single `<script>` tag.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Any website                                                          │
│  ┌────────────────────┐   <script src="chat-widget.js">              │
│  │  Floating Chat UI  │◄──────────────────────────────────────────── │
│  └────────┬───────────┘                                              │
└───────────┼──────────────────────────────────────────────────────────┘
            │ POST /chat
            ▼
┌───────────────────────────┐
│  FastAPI Backend (api.py) │
│  POST /ingest             │
│  POST /chat               │
│  GET  /health             │
└───────────┬───────────────┘
            │
    ┌───────┴────────┐
    ▼                ▼
┌──────────┐   ┌──────────────────────────────────┐
│ ChromaDB │   │  OpenAI                           │
│ (vectors)│   │  • text-embedding-3-small         │
└──────────┘   │  • gpt-4o-mini                    │
               └──────────────────────────────────┘
```

### Components

| Layer | Files | Description |
|---|---|---|
| **Web Scraper** | `backend/scraper.py` | BFS crawler using `requests` + `BeautifulSoup`. Extracts clean text from every page of a domain. |
| **Ingestion Pipeline** | `backend/ingest.py` | Splits text into ~500-char chunks (`RecursiveCharacterTextSplitter`), embeds them via OpenAI and upserts into ChromaDB. |
| **RAG Chain** | `backend/rag_chain.py` | Embeds the user question, retrieves top-k chunks, and calls `gpt-4o-mini` with a strict brand-safety prompt. |
| **REST API** | `backend/api.py` | FastAPI server with `/ingest`, `/chat` and `/health` endpoints plus CORS support. |
| **Chat Widget** | `widget/chat-widget.js` | Zero-dependency floating chat UI. Embeds on any website with two lines of HTML. |
| **Demo Page** | `widget/demo.html` | Stand-alone HTML demo showing the widget and integration instructions. |

---

## Quick Start

### 1 — Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Open .env and set OPENAI_API_KEY (and optionally other values)

# Ingest your website (one-time or whenever content changes)
python ingest.py --url https://your-site.com --max-pages 50

# Start the API server
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The interactive API docs are available at `http://localhost:8000/docs`.

### 2 — Embed the widget

Paste this snippet just before `</body>` on any HTML page:

```html
<script>
  window.ChatWidgetConfig = {
    apiUrl:       "https://your-api-server.com",  // URL of the FastAPI server
    title:        "Support Chat",
    primaryColor: "#4f46e5",
  };
</script>
<script src="chat-widget.js" defer></script>
```

Open `widget/demo.html` in your browser for a live preview.

---

## API Reference

### `POST /ingest`
Crawl a URL and populate the vector database.

```json
// Request
{ "url": "https://example.com", "max_pages": 50 }

// Response
{ "message": "Ingestion complete.", "pages_scraped": 12, "chunks_stored": 348 }
```

### `POST /chat`
Ask a question grounded in the ingested content.

```json
// Request
{ "message": "What products do you sell?", "history": [] }

// Response
{ "reply": "We sell..." }
```

### `GET /health`
Simple liveness probe — returns `{"status": "ok"}`.

---

## Project Structure

```
CHAT-BOT/
├── backend/
│   ├── scraper.py        # Web crawler & text extractor
│   ├── ingest.py         # Chunking + ChromaDB ingestion (CLI)
│   ├── rag_chain.py      # RAG query engine
│   ├── api.py            # FastAPI REST server
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment variable template
├── widget/
│   ├── chat-widget.js    # Embeddable JS chat widget
│   └── demo.html         # Demo page
├── .gitignore
└── README.md
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Web Scraping | Python, `requests`, `BeautifulSoup4` |
| Text Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector Database | ChromaDB (local, persistent) |
| LLM | OpenAI `gpt-4o-mini` |
| Backend API | FastAPI + Uvicorn |
| Frontend Widget | Vanilla JavaScript (no dependencies) |
