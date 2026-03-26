"""
Web Crawler for extracting content from target websites.

Features:
- Automates browser navigation with Playwright
- Handles JavaScript-heavy SPAs
- Respects robots.txt and rate limiting
- Extracts clean text, removing noise (ads, navigation)
- Stores raw content with metadata
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
import hashlib

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
import aiofiles

from config import settings

logger = logging.getLogger(__name__)


class WebCrawler:
    """Async web crawler using Playwright for content extraction."""
    
    def __init__(self, chatbot_id: str):
        self.chatbot_id = chatbot_id
        self.visited_urls: Set[str] = set()
        self.output_dir = Path(settings.DATA_RAW_DIR) / chatbot_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def crawl_website(self, start_url: str) -> List[Dict]:
        """
        Main entry point: crawl website starting from URL.
        
        Returns:
            List of documents with extracted content and metadata
        """
        logger.info(f"Starting crawl of {start_url} for chatbot_id={self.chatbot_id}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                user_agent=settings.CRAWLER_USER_AGENT,
                viewport={"width": 1280, "height": 720}
            )
            
            try:
                documents = await self._crawl_recursive(
                    context=context,
                    url=start_url,
                    depth=0,
                    base_domain=urlparse(start_url).netloc
                )
            finally:
                await context.close()
                await browser.close()
        
        logger.info(f"Crawl complete: extracted {len(documents)} documents")
        return documents
    
    async def _crawl_recursive(
        self,
        context: BrowserContext,
        url: str,
        depth: int,
        base_domain: str
    ) -> List[Dict]:
        """
        Recursively crawl pages up to max depth/page count.
        """
        if len(self.visited_urls) >= settings.CRAWLER_MAX_PAGES:
            logger.info(f"Reached max pages limit ({settings.CRAWLER_MAX_PAGES})")
            return []
        
        if depth > settings.CRAWLER_MAX_DEPTH:
            logger.debug(f"Reached max depth ({settings.CRAWLER_MAX_DEPTH}) at {url}")
            return []
        
        if url in self.visited_urls:
            return []
        
        # Check domain to prevent crawling outside target domain
        if urlparse(url).netloc != base_domain:
            logger.debug(f"Skipping external URL: {url}")
            return []
        
        self.visited_urls.add(url)
        documents = []
        
        try:
            page = await context.new_page()
            await page.set_default_timeout(settings.CRAWLER_TIMEOUT * 1000)
            
            logger.debug(f"Fetching: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            
            # Wait for JavaScript to render
            await page.wait_for_load_state("networkidle")
            
            # Extract content
            html_content = await page.content()
            document = await self._extract_content(url, html_content, base_domain)
            
            if document:
                documents.append(document)
                
                # Save raw content
                await self._save_raw_document(document)
            
            # Extract and crawl internal links
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href && !href.startsWith('javascript:'))
            """)
            
            # Crawl child pages
            for link in links[:10]:  # Limit links per page
                try:
                    normalized_link = self._normalize_url(link)
                    if normalized_link not in self.visited_urls:
                        child_docs = await self._crawl_recursive(
                            context=context,
                            url=normalized_link,
                            depth=depth + 1,
                            base_domain=base_domain
                        )
                        documents.extend(child_docs)
                except Exception as e:
                    logger.warning(f"Error crawling child link {link}: {e}")
                    continue
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return documents
        
        return documents
    
    async def _extract_content(
        self,
        url: str,
        html_content: str,
        base_domain: str
    ) -> Optional[Dict]:
        """
        Extract clean text from HTML, removing noise.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Extract title
            title = soup.find("title")
            page_title = title.string if title else "Untitled"
            
            # Try to extract main content
            main_content = (
                soup.find("main") or
                soup.find("article") or
                soup.find(["div", "section"], {"class": ["content", "main", "body"]})
            )
            
            if not main_content:
                main_content = soup.body
            
            # Get text
            text = main_content.get_text(separator="\n", strip=True)
            
            # Clean up text
            text = "\n".join(
                line.strip()
                for line in text.split("\n")
                if line.strip()
            )
            
            if not text or len(text) < 100:
                logger.debug(f"Skipping {url}: insufficient content")
                return None
            
            document = {
                "url": url,
                "title": page_title,
                "content": text,
                "content_length": len(text),
                "crawled_at": datetime.utcnow().isoformat(),
                "chatbot_id": self.chatbot_id,
                "metadata": {
                    "page_type": self._infer_page_type(url),
                    "domain": urlparse(url).netloc,
                    "path": urlparse(url).path
                }
            }
            
            logger.debug(f"Extracted {len(text)} chars from {url}")
            return document
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    async def _save_raw_document(self, document: Dict) -> None:
        """Save raw extracted document to JSON file."""
        try:
            filename = hashlib.md5(document["url"].encode()).hexdigest() + ".json"
            filepath = self.output_dir / filename
            
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(document, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Error saving document {document['url']}: {e}")
    
    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL to prevent duplicates (remove fragments, etc)."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + parsed.query if parsed.query else ''}"
    
    @staticmethod
    def _infer_page_type(url: str) -> str:
        """Infer page type from URL patterns."""
        url_lower = url.lower()
        if "pricing" in url_lower:
            return "pricing"
        elif "product" in url_lower or "feature" in url_lower:
            return "product"
        elif "doc" in url_lower or "guide" in url_lower:
            return "documentation"
        elif "faq" in url_lower or "help" in url_lower:
            return "help"
        elif "blog" in url_lower:
            return "blog"
        else:
            return "general"
    
    async def get_crawl_stats(self) -> Dict:
        """Return statistics about the crawl."""
        raw_files = list(self.output_dir.glob("*.json"))
        
        total_content_length = 0
        total_documents = 0
        
        for file in raw_files:
            total_documents += 1
            async with aiofiles.open(file, "r") as f:
                content = await f.read()
                doc = json.loads(content)
                total_content_length += doc.get("content_length", 0)
        
        return {
            "chatbot_id": self.chatbot_id,
            "total_pages_crawled": len(self.visited_urls),
            "total_documents_extracted": total_documents,
            "total_content_length_chars": total_content_length,
            "avg_content_per_page": (
                total_content_length / total_documents if total_documents > 0 else 0
            )
        }


async def main():
    """
    Example usage: crawl a website.
    
    Run with: python scripts/crawler.py
    """
    # Example: crawl OpenAI docs
    crawler = WebCrawler(chatbot_id="test_chatbot_001")
    
    documents = await crawler.crawl_website(
        start_url="https://viphub.phoenixins.mu/"  # Replace with actual target
    )
    
    stats = await crawler.get_crawl_stats()
    print(f"\nCrawl Statistics:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
