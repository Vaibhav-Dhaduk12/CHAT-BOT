"""
Data Processor for text chunking and preparation.

Features:
- Semantic chunking using LangChain's RecursiveCharacterTextSplitter
- Preserves metadata and source information
- Configurable chunk size and overlap
- Validation of chunk integrity
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Iterator
from datetime import datetime
import hashlib

from langchain.text_splitter import RecursiveCharacterTextSplitter
import aiofiles
import tiktoken

from config import settings

logger = logging.getLogger(__name__)


class ChunkProcessor:
    """Process and chunk extracted documents."""
    
    def __init__(self, chatbot_id: str):
        self.chatbot_id = chatbot_id
        self.raw_dir = Path(settings.DATA_RAW_DIR) / chatbot_id
        self.processed_dir = Path(settings.DATA_PROCESSED_DIR) / chatbot_id
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Token counter (for tracking token usage)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not load tiktoken: {e}, using fallback counter")
            self.tokenizer = None
    
    async def process_raw_documents(self) -> List[Dict]:
        """
        Process all raw documents in the chatbot's directory.
        
        Returns:
            List of chunks with metadata
        """
        logger.info(f"Processing raw documents for chatbot_id={self.chatbot_id}")
        
        if not self.raw_dir.exists():
            logger.warning(f"Raw data directory does not exist: {self.raw_dir}")
            return []
        
        all_chunks = []
        raw_files = list(self.raw_dir.glob("*.json"))
        
        for raw_file in raw_files:
            try:
                async with aiofiles.open(raw_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    document = json.loads(content)
                
                chunks = await self._chunk_document(document)
                all_chunks.extend(chunks)
                
                logger.debug(f"Chunked {raw_file.name}: {len(chunks)} chunks created")
                
            except Exception as e:
                logger.error(f"Error processing {raw_file.name}: {e}")
                continue
        
        # Save all chunks to a single index file
        await self._save_chunks_index(all_chunks)
        
        logger.info(f"Processing complete: {len(all_chunks)} total chunks created")
        return all_chunks
    
    async def _chunk_document(self, document: Dict) -> List[Dict]:
        """
        Split a single document into chunks.
        """
        text = document.get("content", "")
        
        if not text or len(text) < settings.CHUNK_MIN_SIZE:
            logger.debug(f"Skipping document {document['url']}: insufficient content")
            return []
        
        # Chunk the text
        text_chunks = self.splitter.split_text(text)
        
        chunks = []
        for chunk_idx, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                continue
            
            # Validate chunk
            if len(chunk_text) < settings.CHUNK_MIN_SIZE:
                continue
            
            chunk_id = self._generate_chunk_id(
                document["url"],
                chunk_idx
            )
            
            chunk = {
                "id": chunk_id,
                "text": chunk_text,
                "source_url": document["url"],
                "page_title": document.get("title", "Untitled"),
                "chunk_index": chunk_idx,
                "content_length": len(chunk_text),
                "token_count": self._count_tokens(chunk_text),
                "created_at": datetime.utcnow().isoformat(),
                "chatbot_id": self.chatbot_id,
                "metadata": {
                    "page_type": document.get("metadata", {}).get("page_type", "general"),
                    "domain": document.get("metadata", {}).get("domain", ""),
                    "path": document.get("metadata", {}).get("path", "")
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    async def _save_chunks_index(self, chunks: List[Dict]) -> None:
        """Save chunks index to JSON file for later retrieval."""
        try:
            index_file = self.processed_dir / "chunks_index.json"
            
            async with aiofiles.open(index_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps({
                    "chatbot_id": self.chatbot_id,
                    "total_chunks": len(chunks),
                    "created_at": datetime.utcnow().isoformat(),
                    "chunks": chunks
                }, indent=2, ensure_ascii=False))
            
            logger.info(f"Saved chunks index to {index_file}")
            
        except Exception as e:
            logger.error(f"Error saving chunks index: {e}")
    
    async def load_chunks(self) -> List[Dict]:
        """Load previously processed chunks from storage."""
        try:
            index_file = self.processed_dir / "chunks_index.json"
            
            if not index_file.exists():
                logger.warning(f"Chunks index not found: {index_file}")
                return []
            
            async with aiofiles.open(index_file, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
            
            return data.get("chunks", [])
            
        except Exception as e:
            logger.error(f"Error loading chunks: {e}")
            return []
    
    def _count_tokens(self, text: str) -> int:
        """Count approximate number of tokens in text."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Error counting tokens: {e}")
        
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4
    
    @staticmethod
    def _generate_chunk_id(url: str, chunk_idx: int) -> str:
        """Generate unique chunk ID."""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"chunk_{url_hash}_{chunk_idx:04d}"
    
    async def get_processing_stats(self) -> Dict:
        """Return statistics about the processed data."""
        chunks = await self.load_chunks()
        
        if not chunks:
            return {
                "chatbot_id": self.chatbot_id,
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "total_characters": 0,
                "total_tokens": 0,
                "avg_token_count": 0,
                "chunk_size_config": settings.CHUNK_SIZE,
                "chunk_overlap_config": settings.CHUNK_OVERLAP
            }
        
        total_size = sum(c.get("content_length", 0) for c in chunks)
        total_tokens = sum(c.get("token_count", 0) for c in chunks)
        
        return {
            "chatbot_id": self.chatbot_id,
            "total_chunks": len(chunks),
            "avg_chunk_size": total_size // len(chunks),
            "total_characters": total_size,
            "total_tokens": total_tokens,
            "avg_token_count": total_tokens // len(chunks),
            "chunk_size_config": settings.CHUNK_SIZE,
            "chunk_overlap_config": settings.CHUNK_OVERLAP
        }


async def main():
    """
    Example usage: process raw documents.
    
    Run with: python -m api.processor
    """
    import asyncio
    
    processor = ChunkProcessor(chatbot_id="test_chatbot_001")
    
    # Process raw documents
    chunks = await processor.process_raw_documents()
    
    # Get statistics
    stats = await processor.get_processing_stats()
    
    print(f"\nProcessing Statistics:")
    import json
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
