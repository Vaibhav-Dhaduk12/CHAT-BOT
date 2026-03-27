"""
Embeddings Manager for converting text to embeddings and storing in vector database.

Features:
- Provider abstraction: HuggingFace (free), OpenAI (paid), Google (paid)
- Vector database abstraction: FAISS (local), Pinecone (cloud)
- Batch processing for efficiency
- Namespace/collection support for multi-tenancy
"""

import json
import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import os
import pickle

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import openai
except ImportError:
    openai = None

try:
    from google import genai
except ImportError:
    genai = None

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts and return vectors."""
        pass
    
    @abstractmethod
    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text and return vector."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace sentence-transformers embedding provider (free, local)."""
    
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        
        logger.info(f"Loading HuggingFace model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts using batch encoding."""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                convert_to_numpy=False,
                show_progress_bar=False
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            raise
    
    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text."""
        embedding = self.model.encode([text], convert_to_numpy=False)
        return embedding[0].tolist()
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider (paid, cloud)."""
    
    def __init__(self, api_key: str = settings.OPENAI_API_KEY):
        if openai is None:
            raise ImportError("openai not installed. Run: pip install openai")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not provided")
        
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.model = settings.OPENAI_EMBEDDING_MODEL
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            # Sort by index to maintain order
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in embeddings]
            
        except Exception as e:
            logger.error(f"Error embedding batch via OpenAI: {e}")
            raise
    
    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text via OpenAI."""
        embeddings = await self.embed([text])
        return embeddings[0]
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return settings.OPENAI_EMBEDDING_DIMENSION


class GoogleGeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini embedding provider (paid, cloud)."""
    
    def __init__(self, api_key: str = settings.GEMINI_API_KEY):
        if genai is None:
            raise ImportError("google-genai not installed. Run: pip install google-genai")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not provided")
        
        self.client = genai.Client(api_key=api_key)
        self.model = settings.GEMINI_EMBEDDING_MODEL
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts using Google Gemini API."""
        try:
            embeddings = []
            for text in texts:
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                )

                values = None
                if hasattr(result, "embeddings") and result.embeddings:
                    first_embedding = result.embeddings[0]
                    values = getattr(first_embedding, "values", None)
                elif hasattr(result, "embedding"):
                    values = getattr(result.embedding, "values", None)

                if not values:
                    raise ValueError("No embedding values returned from Gemini API")

                embeddings.append(list(values))
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding batch via Google Gemini: {e}")
            raise
    
    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text via Google Gemini."""
        embeddings = await self.embed([text])
        return embeddings[0]
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return settings.GEMINI_EMBEDDING_DIMENSION


class VectorDatabase(ABC):
    """Abstract base class for vector databases."""
    
    @abstractmethod
    async def upsert(self, vectors: List[Dict], namespace: str = None) -> bool:
        """Store vectors in database."""
        pass
    
    @abstractmethod
    async def query(
        self,
        query_vector: List[float],
        top_k: int = 4,
        namespace: str = None
    ) -> List[Dict]:
        """Query similar vectors."""
        pass
    
    @abstractmethod
    async def delete_namespace(self, namespace: str) -> bool:
        """Delete all vectors in a namespace."""
        pass


