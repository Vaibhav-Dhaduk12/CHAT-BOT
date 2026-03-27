#!/usr/bin/env python3
"""
Universal AI Chatbot - Full RAG Pipeline
==========================================

This script demonstrates the complete 4-step RAG pipeline:
1. CRAWL    - Scrape website content using Playwright
2. PROCESS  - Chunk documents semantically with LangChain
3. EMBED    - Generate embeddings and index with FAISS
4. QUERY    - Retrieve similar documents for RAG

Usage:
    python run_pipeline.py
    python run_pipeline.py --url "https://example.com" --chatbot-id "my_bot"
    python run_pipeline.py --max-depth 2 --max-pages 20
"""

import asyncio
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from scripts.crawler import WebCrawler
from api.processor import ChunkProcessor
from api.embeddings import EmbeddingManager
from config import settings


class RAGPipeline:
    """Complete RAG pipeline execution."""
    
    def __init__(
        self,
        chatbot_id: str = "demo_bot",
        url: str = "https://docs.python.org/3/library/functions.html",
        max_depth: int = 1,
        max_pages: int = 5,
        embedding_provider: str = "huggingface",
        vector_db: str = "faiss"
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            chatbot_id: Unique identifier for this chatbot instance
            url: Starting URL to crawl
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl per domain
            embedding_provider: Provider for embeddings (huggingface, openai)
            vector_db: Vector database provider (faiss, chromadb)
        """
        self.chatbot_id = chatbot_id
        self.url = url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.embedding_provider = embedding_provider
        self.vector_db = vector_db
        
        logger.info(f"🤖 Initializing RAG Pipeline: {chatbot_id}")
        logger.info(f"   URL: {url}")
        logger.info(f"   Max Depth: {max_depth}, Max Pages: {max_pages}")
        logger.info(f"   Embeddings: {embedding_provider}, Vector DB: {vector_db}")
    
    async def step_1_crawl(self) -> dict:
        """
        STEP 1: Crawl website and extract content.
        
        Returns:
            Statistics about crawled documents
        """
        print("\n" + "="*60)
        print("📡 STEP 1: CRAWLING WEBSITE")
        print("="*60)
        
        try:
            crawler = WebCrawler(chatbot_id=self.chatbot_id)
            
            logger.info(f"Starting crawl from: {self.url}")
            documents = await crawler.crawl_website(self.url)
            
            stats = await crawler.get_crawl_stats()
            
            print(f"\n✅ Crawling Complete!")
            print(f"   📄 Pages crawled: {stats['total_pages_crawled']}")
            print(f"   📊 Total characters: {stats['total_content_length_chars']:,}")
            print(f"   📁 Stored in: data/raw/{self.chatbot_id}/")
            
            return stats
            
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
            print(f"\n❌ Crawling failed: {e}")
            raise
    
    async def step_2_process(self) -> list:
        """
        STEP 2: Process documents and create semantic chunks.
        
        Returns:
            List of processed chunks
        """
        print("\n" + "="*60)
        print("📝 STEP 2: PROCESSING DOCUMENTS")
        print("="*60)
        
        try:
            processor = ChunkProcessor(chatbot_id=self.chatbot_id)
            
            logger.info("Starting document processing...")
            chunks = await processor.process_raw_documents()
            
            stats = await processor.get_processing_stats()
            
            print(f"\n✅ Processing Complete!")
            print(f"   ✂️  Chunks created: {stats['total_chunks']}")
            if stats['total_chunks'] > 0:
                print(f"   📊 Total characters: {stats['total_characters']:,}")
                print(f"   🔢 Total tokens: {stats['total_tokens']:,}")
            print(f"   📁 Stored in: data/processed/{self.chatbot_id}/chunks_index.json")
            
            # Show sample chunks
            if chunks:
                print(f"\n   Sample chunks:")
                for i, chunk in enumerate(chunks[:2], 1):
                    preview = chunk['text'][:80].replace('\n', ' ')
                    print(f"   {i}. {preview}...")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            print(f"\n❌ Processing failed: {e}")
            raise
    
    async def step_3_embed(self, chunks: list) -> bool:
        """
        STEP 3: Generate embeddings and store in vector database.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            Success status
        """
        print("\n" + "="*60)
        print("🧠 STEP 3: GENERATING EMBEDDINGS & INDEXING")
        print("="*60)
        
        try:
            if not chunks:
                logger.warning("No chunks to embed")
                print("\n⚠️  No chunks available to embed")
                return False
            
            logger.info(f"Initializing embedding manager: {self.embedding_provider}")
            manager = EmbeddingManager(
                embedding_provider=self.embedding_provider,
                vector_db_provider=self.vector_db
            )
            
            logger.info(f"Embedding {len(chunks)} chunks...")
            print(f"   Embedding {len(chunks)} chunks...")
            
            success = await manager.embed_and_store(
                chunks=chunks,
                namespace=self.chatbot_id
            )
            
            if success:
                print(f"\n✅ Embedding Complete!")
                print(f"   🔢 Chunks indexed: {len(chunks)}")
                print(f"   📦 Embedding dimension: {manager.embedder.dimension}")
                print(f"   💾 Stored in: data/vectors/{self.chatbot_id}.pkl")
                return True
            else:
                print(f"\n❌ Embedding failed")
                return False
                
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            print(f"\n❌ Embedding failed: {e}")
            raise
    
    async def step_4_query(self, sample_queries: list = None) -> list:
        """
        STEP 4: Query the vector database and retrieve similar documents.
        
        Args:
            sample_queries: List of queries to test (optional)
            
        Returns:
            List of query results
        """
        print("\n" + "="*60)
        print("🔍 STEP 4: QUERYING & RETRIEVAL")
        print("="*60)
        
        if not sample_queries:
            sample_queries = [
                "What are built-in functions?",
                "How do I use this component?",
                "Tell me about the main features"
            ]
        
        try:
            logger.info(f"Initializing query manager...")
            manager = EmbeddingManager(
                embedding_provider=self.embedding_provider,
                vector_db_provider=self.vector_db
            )
            
            all_results = []
            
            for query_idx, query_text in enumerate(sample_queries, 1):
                logger.info(f"Query {query_idx}: {query_text}")
                print(f"\n📌 Query {query_idx}: \"{query_text}\"")
                
                results = await manager.query(
                    query_text=query_text,
                    namespace=self.chatbot_id,
                    top_k=settings.RAG_TOP_K_CHUNKS
                )
                
                all_results.append({
                    "query": query_text,
                    "results": results
                })
                
                if results:
                    print(f"   ✅ Found {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        distance = result.get('distance', 0)
                        text_preview = result['text'][:90].replace('\n', ' ')
                        print(f"   {i}. {text_preview}...")
                        print(f"      📊 Distance: {distance:.4f}")
                else:
                    print(f"   ⚠️  No results found")
            
            print(f"\n✅ Query Complete!")
            print(f"   🔎 Queries executed: {len(sample_queries)}")
            
            return all_results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            print(f"\n❌ Query failed: {e}")
            raise
    
    async def run_full_pipeline(self):
        """
        Execute the complete RAG pipeline: Crawl → Process → Embed → Query
        """
        start_time = datetime.now()
        
        print("\n" + "🚀 "*20)
        print("UNIVERSAL AI CHATBOT - FULL RAG PIPELINE")
        print("🚀 "*20)
        
        try:
            # Step 1: Crawl
            crawl_stats = await self.step_1_crawl()
            
            # Step 2: Process
            chunks = await self.step_2_process()
            
            if not chunks:
                print("\n❌ No chunks generated, stopping pipeline")
                return
            
            # Step 3: Embed
            embed_success = await self.step_3_embed(chunks)
            
            if not embed_success:
                print("\n❌ Embedding failed, stopping pipeline")
                return
            
            # Step 4: Query
            query_results = await self.step_4_query()
            
            # Summary
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print("\n" + "="*60)
            print("📊 PIPELINE SUMMARY")
            print("="*60)
            print(f"✅ Pipeline Status: SUCCESS")
            print(f"⏱️  Total Time: {elapsed:.2f}s")
            print(f"📄 Pages Crawled: {crawl_stats['total_pages_crawled']}")
            print(f"✂️  Chunks Created: {len(chunks)}")
            print(f"🔎 Queries Executed: {len(query_results)}")
            print(f"📁 Chatbot ID: {self.chatbot_id}")
            print(f"📂 Data Location: data/{{raw,processed,vectors}}/{self.chatbot_id}/")
            print("="*60)
            
            print("\n✨ RAG Pipeline completed successfully!")
            print("\n💡 Next Steps:")
            print("   1. Review the generated chunks in: data/processed/")
            print("   2. Query results show document relevance (lower distance = more relevant)")
            print("   3. Integrate with FastAPI backend (Phase 2)")
            print("   4. Add LLM layer for actual chatbot responses")
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Pipeline failed after {elapsed:.2f}s: {e}")
            print(f"\n❌ Pipeline failed after {elapsed:.2f}s")
            print(f"   Error: {e}")
            raise


async def main():
    """Main entry point with CLI argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Run the complete Universal AI Chatbot RAG pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py
  python run_pipeline.py --url "https://docs.python.org" --chatbot-id "py_bot"
  python run_pipeline.py --max-pages 10 --max-depth 2
  python run_pipeline.py --embedding-provider huggingface --vector-db faiss
        """
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default="https://docs.python.org/3/library/functions.html",
        help="Starting URL to crawl (default: Python docs)"
    )
    
    parser.add_argument(
        "--chatbot-id",
        type=str,
        default="demo_bot",
        help="Unique identifier for this chatbot (default: demo_bot)"
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=1,
        help="Maximum crawl depth (default: 1)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum pages to crawl (default: 5)"
    )
    
    parser.add_argument(
        "--embedding-provider",
        type=str,
        default="huggingface",
        choices=["huggingface", "openai", "google"],
        help="Embedding provider (default: huggingface)"
    )
    
    parser.add_argument(
        "--vector-db",
        type=str,
        default="faiss",
        choices=["faiss"],
        help="Vector database (default: faiss)"
    )
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = RAGPipeline(
        chatbot_id=args.chatbot_id,
        url=args.url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        embedding_provider=args.embedding_provider,
        vector_db=args.vector_db
    )
    
    await pipeline.run_full_pipeline()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚙️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        raise
