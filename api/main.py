"""
FastAPI server for the AI Chatbot.

Provides REST API endpoints for chatbot queries and serves web interface.

Run with: uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import logging
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from api.embeddings import EmbeddingManager
from api.llm_provider import LLMManager
from config import settings

try:
    from api.database import SupabaseDB
    SUPABASE_AVAILABLE = True
except Exception as e:
    SupabaseDB = None  # type: ignore[assignment]
    SUPABASE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Supabase module unavailable: {e}")

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Phoenix Insurance AI Chatbot",
    description="AI-powered chatbot for insurance inquiries",
    version="1.0.0"
)

# Global managers (initialized lazily)
embedding_manager: Optional[EmbeddingManager] = None
llm_manager: Optional[LLMManager] = None
db_manager: Optional[Any] = None
# In-memory crawl job state for UI polling.
crawl_jobs: Dict[str, Dict[str, Any]] = {}


class QueryRequest(BaseModel):
    """Request model for chatbot queries."""
    query: str = Field(..., description="User's question")
    chatbot_id: str = Field(default="phoenix_insurance_bot", description="Chatbot identifier")
    top_k: int = Field(default=4, description="Number of results to return", ge=1, le=20)


class ResultItem(BaseModel):
    """Individual result from the vector database."""
    rank: int
    text: str
    source_url: str = ""
    page_title: str = ""
    distance: float


class QueryResponse(BaseModel):
    """Response model for chatbot queries."""
    query: str
    response: str = Field(..., description="AI-generated response to the query")
    results: List[ResultItem]
    total_results: int
    confidence_score: float = Field(0.0, description="Confidence score based on top result distance")


class ChatbotConfigRequest(BaseModel):
    """Request model for chatbot configuration."""
    chatbot_id: str = Field(..., description="Unique identifier for chatbot")
    name: str = Field(..., description="Display name for chatbot")
    website_url: str = Field(..., description="URL of website to crawl")
    description: Optional[str] = Field(None, description="Chatbot description")
    max_pages: int = Field(default=50, description="Maximum pages to crawl", ge=1, le=500)
    max_depth: int = Field(default=2, description="Maximum crawl depth", ge=1, le=10)
    status: str = Field(default="pending", description="Crawl status")


class CrawlRequest(BaseModel):
    """Request model for triggering crawl."""
    chatbot_id: str = Field(..., description="Chatbot identifier")
    url: str = Field(..., description="URL to crawl")
    max_pages: int = Field(default=50, ge=1, le=500)
    max_depth: int = Field(default=2, ge=1, le=10)
    save_to_database: bool = Field(default=True, description="Save results to database")


class CrawlResponse(BaseModel):
    """Response model for crawl operation."""
    chatbot_id: str
    pages_crawled: int
    chunks_created: int
    documents_saved: int
    status: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize embedding manager and LLM on startup."""
    global embedding_manager, llm_manager, db_manager
    try:
        embedding_manager = EmbeddingManager(
            embedding_provider=settings.EMBEDDING_PROVIDER,
            vector_db_provider="faiss"
        )
        logger.info("✓ Embedding manager initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing embedding manager: {e}")
    
    try:
        llm_manager = LLMManager(provider=settings.EMBEDDING_PROVIDER)
        logger.info("✓ LLM manager initialized successfully")
    except Exception as e:
        logger.warning(f"LLM manager initialization warning: {e}")
        logger.warning("Chatbot will still work but use fallback responses")
    
    # Initialize Supabase if enabled
    if settings.USE_SUPABASE and SUPABASE_AVAILABLE:
        try:
            db_manager = SupabaseDB()
            logger.info("✓ Supabase database connection initialized")
        except Exception as e:
            logger.warning(f"Supabase initialization warning: {e}")
            logger.warning("Chatbot will work without database persistence")
    elif settings.USE_SUPABASE and not SUPABASE_AVAILABLE:
        logger.warning("USE_SUPABASE=true but supabase package is missing; continuing without database persistence")


