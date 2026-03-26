"""
FastAPI server for the AI Chatbot.

Provides REST API endpoints for chatbot queries and serves web interface.

Run with: uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import logging
import json
from typing import Optional, List
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from api.embeddings import EmbeddingManager
from config import settings

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Phoenix Insurance AI Chatbot",
    description="AI-powered chatbot for insurance inquiries",
    version="1.0.0"
)

# Global embedding manager (initialized lazily)
embedding_manager: Optional[EmbeddingManager] = None


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
    results: List[ResultItem]
    total_results: int


@app.on_event("startup")
async def startup_event():
    """Initialize embedding manager on startup."""
    global embedding_manager
    try:
        embedding_manager = EmbeddingManager(
            embedding_provider=settings.EMBEDDING_PROVIDER,
            vector_db_provider="faiss"
        )
        logger.info("Embedding manager initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing embedding manager: {e}")
        # Continue without embeddings for now


@app.get("/")
async def serve_interface():
    """Serve the chatbot web interface."""
    interface_path = Path(__file__).parent / "static" / "index.html"
    
    if interface_path.exists():
        return FileResponse(interface_path, media_type="text/html")
    
    # Fallback if HTML not found
    return {"message": "Chatbot API is running", "docs": "/docs"}


@app.get("/config")
async def serve_config():
    """Serve the chatbot configuration page."""
    config_path = Path(__file__).parent / "static" / "config.html"
    
    if config_path.exists():
        return FileResponse(config_path, media_type="text/html")
    
    return {"message": "Configuration page not found"}


@app.post("/api/query")
async def query_chatbot(request: QueryRequest) -> QueryResponse:
    """
    Process a chatbot query and return relevant results.
    
    Args:
        request: Query request with question and chatbot_id
    
    Returns:
        QueryResponse with relevant chunks from the vector database
    
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
        # Query the embedding manager
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
        
        return QueryResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results)
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
