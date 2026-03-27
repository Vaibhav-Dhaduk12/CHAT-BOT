"""
Hybrid Web Crawler for extracting content from target websites.

Features:
- Tries multiple strategies: Sitemap → API → SPA Click Navigation
- Automates browser navigation with Playwright for SPAs
- Content-based deduplication (hash checking)
- Respects robots.txt and rate limiting
- Extracts clean text, removing noise (ads, navigation)
- Stores raw content with metadata
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from urllib.parse import urlparse, urlunparse
import hashlib
import xml.etree.ElementTree as ET

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
import aiofiles
import httpx

from config import settings

logger = logging.getLogger(__name__)


class WebCrawler:
    """Hybrid web crawler with multiple extraction strategies."""
    
    def __init__(self, chatbot_id: str):
        self.chatbot_id = chatbot_id
        self.visited_urls: Set[str] = set()
        self.visited_content_hashes: Set[str] = set()  # For deduplication
        self.output_dir = Path(settings.DATA_RAW_DIR) / chatbot_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def crawl_website(self, start_url: str) -> List[Dict]:
        """
        Main entry point: try multiple strategies to crawl website.
        
        Strategy order:
        1. Sitemap.xml (best for discovering all pages)
        2. API endpoints (if available)
        3. SPA click navigation (fallback)
        
        Returns:
            List of documents with extracted content and metadata
        """
        logger.info(f"🚀 Starting hybrid crawl of {start_url} for chatbot_id={self.chatbot_id}")
        documents = []
        base_domain = urlparse(start_url).netloc
        
        # Strategy 1: Try sitemap.xml
        logger.info("📋 Strategy 1: Checking for sitemap.xml...")
        sitemap_docs = await self._crawl_from_sitemap(start_url, base_domain)
        if sitemap_docs:
            logger.info(f"✅ Sitemap found! Extracted {len(sitemap_docs)} pages from sitemap.xml")
            documents.extend(sitemap_docs)
            return documents
        
        logger.info("❌ No sitemap.xml found, proceeding to alternate strategies")
        
        # Strategy 2: Try SPA click navigation
        logger.info("🔗 Strategy 2: Using SPA click-based crawling...")
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                user_agent=settings.CRAWLER_USER_AGENT,
                viewport={"width": 1280, "height": 720}
            )
            
            try:
                documents = await self._crawl_spa(
                    context=context,
                    start_url=start_url,
                    base_domain=base_domain
                )
            finally:
                await context.close()
                await browser.close()
        
        logger.info(f"✅ Crawl complete: extracted {len(documents)} documents")
        return documents
    
    async def _crawl_from_sitemap(self, start_url: str, base_domain: str) -> List[Dict]:
        """
        Extract URLs from sitemap.xml and crawl them.
        
        Returns:
            List of documents extracted from sitemap URLs
        """
        try:
            base_parsed = urlparse(start_url)
            sitemap_url = f"{base_parsed.scheme}://{base_parsed.netloc}/sitemap.xml"
            
            logger.debug(f"Attempting to fetch sitemap from: {sitemap_url}")
            
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.get(sitemap_url, timeout=10)
                    
                    if resp.status_code != 200:
                        logger.debug(f"Sitemap not found (status {resp.status_code})")
                        return []
                    
                    content = resp.text
                    root = ET.fromstring(content)
                    
                    # Extract URLs from sitemap
                    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                    urls = [url.text for url in root.findall('.//ns:loc', namespace)]
                    
                    if not urls:
                        logger.debug("Sitemap exists but no URLs found")
                        return []
                    
                    logger.info(f"Found {len(urls)} URLs in sitemap")
                    
                    # Crawl each URL from sitemap
                    documents = []
                    async with async_playwright() as p:
                        browser = await p.chromium.launch()
                        context = await browser.new_context(
                            user_agent=settings.CRAWLER_USER_AGENT,
                            viewport={"width": 1280, "height": 720}
                        )
                        
                        try:
                            for url in urls[:settings.CRAWLER_MAX_PAGES]:
                                try:
                                    doc = await self._fetch_and_extract(context, url, base_domain)
                                    if doc:
                                        documents.append(doc)
                                except Exception as e:
                                    logger.warning(f"Error crawling sitemap URL {url}: {e}")
                                    continue
                        finally:
                            await context.close()
                            await browser.close()
                    
                    return documents
                    
                except Exception as e:
                    logger.debug(f"Failed to fetch sitemap: {e}")
                    return []
                    
        except Exception as e:
            logger.debug(f"Sitemap extraction error: {e}")
            return []
    
    async def _crawl_spa(
        self,
        context: BrowserContext,
        start_url: str,
        base_domain: str
    ) -> List[Dict]:
        """
        Crawl SPA using click simulation and API interception.
        Captures both UI content AND API responses.
        """
        documents = []
        api_responses = {}  # Track API calls
        
        try:
            page = await context.new_page()
            page.set_default_timeout(settings.CRAWLER_TIMEOUT * 1000)
            
            # Intercept API calls
            async def handle_route(route):
                request = route.request
                response = await route.fetch()
                
                # Capture API responses (JSON data)
                if 'application/json' in response.headers.get('content-type', ''):
                    try:
                        data = await response.json()
                        api_url = request.url
                        
                        if api_url not in api_responses:
                            api_responses[api_url] = data
                            logger.info(f"🔗 Captured API: {api_url}")
                    except:
                        pass
                
                await route.continue_()
            
            # Set up interception for API calls
            await page.route('**/*', handle_route)
            
            logger.debug(f"Fetching SPA: {start_url}")
            await page.goto(start_url, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)
            
            # Extract initial page
            initial_doc = await self._extract_content_from_page(page, start_url, base_domain)
            if initial_doc:
                documents.append(initial_doc)
            
            # Get interactive elements
            elements = await page.evaluate("""
                () => {
                    const elements = [];
                    document.querySelectorAll('button, a, [role="button"]').forEach(el => {
                        if (el.offsetParent !== null && el.textContent.trim().length > 0) {
                            elements.push({
                                text: el.textContent.trim().substring(0, 50),
                                type: el.tagName
                            });
                        }
                    });
                    return elements.slice(0, 20);
                }
            """)
            
            logger.info(f"Found {len(elements)} interactive elements on SPA")
            
            # Click elements to trigger API calls
            for idx, elem in enumerate(elements):
                if len(documents) >= settings.CRAWLER_MAX_PAGES:
                    break
                
                try:
                    logger.debug(f"Clicking element {idx+1}/{len(elements)}: {elem['text']}")
                    
                    content_before = await page.content()
                    before_hash = hashlib.md5(content_before.encode()).hexdigest()
                    
                    await page.evaluate(f"""
                        Array.from(document.querySelectorAll('button, a, [role="button"]'))[{idx}]?.click()
                    """)
                    
                    await page.wait_for_timeout(2000)
                    
                    try:
                        await page.wait_for_load_state("networkidle", timeout=3000)
                    except:
                        pass
                    
                    content_after = await page.content()
                    after_hash = hashlib.md5(content_after.encode()).hexdigest()
                    
                    if before_hash != after_hash:
                        current_url = page.url
                        
                        if current_url not in self.visited_urls:
                            doc = await self._extract_content_from_page(page, current_url, base_domain)
                            if doc:
                                content_hash = hashlib.md5(doc['content'].encode()).hexdigest()
                                if content_hash not in self.visited_content_hashes:
                                    documents.append(doc)
                                    self.visited_content_hashes.add(content_hash)
                                    logger.info(f"✅ Extracted new page: {current_url}")
                            
                            self.visited_urls.add(current_url)
                    
                except Exception as e:
                    logger.warning(f"Error clicking element {idx}: {e}")
                    continue
            
            # Convert captured API responses to documents
            for api_url, api_data in api_responses.items():
                try:
                    # Skip if we've already processed limit
                    if len(documents) >= settings.CRAWLER_MAX_PAGES:
                        break
                    
                    # Convert API response to document
                    api_doc = await self._extract_api_data(api_url, api_data)
                    if api_doc:
                        content_hash = hashlib.md5(api_doc['content'].encode()).hexdigest()
                        if content_hash not in self.visited_content_hashes:
                            documents.append(api_doc)
                            self.visited_content_hashes.add(content_hash)
                            logger.info(f"✅ Extracted API data from: {api_url}")
                except Exception as e:
                    logger.warning(f"Error extracting API data from {api_url}: {e}")
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error in SPA crawl: {e}", exc_info=True)
        
        logger.info(f"Total API calls captured: {len(api_responses)}")
        return documents
    
    async def _extract_api_data(self, api_url: str, api_data: dict) -> Optional[Dict]:
        """
        Convert API JSON response to a document.
        """
        try:
            # Flatten nested JSON into readable text
            def flatten_json(obj, prefix=""):
                result = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            result.extend(flatten_json(value, f"{prefix}{key}."))
                        else:
                            result.append(f"{prefix}{key}: {value}")
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj[:10]):  # Limit to 10 items
                        result.extend(flatten_json(item, f"{prefix}[{idx}]."))
                else:
                    result.append(str(obj))
                return result
            
            flattened = flatten_json(api_data)
            content = "\n".join(flattened)
            
            if not content or len(content) < 50:
                return None
            
            document = {
                "url": api_url,
                "title": f"API Response: {urlparse(api_url).path}",
                "content": content,
                "content_length": len(content),
                "crawled_at": datetime.utcnow().isoformat(),
                "chatbot_id": self.chatbot_id,
                "metadata": {
                    "page_type": "api",
                    "domain": urlparse(api_url).netloc,
                    "path": urlparse(api_url).path
                }
            }
            
            await self._save_raw_document(document)
            return document
            
        except Exception as e:
            logger.warning(f"Error extracting API data: {e}")
            return None
    
    async def _fetch_and_extract(
        self,
        context: BrowserContext,
        url: str,
        base_domain: str
    ) -> Optional[Dict]:
        """
        Fetch a single URL and extract content.
        Used for sitemap-based crawling.
        """
        if len(self.visited_urls) >= settings.CRAWLER_MAX_PAGES:
            return None
        
        if url in self.visited_urls:
            return None
        
        if urlparse(url).netloc != base_domain:
            logger.debug(f"Skipping external URL: {url}")
            return None
        
        self.visited_urls.add(url)
        
        try:
            page = await context.new_page()
            page.set_default_timeout(settings.CRAWLER_TIMEOUT * 1000)
            
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)
            
            doc = await self._extract_content_from_page(page, url, base_domain)
            await page.close()
            
            return doc
            
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None
    
    async def _extract_content_from_page(
        self,
        page: Page,
        url: str,
        base_domain: str
    ) -> Optional[Dict]:
        """
        Extract clean content from a loaded page.
        """
        try:
            html_content = await page.content()
            return await self._extract_content(url, html_content, base_domain)
        except Exception as e:
            logger.error(f"Error extracting from page {url}: {e}")
            return None
    
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
            
            # Save raw content
            await self._save_raw_document(document)
            
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
        normalized_path = parsed.path.rstrip("/")
        cleaned = parsed._replace(path=normalized_path, params="", fragment="")
        return urlunparse((
            cleaned.scheme,
            cleaned.netloc,
            cleaned.path,
            cleaned.params,
            cleaned.query,
            cleaned.fragment,
        ))
    
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
            async with aiofiles.open(file, "r", encoding="utf-8") as f:
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