@app.get("/")
async def serve_interface():
    """Serve the chatbot web interface."""
    interface_path = Path(__file__).parent / "static" / "index.html"
    
    try:
        if interface_path.exists():
            with open(interface_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving interface: {e}")
    
    # Fallback if HTML not found or error occurred
    return {"message": "Chatbot API is running", "docs": "/docs"}


@app.get("/config")
async def serve_config():
    """Serve the chatbot configuration page."""
    config_path = Path(__file__).parent / "static" / "crawler-config.html"
    
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving config: {e}")
    
    return {"message": "Configuration page not found"}


@app.post("/api/chatbots/{chatbot_id}/config")
async def save_chatbot_config(chatbot_id: str, request: ChatbotConfigRequest):
    """Save chatbot configuration to database."""
    try:
        if settings.USE_SUPABASE and SUPABASE_AVAILABLE:
            db = SupabaseDB()
            saved = await db.save_chatbot_config({
                "chatbot_id": chatbot_id,
                "website_url": request.website_url,
                "name": request.name,
                "description": request.description or "",
                "max_pages": request.max_pages,
                "max_depth": request.max_depth,
                "config_data": {
                    "max_pages": request.max_pages,
                    "max_depth": request.max_depth
                },
                "status": request.status
            })

            if not saved:
                raise RuntimeError("Failed to save chatbot configuration")

            logger.info(f"✓ Configuration saved for chatbot: {chatbot_id}")
            return {
                "status": "success",
                "message": f"Configuration saved for {chatbot_id}",
                "chatbot_id": chatbot_id
            }
        else:
            # Fallback: save to local filesystem
            return {
                "status": "success",
                "message": "Configuration saved (local mode)",
                "chatbot_id": chatbot_id
            }
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def crawl_and_process(
    chatbot_id: str, 
    url: str, 
    max_pages: int, 
    max_depth: int,
    save_to_db: bool
):
    """Background task to crawl website and save to database."""
    try:
        logger.info(f"🚀 Starting crawl for {chatbot_id}: {url}")
        crawl_jobs[chatbot_id] = {
            "chatbot_id": chatbot_id,
            "url": url,
            "status": "crawling",
            "pages_crawled": 0,
            "chunks_created": 0,
            "documents_saved": 0,
            "error": None,
        }
        
        # Run crawler
        from scripts.crawler import WebCrawler
        crawler = WebCrawler(chatbot_id=chatbot_id)
        documents = await crawler.crawl_website(url)
        crawl_jobs[chatbot_id]["pages_crawled"] = len(documents)
        
        logger.info(f"✓ Crawled {len(documents)} documents")

        # Process crawled pages into chunks and index embeddings.
        chunks_count = 0
        try:
            from api.processor import ChunkProcessor
            processor = ChunkProcessor(chatbot_id=chatbot_id)
            chunks = await processor.process_raw_documents()
            chunks_count = len(chunks)
            crawl_jobs[chatbot_id]["chunks_created"] = chunks_count

            if embedding_manager and chunks:
                await embedding_manager.embed_and_store(chunks, namespace=chatbot_id)
        except Exception as process_error:
            logger.warning(f"Chunk processing warning for {chatbot_id}: {process_error}")
        
        # Save to database if enabled
        if save_to_db and settings.USE_SUPABASE and SUPABASE_AVAILABLE:
            try:
                db = SupabaseDB()
                
                # Save documents
                saved_docs = 0
                for doc in documents:
                    if await db.save_crawled_document(doc):
                        saved_docs += 1
                crawl_jobs[chatbot_id]["documents_saved"] = saved_docs
                
                # Update status to completed
                await db.update_chatbot_status(chatbot_id, "completed")
                logger.info(f"✓ Saved {saved_docs}/{len(documents)} documents to database")
                
            except Exception as db_error:
                logger.error(f"Error saving to database: {db_error}")
                if settings.USE_SUPABASE and SUPABASE_AVAILABLE:
                    db = SupabaseDB()
                    await db.update_chatbot_status(chatbot_id, "failed")

        crawl_jobs[chatbot_id]["status"] = "completed"
    
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        crawl_jobs[chatbot_id] = {
            "chatbot_id": chatbot_id,
            "url": url,
            "status": "failed",
            "pages_crawled": crawl_jobs.get(chatbot_id, {}).get("pages_crawled", 0),
            "chunks_created": crawl_jobs.get(chatbot_id, {}).get("chunks_created", 0),
            "documents_saved": crawl_jobs.get(chatbot_id, {}).get("documents_saved", 0),
            "error": str(e),
        }
        if settings.USE_SUPABASE and SUPABASE_AVAILABLE:
            db = SupabaseDB()
            await db.update_chatbot_status(chatbot_id, "failed")


@app.post("/api/crawl", response_model=CrawlResponse)
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Trigger website crawling with optional database persistence."""
    try:
        chatbot_id = request.chatbot_id
        url = request.url
        
        logger.info(f"📍 Crawl request received: {chatbot_id} -> {url}")
        
        # Update status to crawling
        if settings.USE_SUPABASE and SUPABASE_AVAILABLE:
            db = SupabaseDB()
            await db.update_chatbot_status(chatbot_id, "crawling")

        crawl_jobs[chatbot_id] = {
            "chatbot_id": chatbot_id,
            "url": url,
            "status": "queued",
            "pages_crawled": 0,
            "chunks_created": 0,
            "documents_saved": 0,
            "error": None,
        }
        
        # Add crawl task to background
        background_tasks.add_task(
            crawl_and_process,
            chatbot_id=chatbot_id,
            url=url,
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            save_to_db=request.save_to_database
        )
        
        return CrawlResponse(
            chatbot_id=chatbot_id,
            pages_crawled=0,
            chunks_created=0,
            documents_saved=0,
            status="started",
            message=f"Crawl queued for {chatbot_id}. Processing in background..."
        )
    
    except Exception as e:
        logger.error(f"Error starting crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chatbots/{chatbot_id}/documents")
async def get_chatbot_documents(chatbot_id: str):
    """Get all documents for a specific chatbot from database."""
    try:
        if settings.USE_SUPABASE and SUPABASE_AVAILABLE:
            db = SupabaseDB()
            documents = await db.get_documents_by_chatbot(chatbot_id)
            return {
                "chatbot_id": chatbot_id,
                "total_documents": len(documents),
                "documents": documents
            }
        else:
            return {
                "chatbot_id": chatbot_id,
                "total_documents": 0,
                "documents": []
            }
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/crawl-status/{chatbot_id}")
async def get_crawl_status(chatbot_id: str):
    """Return crawl progress for a chatbot ID."""
    # Prefer in-memory live status.
    if chatbot_id in crawl_jobs:
        return crawl_jobs[chatbot_id]

    # Fallback from processed data when no active in-memory job exists.
    processed_dir = Path(settings.DATA_PROCESSED_DIR) / chatbot_id
    chunks_file = processed_dir / "chunks_index.json"
    raw_dir = Path(settings.DATA_RAW_DIR) / chatbot_id

    pages_crawled = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0
    chunks_created = 0
    if chunks_file.exists():
        try:
            with open(chunks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            chunks_created = len(data.get("chunks", []))
        except Exception:
            chunks_created = 0

    status = "completed" if (pages_crawled > 0 or chunks_created > 0) else "not_found"
    return {
        "chatbot_id": chatbot_id,
        "status": status,
        "pages_crawled": pages_crawled,
        "chunks_created": chunks_created,
        "documents_saved": pages_crawled,
        "error": None,
    }


@app.post("/api/query")
async def query_chatbot(request: QueryRequest) -> QueryResponse:
    """
    Process a chatbot query and return relevant results + AI-generated response.
    
    Args:
        request: Query request with question and chatbot_id
    
    Returns:
        QueryResponse with AI response and relevant chunks from vector database
    
    Raises:
        HTTPException: If embedding manager not initialized or query fails
    """
    if not embedding_manager:
        raise HTTPException(
            status_code=503,
            detail="Embedding manager not initialized"
        )
    
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        # Step 1: Query the embedding manager for relevant context
        results = await embedding_manager.query(
            query_text=request.query,
            namespace=request.chatbot_id,
            top_k=request.top_k
        )
        
        # Format results for response
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "text": result.get("text", "")[:200],  # First 200 chars
                "source_url": result.get("metadata", {}).get("source_url", ""),
                "page_title": result.get("metadata", {}).get("page_title", ""),
                "distance": result.get("distance", 0)
            })
        
        # Calculate confidence score (1 - normalized distance, capped at 0.95)
        confidence_score = 0.0
        if formatted_results and len(formatted_results) > 0:
            distance = formatted_results[0].get("distance", 1.0)
            # Convert distance to confidence (0 distance = high confidence)
            confidence_score = min(0.95, max(0.0, 1.0 - distance))
        
        # Step 2: Generate AI response using LLM
        ai_response = "I couldn't find information about that."
        
        if llm_manager and formatted_results:
            try:
                ai_response = await llm_manager.generate_response(
                    query=request.query,
                    context=results,
                    max_tokens=500
                )
                logger.debug(f"Generated AI response: {ai_response[:100]}...")
            except Exception as e:
                logger.warning(f"LLM generation failed, using fallback: {e}")
                if formatted_results:
                    ai_response = f"Based on our records: {formatted_results[0]['text']}..."
        
        return QueryResponse(
            query=request.query,
            response=ai_response,
            results=formatted_results,
            total_results=len(formatted_results),
            confidence_score=confidence_score
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "embedding_manager": "initialized" if embedding_manager else "not_initialized",
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL
    }


@app.get("/api/chatbots/{chatbot_id}/stats")
async def get_chatbot_stats(chatbot_id: str):
    """Get statistics for a specific chatbot."""
    try:
        # Try to load chunks index
        processed_dir = Path(settings.DATA_PROCESSED_DIR) / chatbot_id
        chunks_file = processed_dir / "chunks_index.json"
        
        if chunks_file.exists():
            with open(chunks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            chunks = data.get("chunks", [])
            return {
                "chatbot_id": chatbot_id,
                "total_chunks": len(chunks),
                "status": "ready"
            }
        else:
            return {
                "chatbot_id": chatbot_id,
                "total_chunks": 0,
                "status": "no_data"
            }
    
    except Exception as e:
        logger.error(f"Error getting chatbot stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )


@app.get("/api/list-chatbots")
async def list_chatbots():
    """List all available chatbots with their statistics."""
    try:
        chatbots = []
        
        # Scan processed directory for chatbot folders
        processed_dir = Path(settings.DATA_PROCESSED_DIR)
        if processed_dir.exists():
            for chatbot_folder in processed_dir.iterdir():
                if chatbot_folder.is_dir():
                    chatbot_id = chatbot_folder.name
                    chunks_file = chatbot_folder / "chunks_index.json"
                    
                    # Get chunks count
                    chunks_count = 0
                    if chunks_file.exists():
                        try:
                            with open(chunks_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                chunks_count = len(data.get("chunks", []))
                        except:
                            pass
                    
                    # Get raw files count
                    raw_dir = Path(settings.DATA_RAW_DIR) / chatbot_id
                    raw_files_count = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0
                    
                    # Try to get website URL from raw documents
                    url = "Unknown"
                    if raw_dir.exists():
                        raw_files = list(raw_dir.glob("*.json"))
                        if raw_files:
                            try:
                                with open(raw_files[0], "r", encoding="utf-8") as f:
                                    doc = json.load(f)
                                    url = doc.get("url", "Unknown")
                                    # Extract domain
                                    parsed = urlparse(url)
                                    url = f"{parsed.scheme}://{parsed.netloc}"
                            except:
                                pass
                    
                    chatbots.append({
                        "id": chatbot_id,
                        "chatbot_id": chatbot_id,
                        "url": url,
                        "chunks": chunks_count,
                        "raw_files": raw_files_count,
                        "status": "ready" if chunks_count > 0 else "indexing"
                    })
        
        # Sort by most recently used/largest knowledge base
        chatbots.sort(key=lambda x: x["chunks"], reverse=True)
        
        return {
            "total": len(chatbots),
            "chatbots": chatbots
        }
    
    except Exception as e:
        logger.error(f"Error listing chatbots: {e}")
        return {
            "total": 0,
            "chatbots": []
        }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
