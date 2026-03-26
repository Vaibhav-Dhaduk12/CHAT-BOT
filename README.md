# 🤖 Universal AI Chatbot System

> A production-ready, multi-tenant AI chatbot that works on any website. Build intelligent customer support bots with RAG (Retrieval-Augmented Generation) technology.

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.2-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Phase 1 Complete](https://img.shields.io/badge/Status-Phase%201%20Complete%20%E2%9C%85-brightgreen)](PHASE_1_COMPLETE.md)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Technologies Used](#technologies-used)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Quick Start Guide](#quick-start-guide)
- [Running the Project](#running-the-project)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## 🎯 Overview

The **Universal AI Chatbot System** is a modular platform for building intelligent chatbots powered by Retrieval-Augmented Generation (RAG). It consists of three main phases:

- **Phase 1 ✅**: Knowledge Engine (Web crawler + text processor + embeddings)
- **Phase 2 🚧**: Backend Controller (FastAPI server + LLM integration)
- **Phase 3 📋**: Frontend Widget (Universal JavaScript embed)

This project is **currently in Phase 1** with all core components tested and validated.

---

## 🛠 Technologies Used

### Backend Framework & APIs
- **FastAPI** (0.95.2) - Modern REST API framework with async support
- **Uvicorn** (0.23.0) - ASGI web server for FastAPI
- **Pydantic** (1.10.13) - Data validation and settings management

### Web Scraping & Automation
- **Playwright** (1.40.0) - Browser automation for JavaScript rendering
- **BeautifulSoup4** (4.12.0) - HTML parsing and content extraction
- **LXML** - XML/HTML processing

### Natural Language Processing & RAG
- **LangChain** (0.0.350) - RAG orchestration and text processing
- **Sentence-Transformers** (≥2.7.0) - Free local embeddings (HuggingFace models)
- **Tiktoken** (≥0.5.0) - Token counting for LLMs

### Vector Database & Search
- **FAISS** (1.13.2) - Pure-Python vector similarity search (no C++ needed!)
- **NumPy** - Numerical computing

### External APIs
- **OpenAI** (1.3.0) - LLM provider (optional, for Phase 2)

### HTTP & Networking
- **HTTPX** (0.25.0) - Async HTTP client
- **Requests** (2.31.0) - Synchronous HTTP client
- **ARK** - URL handling

### Testing & Development
- **Pytest** (7.4.3) - Testing framework
- **Pytest-AsyncIO** (0.21.1) - Async test support
- **Python-JSON-Logger** (2.0.7) - Structured logging

### Configuration & Utilities
- **Python-DotEnv** (1.0.0) - Environment variable management
- **Cryptography** (41.0.7) - Security utilities
- **Tenacity** (8.2.3) - Retry logic
- **Validators** (0.22.0) - Data validation

---

## ✨ Features

### Phase 1: Knowledge Engine ✅

| Feature | Description | Status |
|---------|-------------|--------|
| **Web Crawler** | Async Playwright-based crawling with BFS algorithm | ✅ |
| **JavaScript Support** | Renders SPAs and dynamic content | ✅ |
| **Text Processor** | LangChain semantic chunking (400-600 tokens) | ✅ |
| **Local Embeddings** | Free HuggingFace models (no API keys needed) | ✅ |
| **Vector Database** | FAISS for efficient similarity search | ✅ |
| **Multi-Tenancy** | Namespace-based data isolation | ✅ |
| **Configuration** | 80+ tunable environment variables | ✅ |
| **Unit Tests** | 8/8 passing integration tests | ✅ |

### Planned: Phase 2 & 3
- FastAPI REST endpoints for chat
- LLM integration (OpenAI, Anthropic, local models)
- Universal JavaScript widget for any website
- Real-time chat streaming
- Analytics and metering

---

## 📁 Project Structure

```
CHAT-BOT/
│
├── 📄 README.md                    # This file
├── 📄 PHASE_1_COMPLETE.md          # Phase 1 summary & metrics
├── 📄 PHASE_1_README.md            # Detailed technical setup
├── 📄 config.py                    # Pydantic configuration system
├── 📄 requirements.txt             # Python dependencies (40+)
├── 📄 .env.example                 # Environment variables template
│
├── 📂 api/                         # Backend API modules
│   ├── __init__.py
│   ├── embeddings.py              # Embedding generation & FAISS DB
│   ├── processor.py               # Text chunking with LangChain
│   └── routes/                    # (Phase 2) API endpoints
│
├── 📂 scripts/                     # Utility scripts
│   ├── __init__.py
│   └── crawler.py                 # Web crawler & content extraction
│
├── 📂 tests/                       # Unit tests
│   ├── __init__.py
│   └── test_phase1.py             # 8 integration tests
│
├── 📂 data/                        # Data storage
│   ├── raw/                       # Crawled documents
│   ├── processed/                 # Chunked documents
│   └── vectors/                   # FAISS indices
│
├── 📂 logs/                        # Application logs
│
└── 📂 .github/                     # GitHub configuration
    └── instructions/              # AI agent instructions
```

---

## 📦 Prerequisites

Before starting, ensure you have:

### System Requirements
- **Python**: 3.10+ (tested on 3.12)
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB+ recommended for model inference)
- **Disk**: ~2GB for dependencies and models

### Required Software
- **Git**: For version control
- **pip**: Python package manager

### Optional
- **Docker**: For containerized deployment
- **Visual Studio Code**: Recommended IDE

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/CHAT-BOT.git
cd CHAT-BOT
```

### Step 2: Create Python Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**Installation typically takes 2-5 minutes.**

> Note: FAISS is pure Python and requires NO C++ build tools, so installation is frictionless on all platforms!

### Step 4: Setup Environment Variables

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your settings (optional for Phase 1)
# Default values work out-of-the-box!
```

### Step 5: Install Playwright Browsers

```bash
# First-time setup: Install chromium browser
playwright install chromium
```

### Step 6: Verify Installation

```bash
# Run the test suite
pytest tests/test_phase1.py -v

# Expected output: 8/8 PASSED ✅
```

---

## 🎯 Quick Start Guide

### 5-Minute Test

Run the complete RAG pipeline with test data:

```bash
# Run all Phase 1 tests
pytest tests/test_phase1.py -v

# You should see:
# ✅ test_chunk_id_generation PASSED
# ✅ test_token_counting PASSED
# ✅ test_huggingface_embedding_dimension PASSED
# ✅ test_embedding_manager_initialization PASSED
# ✅ test_batch_embedding PASSED
# ✅ test_settings_loaded PASSED
# ✅ test_embedding_provider_valid PASSED
# ✅ test_full_embedding_pipeline PASSED
#
# ===== 8 passed in ~25 seconds =====
```

---

## 🔄 Running the Project

### Full 4-Step RAG Pipeline

Create a file `run_pipeline.py`:

```python
import asyncio
import json
from pathlib import Path
from scripts.crawler import WebCrawler
from api.processor import ChunkProcessor
from api.embeddings import EmbeddingManager

async def main():
    chatbot_id = "my_bot"
    
    # ============== STEP 1: CRAWL ==============
    print("📡 Step 1: Crawling website...")
    crawler = WebCrawler(chatbot_id=chatbot_id)
    await crawler.crawl_website(
        "https://docs.python.org/3/library/functions.html",
        max_depth=1,
        max_pages=5
    )
    stats = crawler.get_crawl_stats()
    print(f"✅ Crawled {stats['total_pages']} pages")
    
    # ============== STEP 2: PROCESS ==============
    print("\n📝 Step 2: Processing documents...")
    processor = ChunkProcessor(chatbot_id=chatbot_id)
    chunks = await processor.process_raw_documents()
    stats = processor.get_processing_stats()
    print(f"✅ Created {stats['total_chunks']} chunks from {stats['total_documents']} docs")
    
    # ============== STEP 3: EMBED ==============
    print("\n🧠 Step 3: Generating embeddings...")
    manager = EmbeddingManager("huggingface", "faiss")
    success = await manager.embed_and_store(chunks, namespace=chatbot_id)
    if success:
        print(f"✅ Embedded and indexed {len(chunks)} chunks")
    
    # ============== STEP 4: QUERY ==============
    print("\n🔍 Step 4: Testing retrieval...")
    results = await manager.query(
        "What are built-in functions?",
        namespace=chatbot_id,
        top_k=3
    )
    
    print(f"\nTop {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['text'][:150]}...")
        print(f"   Distance: {result['distance']:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python run_pipeline.py
```

Expected output:
```
📡 Step 1: Crawling website...
✅ Crawled 5 pages

📝 Step 2: Processing documents...
✅ Created 47 chunks from 5 docs

🧠 Step 3: Generating embeddings...
✅ Embedded and indexed 47 chunks

🔍 Step 4: Testing retrieval...

Top 3 results:
1. The built-in functions are defined in the standard library...
   Distance: 0.2341
```

### Individual Component Usage

#### 🕷️ Crawler Only

```python
from scripts.crawler import WebCrawler
import asyncio

async def crawl():
    crawler = WebCrawler(chatbot_id="test_bot")
    await crawler.crawl_website(
        url="https://example.com",
        max_depth=2,
        max_pages=10
    )
    
    stats = crawler.get_crawl_stats()
    print(f"Pages crawled: {stats['total_pages']}")
    print(f"Total bytes: {stats['total_bytes']}")

asyncio.run(crawl())
```

#### 📝 Processor Only

```python
from api.processor import ChunkProcessor
import asyncio

async def process():
    processor = ChunkProcessor(chatbot_id="test_bot")
    chunks = await processor.process_raw_documents()
    print(f"Created {len(chunks)} chunks")
    for chunk in chunks[:2]:
        print(f"- {chunk['text'][:100]}...")

asyncio.run(process())
```

#### 🧠 Embeddings Only

```python
from api.embeddings import EmbeddingManager
import asyncio

async def embed():
    manager = EmbeddingManager("huggingface", "faiss")
    
    # Sample chunks
    chunks = [
        {"id": "1", "text": "Python is a programming language"},
        {"id": "2", "text": "FastAPI is a modern web framework"}
    ]
    
    # Store embeddings
    await manager.embed_and_store(chunks, namespace="test")
    
    # Query
    results = await manager.query("What is Python?", namespace="test", top_k=2)
    for result in results:
        print(f"✓ {result['text']}")

asyncio.run(embed())
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# ===== CRAWLER SETTINGS =====
CRAWLER_TIMEOUT=30                          # Seconds per page
CRAWLER_MAX_DEPTH=3                         # Crawl depth
CRAWLER_MAX_PAGES_PER_DOMAIN=100            # Max pages to crawl
CRAWLER_RESPECT_ROBOTS_TXT=true             # Respect robots.txt

# ===== TEXT PROCESSING =====
CHUNK_SIZE=500                              # Target tokens per chunk
CHUNK_OVERLAP=100                           # Overlap between chunks
MIN_CHUNK_SIZE=100                          # Minimum chunk tokens

# ===== EMBEDDINGS (FREE, LOCAL) =====
EMBEDDING_PROVIDER=huggingface              # or 'openai'
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32                     # Batch size for encoding

# ===== VECTOR DATABASE =====
VECTOR_DB_PROVIDER=faiss                    # Local vector search
CHROMADB_PATH=./data/vectors                # Storage location

# ===== RAG RETRIEVAL =====
RAG_TOP_K_CHUNKS=4                          # Top-K similar documents
RAG_CONFIDENCE_THRESHOLD=0.7                # Confidence score threshold

# ===== APPLICATION =====
APP_NAME=Universal Chatbot Backend
ENVIRONMENT=development                     # development, staging, production
DEBUG=true
LOG_LEVEL=INFO
```

### Default Configuration

All settings have sensible defaults, so you can use them without modifying `.env`:

```python
from config import settings

print(settings.CHUNK_SIZE)          # 500
print(settings.CRAWLER_TIMEOUT)     # 30
print(settings.RAG_TOP_K_CHUNKS)    # 4
```

---

## 🧪 Testing

### Run All Tests

```bash
# Run complete test suite
pytest tests/test_phase1.py -v

# Run with coverage report
pytest tests/test_phase1.py --cov=api --cov=scripts
```

### Run Specific Tests

```bash
# Run only embeddings tests
pytest tests/test_phase1.py::TestEmbeddings -v

# Run only one test
pytest tests/test_phase1.py::TestChunkProcessor::test_token_counting -v
```

### Test Output Example

```
==================== test session starts ====================
platform win32 -- Python 3.12.10, pytest-7.4.3
collected 8 items

tests/test_phase1.py::TestChunkProcessor::test_chunk_id_generation PASSED [ 12%]
tests/test_phase1.py::TestChunkProcessor::test_token_counting PASSED [ 25%]
tests/test_phase1.py::TestEmbeddings::test_huggingface_embedding_dimension PASSED [ 37%]
tests/test_phase1.py::TestEmbeddings::test_embedding_manager_initialization PASSED [ 50%]
tests/test_phase1.py::TestEmbeddings::test_batch_embedding PASSED [ 62%]
tests/test_phase1.py::TestConfiguration::test_settings_loaded PASSED [ 75%]
tests/test_phase1.py::TestConfiguration::test_embedding_provider_valid PASSED [ 87%]
tests/test_phase1.py::test_full_embedding_pipeline PASSED [100%]

===================== 8 passed in 23.57s =====================
```

---

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'api'"

**Solution**: Ensure you're running from the project root directory:
```bash
cd /path/to/CHAT-BOT
python your_script.py
```

### Problem: Playwright browser not found

**Solution**: Install Playwright chromium browser:
```bash
playwright install chromium
```

### Problem: "Out of memory" error during embeddings

**Solution**: Reduce batch size in `.env`:
```bash
EMBEDDING_BATCH_SIZE=16  # Reduced from 32
```

### Problem: Slow first embedding generation

**Cause**: HuggingFace model downloading (~240MB on first run)  
**Solution**: This is normal! First run takes 2-3 minutes, subsequent runs are instant (model cached)

### Problem: Tests failing with import errors

**Solution**: Reinstall dependencies in clean environment:
```bash
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Problem: FAISS index corruption

**Solution**: Delete the vector database and regenerate:
```bash
rm -rf data/vectors/
python run_pipeline.py  # Recreates fresh index
```

---

## 📊 Project Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 1500+ |
| **Test Coverage** | 8/8 tests passing |
| **Dependencies** | 40+ packages |
| **Configuration Options** | 80+ parameters |
| **Supported Embeddings** | 2 providers (HuggingFace, OpenAI) |
| **Supported Vector DBs** | 2 providers (FAISS, ChromaDB-ready) |

---

## 🚀 Next Steps

### Phase 2: Backend Controller (Coming Soon)

- [ ] FastAPI REST endpoints (`POST /chat`)
- [ ] LLM integration (OpenAI, Anthropic, local models)
- [ ] WebSocket support for real-time streaming
- [ ] Authentication & API keys
- [ ] Request/response validation

### Phase 3: Frontend Widget (Coming Soon)

- [ ] Universal JavaScript embed script
- [ ] Responsive widget UI
- [ ] Real-time chat streaming
- [ ] Brand customization (CSS variables)
- [ ] Analytics tracking

### Deployment

- [ ] Docker containerization
- [ ] AWS Lambda/Google Cloud Run setup
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring & alerting
- [ ] Multi-region deployment

---

## 📚 Additional Resources

- **[Phase 1 Complete Documentation](PHASE_1_COMPLETE.md)** - Detailed completion summary
- **[Phase 1 Technical README](PHASE_1_README.md)** - Advanced setup & configuration
- **[LangChain Docs](https://python.langchain.com/)** - RAG framework documentation
- **[FAISS Docs](https://github.com/facebookresearch/faiss)** - Vector database guide
- **[FastAPI Docs](https://fastapi.tiangolo.com/)** - REST API framework

---

## 💡 Quick Tips

1. **First time is slow**: Initial embeddings download HuggingFace models (~240MB), but it's cached afterward
2. **No API keys needed**: Phase 1 uses free local HuggingFace models
3. **Windows-friendly**: FAISS is pure Python, needs no C++ build tools
4. **Async throughout**: All I/O operations are non-blocking for performance
5. **Multi-tenant ready**: Namespace-based isolation for multiple chatbots

---

## 📝 License

This project is licensed under the MIT License—see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Support

For questions or issues:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [Phase 1 Documentation](PHASE_1_COMPLETE.md)
3. Open an GitHub issue
4. Contact: your-email@example.com

---

## 🎯 Roadmap

```
┌─────────────────────────────────────────────────────┐
│ Phase 1: Knowledge Engine ✅ COMPLETE              │
│ - Web Crawler, Text Processor, Embeddings, Tests   │
└──────────────┬──────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────┐
│ Phase 2: Backend Controller 🚧 IN PROGRESS        │
│ - FastAPI, LLM Integration, Chat Endpoints         │
└──────────────┬──────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────┐
│ Phase 3: Frontend Widget 📋 PLANNED               │
│ - JS Embed, Real-time Chat, Analytics              │
└─────────────────────────────────────────────────────┘
```

---

**Made with ❤️ by the Universal Chatbot Team**  
**Last Updated**: March 2026 | **Status**: Phase 1 ✅ Complete