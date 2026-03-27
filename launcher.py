#!/usr/bin/env python3
"""
🚀 Universal AI Chatbot Launcher
================================

Single command to:
1. Initialize the RAG pipeline (if needed)
2. Start the FastAPI server
3. Open the chatbot UI in your browser

Usage:
    python launcher.py                          # Start with existing data
    python launcher.py --init                   # Initialize with demo data first
    python launcher.py --url "https://..."     # Crawl specific website first
    python launcher.py --help                   # Show all options
"""

import asyncio
import subprocess
import sys
import webbrowser
import argparse
import logging
import time
import os
from pathlib import Path
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project modules
try:
    from config import settings
    from scripts.crawler import WebCrawler
    from api.processor import ChunkProcessor
    from api.embeddings import EmbeddingManager
except ImportError as e:
    logger.error(f"❌ Failed to import modules: {e}")
    sys.exit(1)


class ChatbotLauncher:
    """Launcher for the complete chatbot system."""
    
    def __init__(self):
        self.chatbot_id = "demo_bot"
        self.url = "https://docs.python.org/3/library/functions.html"
        
    def print_banner(self):
        """Print startup banner."""
        print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║         🤖 Phoenix Insurance AI Chatbot - Unified Launcher        ║
║                                                                    ║
║  Frontend + Server + Knowledge Engine - All in One                 ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
        """)
    
    def check_data_exists(self, chatbot_id: str = "demo_bot") -> bool:
        """Check if embeddings already exist for this chatbot."""
        processed_dir = Path(settings.DATA_PROCESSED_DIR) / chatbot_id
        chunks_file = processed_dir / "chunks_index.json"
        
        if chunks_file.exists():
            logger.info(f"✓ Found existing data for '{chatbot_id}'")
            return True
        return False
    
    async def initialize_rag_pipeline(self, url: str, chatbot_id: str, max_depth: int = 2, max_pages: int = 20):
        """Run the complete RAG pipeline."""
        logger.info(f"\n📚 Initializing RAG Pipeline...")
        logger.info(f"   Website: {url}")
        logger.info(f"   Chatbot ID: {chatbot_id}")
        logger.info(f"   Max Depth: {max_depth}, Max Pages: {max_pages}\n")
        
        try:
            # Step 1: Crawl
            logger.info("🔗 STEP 1: Crawling website...")
            # Apply runtime crawl limits from CLI options.
            settings.CRAWLER_MAX_DEPTH = max_depth
            settings.CRAWLER_MAX_PAGES = max_pages

            crawler = WebCrawler(chatbot_id=chatbot_id)
            crawled_data = await crawler.crawl_website(url)
            logger.info(f"✓ Crawled {len(crawled_data)} pages")
            
            # Step 2: Process
            logger.info("\n✂️  STEP 2: Processing documents...")
            processor = ChunkProcessor(chatbot_id=chatbot_id)
            chunks = await processor.process_raw_documents()
            logger.info(f"✓ Created {len(chunks)} chunks")
            
            # Step 3: Embed
            logger.info("\n🔤 STEP 3: Generating embeddings...")
            embedding_manager = EmbeddingManager(
                embedding_provider=settings.EMBEDDING_PROVIDER,
                vector_db_provider="faiss"
            )
            success = await embedding_manager.embed_and_store(chunks, namespace=chatbot_id)
            
            if success:
                logger.info(f"✓ Embeddings stored successfully")
            else:
                logger.warning("⚠️  Issue with embedding storage")
            
            logger.info(f"\n✅ RAG Pipeline Complete!\n")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return False
    
    def start_server(self):
        """Start the FastAPI server in a subprocess."""
        logger.info("🚀 Starting FastAPI server...\n")
        
        # Run uvicorn server
        try:
            subprocess.run([
                sys.executable, "-m", "uvicorn",
                "api.main:app",
                "--host", settings.API_HOST,
                "--port", str(settings.API_PORT),
                "--reload"
            ])
        except KeyboardInterrupt:
            logger.info("\n✋ Server stopped")
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
    
    def open_browser(self, delay: int = 3):
        """Open chatbot UI in browser after delay."""
        def _open():
            time.sleep(delay)
            # Use localhost for browser navigation; 0.0.0.0 is a bind address.
            url = f"http://localhost:{settings.API_PORT}"
            logger.info(f"\n🌐 Opening browser at {url}...\n")
            webbrowser.open(url)
        
        thread = threading.Thread(target=_open, daemon=True)
        thread.start()
    
    async def run(self, args):
        """Main launcher logic."""
        self.print_banner()
        
        chatbot_id = args.chatbot_id or self.chatbot_id
        
        # Check if we need to initialize
        if args.init or args.url:
            # Run pipeline if --init flag or custom URL provided
            url = args.url or self.url
            max_depth = args.max_depth or 2
            max_pages = args.max_pages or 20
            
            success = await self.initialize_rag_pipeline(
                url=url,
                chatbot_id=chatbot_id,
                max_depth=max_depth,
                max_pages=max_pages
            )
            if not success:
                logger.warning("⚠️  Pipeline had issues, but continuing...")
        
        elif not self.check_data_exists(chatbot_id):
            logger.warning(f"\n⚠️  No existing data found for '{chatbot_id}'")
            response = input("Initialize with demo data? (y/n): ").strip().lower()
            if response == 'y':
                success = await self.initialize_rag_pipeline(
                    url=self.url,
                    chatbot_id=chatbot_id,
                    max_depth=1,
                    max_pages=5
                )
                if not success:
                    logger.warning("Pipeline failed, but continuing with server...")
            else:
                logger.info("Skipping initialization. Server will have no data.")
        
        # Start server with browser
        logger.info(f"""
╔════════════════════════════════════════════════════════════════════╗
║                   🎉 READY TO CHAT!                               ║
╚════════════════════════════════════════════════════════════════════╝

  🌐 Web Interface:  http://localhost:{settings.API_PORT}
  📖 API Docs:       http://localhost:{settings.API_PORT}/docs
  🔧 API Root:       http://localhost:{settings.API_PORT}/api/query

  Press Ctrl+C to stop the server
        """)
        
        # Open browser and start server
        self.open_browser(delay=2)
        self.start_server()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="🚀 Unified Chatbot Launcher - UI + Server + Knowledge Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launcher.py                              # Start with existing data
  python launcher.py --init                       # Initialize demo data first
  python launcher.py --url "https://example.com" --max-pages 50
  python launcher.py --chatbot-id "my_bot" --init
        """
    )
    
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize RAG pipeline with demo data"
    )
    
    parser.add_argument(
        "--url",
        type=str,
        help="Website URL to crawl (triggers initialization)"
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
        default=2,
        help="Max crawl depth (default: 2)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Max pages to crawl (default: 20)"
    )
    
    args = parser.parse_args()
    
    launcher = ChatbotLauncher()
    
    try:
        asyncio.run(launcher.run(args))
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