class FAISSVectorDatabase(VectorDatabase):
    """FAISS vector database (local, free, pure Python)."""
    
    def __init__(self, embedding_dimension: int, db_path: str = settings.CHROMADB_PATH):
        if faiss is None:
            raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")
        
        self.db_path = db_path
        self.embedding_dimension = embedding_dimension
        self.namespaces = {}  # {namespace: {"index": faiss_index, "metadata": [...]}}
        
        os.makedirs(db_path, exist_ok=True)
        logger.info(f"Initializing FAISS at {db_path}")
        
        self._load_all_namespaces()
    
    def _get_namespace_path(self, namespace: str) -> str:
        """Get file path for a namespace."""
        return os.path.join(self.db_path, f"{namespace}.pkl")
    
    def _load_all_namespaces(self):
        """Load all existing namespace indices from disk."""
        for filename in os.listdir(self.db_path):
            if filename.endswith(".pkl"):
                namespace = filename[:-4]
                try:
                    with open(os.path.join(self.db_path, filename), "rb") as f:
                        self.namespaces[namespace] = pickle.load(f)
                    logger.debug(f"Loaded namespace: {namespace}")
                except Exception as e:
                    logger.warning(f"Failed to load namespace {namespace}: {e}")
    
    def _save_namespace(self, namespace: str):
        """Save namespace index to disk."""
        path = self._get_namespace_path(namespace)
        with open(path, "wb") as f:
            pickle.dump(self.namespaces[namespace], f)
        logger.debug(f"Saved namespace: {namespace}")
    
    async def upsert(self, vectors: List[Dict], namespace: str = None) -> bool:
        """Store vectors in FAISS."""
        try:
            namespace = namespace or settings.CHROMADB_COLLECTION_NAME
            
            # Initialize namespace if needed
            if namespace not in self.namespaces:
                index = faiss.IndexFlatL2(self.embedding_dimension)
                self.namespaces[namespace] = {
                    "index": index,
                    "metadata": [],
                    "id_map": {}  # maps FAISS index to document ID
                }
            
            ns_data = self.namespaces[namespace]
            index = ns_data["index"]
            
            # Prepare embeddings
            import numpy as np
            embeddings_array = np.array(
                [v["embedding"] for v in vectors],
                dtype=np.float32
            )
            
            # Add to index
            starting_idx = index.ntotal
            index.add(embeddings_array)
            
            # Store metadata and ID mapping
            for i, vector_data in enumerate(vectors):
                idx = starting_idx + i
                ns_data["id_map"][vector_data["id"]] = idx
                ns_data["metadata"].append({
                    "id": vector_data["id"],
                    "text": vector_data.get("text", ""),
                    "metadata": vector_data.get("metadata", {})
                })
            
            # Save to disk
            self._save_namespace(namespace)
            logger.debug(f"Upserted {len(vectors)} vectors to namespace={namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting to FAISS: {e}")
            return False
    
    async def query(
        self,
        query_vector: List[float],
        top_k: int = 4,
        namespace: str = None
    ) -> List[Dict]:
        """Query FAISS for similar vectors."""
        try:
            namespace = namespace or settings.CHROMADB_COLLECTION_NAME
            
            if namespace not in self.namespaces:
                logger.warning(f"Namespace {namespace} not found")
                return []
            
            import numpy as np
            ns_data = self.namespaces[namespace]
            index = ns_data["index"]
            
            # Convert query to numpy array
            query_array = np.array([query_vector], dtype=np.float32)
            
            # Search
            distances, indices = index.search(query_array, min(top_k, index.ntotal))
            
            # Transform to standard format
            output = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0:  # Valid result
                    metadata = ns_data["metadata"][idx]
                    output.append({
                        "id": metadata["id"],
                        "distance": float(distances[0][i]),
                        "text": metadata["text"],
                        "metadata": metadata.get("metadata", {})
                    })
            
            return output
            
        except Exception as e:
            logger.error(f"Error querying FAISS: {e}")
            return []
    
    async def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace in FAISS."""
        try:
            if namespace in self.namespaces:
                del self.namespaces[namespace]
                path = self._get_namespace_path(namespace)
                if os.path.exists(path):
                    os.remove(path)
                logger.info(f"Deleted namespace: {namespace}")
            return True
        except Exception as e:
            logger.error(f"Error deleting namespace: {e}")
            return False


class EmbeddingManager:
    """Manages embedding generation and vector database operations."""
    
    def __init__(
        self,
        embedding_provider: str = settings.EMBEDDING_PROVIDER,
        vector_db_provider: str = "faiss"  # Now defaults to FAISS
    ):
        self.embedding_provider_name = embedding_provider
        self.vector_db_provider_name = vector_db_provider
        
        # Initialize embedding provider
        if embedding_provider == "huggingface":
            self.embedder = HuggingFaceEmbeddingProvider()
        elif embedding_provider == "openai":
            self.embedder = OpenAIEmbeddingProvider()
        elif embedding_provider == "google":
            self.embedder = GoogleGeminiEmbeddingProvider()
        else:
            raise ValueError(f"Unknown embedding provider: {embedding_provider}")
        
        # Initialize vector database with embedding dimension
        if vector_db_provider == "faiss":
            self.vector_db = FAISSVectorDatabase(
                embedding_dimension=self.embedder.dimension
            )
        else:
            raise ValueError(f"Unknown vector DB provider: {vector_db_provider}")
        
        logger.info(
            f"EmbeddingManager initialized with "
            f"embedder={embedding_provider}, "
            f"vector_db={vector_db_provider}, "
            f"embedding_dim={self.embedder.dimension}"
        )
    
    async def embed_and_store(
        self,
        chunks: List[Dict],
        namespace: str
    ) -> bool:
        """
        Embed chunks and store in vector database.
        
        Args:
            chunks: List of chunk dictionaries (must contain 'id' and 'text')
            namespace: Collection/namespace name in vector DB
        
        Returns:
            True if successful
        """
        if not chunks:
            logger.warning("No chunks to embed")
            return False
        
        logger.info(f"Embedding {len(chunks)} chunks for namespace={namespace}")
        
        try:
            # Extract texts
            texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = await self.embedder.embed(texts)
            
            # Prepare data for storage
            vectors_to_store = []
            for chunk, embedding in zip(chunks, embeddings):
                vectors_to_store.append({
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "embedding": embedding,
                    "metadata": {
                        "source_url": chunk.get("source_url", ""),
                        "page_title": chunk.get("page_title", ""),
                        "chunk_index": chunk.get("chunk_index", 0),
                        "page_type": chunk.get("metadata", {}).get("page_type", "")
                    }
                })
            
            # Store in vector database
            success = await self.vector_db.upsert(vectors_to_store, namespace=namespace)
            
            if success:
                logger.info(f"Successfully embedded and stored {len(chunks)} chunks")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in embed_and_store: {e}")
            return False
    
    async def query(
        self,
        query_text: str,
        namespace: str,
        top_k: int = settings.RAG_TOP_K_CHUNKS
    ) -> List[Dict]:
        """
        Query embedding and retrieve similar chunks.
        """
        try:
            # Embed query
            query_embedding = await self.embedder.embed_single(query_text)
            
            # Search vector database
            results = await self.vector_db.query(
                query_vector=query_embedding,
                top_k=top_k,
                namespace=namespace
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying: {e}")
            return []
    
    async def delete_embeddings(self, namespace: str) -> bool:
        """Delete all embeddings for a namespace."""
        return await self.vector_db.delete_namespace(namespace)


async def main():
    """
    Example usage: embed chunks and store them.
    
    Run with: python -m api.embeddings
    """
    # Initialize manager (FAISS is now default)
    manager = EmbeddingManager(
        embedding_provider="huggingface",
        vector_db_provider="faiss"
    )
    
    # Sample chunks
    sample_chunks = [
        {
            "id": "chunk_001",
            "text": "The product features include real-time collaboration and automatic backups.",
            "source_url": "https://example.com/features",
            "page_title": "Features",
            "chunk_index": 0,
            "metadata": {"page_type": "product"}
        },
        {
            "id": "chunk_002",
            "text": "Pricing starts at $9.99 per month for the basic plan.",
            "source_url": "https://example.com/pricing",
            "page_title": "Pricing",
            "chunk_index": 0,
            "metadata": {"page_type": "pricing"}
        }
    ]
    
    # Embed and store
    success = await manager.embed_and_store(
        chunks=sample_chunks,
        namespace="test_chatbot"
    )
    
    if success:
        # Query
        results = await manager.query(
            query_text="What are the pricing options?",
            namespace="test_chatbot"
        )
        
        print("Query Results:")
        for result in results:
            print(f"  ID: {result['id']}")
            print(f"  Text: {result['text'][:100]}...")
            print(f"  Distance: {result.get('distance', 'N/A')}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
