"""
Supabase Database Integration for Phoenix Insurance Chatbot.

Handles persistent storage of crawled content, embeddings, and chatbot configurations.
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from functools import lru_cache

from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Supabase PostgreSQL database client."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.client: Optional[Client] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Supabase."""
        try:
            self.client = create_client(self.url, self.key)
            logger.info("✅ Connected to Supabase database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if database connection is active."""
        return self.client is not None
    
    # ==================== CRAWLED DOCUMENTS ====================
    
    async def save_crawled_document(self, document: Dict) -> bool:
        """Save a crawled document to database."""
        if not self.client:
            logger.warning("Database not connected, skipping save")
            return False
        
        try:
            record = {
                "chatbot_id": document.get("chatbot_id"),
                "url": document.get("url"),
                "title": document.get("title"),
                "content": document.get("content"),
                "content_length": document.get("content_length"),
                "page_type": document.get("metadata", {}).get("page_type"),
                "domain": document.get("metadata", {}).get("domain"),
                "path": document.get("metadata", {}).get("path"),
                "raw_data": json.dumps(document),
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("crawled_documents").insert(record).execute()
            logger.debug(f"✅ Saved document: {document['url']}")
            return True
            
        except Exception as e:
            logger.warning(f"Error saving document to database: {e}")
            return False
    
    async def get_documents_by_chatbot(self, chatbot_id: str) -> List[Dict]:
        """Retrieve all documents for a specific chatbot."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("crawled_documents").select("*").eq(
                "chatbot_id", chatbot_id
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.warning(f"Error retrieving documents: {e}")
            return []
    
    # ==================== CHATBOT CONFIGURATIONS ====================
    
    async def save_chatbot_config(self, config: Dict) -> bool:
        """Save chatbot configuration to database."""
        if not self.client:
            return False
        
        try:
            record = {
                "chatbot_id": config.get("chatbot_id"),
                "website_url": config.get("website_url"),
                "name": config.get("name"),
                "description": config.get("description"),
                "max_pages": config.get("max_pages", 50),
                "max_depth": config.get("max_depth", 2),
                "status": config.get("status", "pending"),  # pending, crawling, completed, failed
                "config_data": json.dumps(config),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Check if exists
            existing = self.client.table("chatbot_configs").select("*").eq(
                "chatbot_id", config.get("chatbot_id")
            ).execute()
            
            if existing.data:
                # Update
                self.client.table("chatbot_configs").update(record).eq(
                    "chatbot_id", config.get("chatbot_id")
                ).execute()
                logger.info(f"Updated chatbot config: {config.get('chatbot_id')}")
            else:
                # Insert
                self.client.table("chatbot_configs").insert(record).execute()
                logger.info(f"Created chatbot config: {config.get('chatbot_id')}")
            
            return True
            
        except Exception as e:
            logger.warning(f"Error saving chatbot config: {e}")
            return False
    
    async def get_chatbot_config(self, chatbot_id: str) -> Optional[Dict]:
        """Retrieve chatbot configuration."""
        if not self.client:
            return None
        
        try:
            response = self.client.table("chatbot_configs").select("*").eq(
                "chatbot_id", chatbot_id
            ).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving chatbot config: {e}")
            return None
    
    async def list_all_chatbots(self) -> List[Dict]:
        """List all chatbots from database."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("chatbot_configs").select("*").execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.warning(f"Error listing chatbots: {e}")
            return []
    
    async def update_chatbot_status(self, chatbot_id: str, status: str) -> bool:
        """Update chatbot processing status."""
        if not self.client:
            return False
        
        try:
            self.client.table("chatbot_configs").update({
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("chatbot_id", chatbot_id).execute()
            
            logger.info(f"Updated {chatbot_id} status to: {status}")
            return True
            
        except Exception as e:
            logger.warning(f"Error updating status: {e}")
            return False
    
    # ==================== EMBEDDINGS & CHUNKS ====================
    
    async def save_chunk(self, chunk: Dict, embedding: List[float]) -> bool:
        """Save a chunk with its embedding."""
        if not self.client:
            return False
        
        try:
            record = {
                "chatbot_id": chunk.get("chatbot_id"),
                "document_url": chunk.get("document_url"),
                "chunk_text": chunk.get("text"),
                "embedding": embedding,  # pgvector type
                "metadata": json.dumps(chunk.get("metadata", {})),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.client.table("chunks").insert(record).execute()
            return True
            
        except Exception as e:
            logger.warning(f"Error saving chunk: {e}")
            return False
    
    async def get_chunks_by_chatbot(self, chatbot_id: str) -> List[Dict]:
        """Retrieve all chunks for a chatbot."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("chunks").select("*").eq(
                "chatbot_id", chatbot_id
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.warning(f"Error retrieving chunks: {e}")
            return []
    
    # ==================== QUERY LOGS ====================
    
    async def log_query(self, query_log: Dict) -> bool:
        """Log a user query and response for analytics."""
        if not self.client:
            return False
        
        try:
            record = {
                "chatbot_id": query_log.get("chatbot_id"),
                "user_query": query_log.get("query"),
                "ai_response": query_log.get("response"),
                "confidence_score": query_log.get("confidence_score"),
                "retrieved_chunks": query_log.get("num_chunks", 0),
                "execution_time_ms": query_log.get("execution_time_ms"),
                "user_ip": query_log.get("user_ip"),
                "user_agent": query_log.get("user_agent"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.client.table("query_logs").insert(record).execute()
            return True
            
        except Exception as e:
            logger.debug(f"Error logging query: {e}")
            return False


# Singleton instance
@lru_cache(maxsize=1)
def get_db() -> SupabaseDB:
    """Get or create database connection (singleton)."""
    return SupabaseDB()


async def init_database():
    """Initialize database tables if they don't exist."""
    db = get_db()
    
    if not db.is_connected():
        logger.error("Cannot initialize database: not connected")
        return False
    
    logger.info("Database initialized successfully")
    return True
