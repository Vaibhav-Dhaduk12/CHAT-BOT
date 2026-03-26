"""
Unit tests for Phase 1 components.
Run with: pytest tests/
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

from api.processor import ChunkProcessor
from api.embeddings import (
    HuggingFaceEmbeddingProvider,
    EmbeddingManager
)
from config import settings


class TestChunkProcessor:
    """Test text chunking and processing."""
    
    @pytest.fixture
    def processor(self):
        return ChunkProcessor(chatbot_id="test_001")
    
    def test_chunk_id_generation(self):
        """Test unique chunk ID generation."""
        id1 = ChunkProcessor._generate_chunk_id(
            "https://example.com/page1", 0
        )
        id2 = ChunkProcessor._generate_chunk_id(
            "https://example.com/page2", 0
        )
        
        assert id1 != id2
        assert id1.startswith("chunk_")
    
    def test_token_counting(self, processor):
        """Test token counting."""
        text = "This is a test message."
        count = processor._count_tokens(text)
        
        assert count > 0
        assert isinstance(count, int)


class TestEmbeddings:
    """Test embedding generation."""
    
    @pytest.mark.asyncio
    async def test_huggingface_embedding_dimension(self):
        """Test HuggingFace embedding output dimension."""
        embedder = HuggingFaceEmbeddingProvider()
        
        text = "This is a test sentence."
        embedding = await embedder.embed_single(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedder.dimension
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_embedding_manager_initialization(self):
        """Test EmbeddingManager creation."""
        manager = EmbeddingManager(
            embedding_provider="huggingface",
            vector_db_provider="faiss"
        )
        
        assert manager.embedder is not None
        assert manager.vector_db is not None
    
    @pytest.mark.asyncio
    async def test_batch_embedding(self):
        """Test batch embedding of multiple texts."""
        embedder = HuggingFaceEmbeddingProvider()
        
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        
        embeddings = await embedder.embed(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == embedder.dimension for emb in embeddings)


class TestConfiguration:
    """Test configuration loading."""
    
    def test_settings_loaded(self):
        """Test that settings are loaded correctly."""
        assert settings.APP_NAME == "Universal Chatbot Backend"
        assert settings.API_PORT == 8000
        assert settings.CHUNK_SIZE == 500
    
    def test_embedding_provider_valid(self):
        """Test that embedding provider is valid."""
        valid_providers = ["huggingface", "openai", "google"]
        assert settings.EMBEDDING_PROVIDER in valid_providers


@pytest.mark.asyncio
async def test_full_embedding_pipeline():
    """Test complete embedding and storage pipeline."""
    
    # Sample chunks
    sample_chunks = [
        {
            "id": "test_chunk_001",
            "text": "The product offers real-time collaboration features.",
            "source_url": "https://example.com/features",
            "page_title": "Features",
            "chunk_index": 0,
            "metadata": {"page_type": "product"}
        }
    ]
    
    # Initialize manager
    manager = EmbeddingManager(
        embedding_provider="huggingface",
        vector_db_provider="faiss"
    )
    
    # Embed and store
    success = await manager.embed_and_store(
        chunks=sample_chunks,
        namespace="test_namespace"
    )
    
    assert success is True
    
    # Query
    results = await manager.query(
        query_text="collaboration features",
        namespace="test_namespace",
        top_k=1
    )
    
    assert len(results) > 0
    assert results[0]["id"] == "test_chunk_001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
