"""
scraper.py – Web crawler & text extractor.

Given a root URL this module:
  1. Fetches every page reachable from that URL on the same domain.
  2. Strips HTML markup, navigation, scripts and ads, keeping only
     readable body text.
  3. Returns a list of {url, text} dicts that the ingestion pipeline
     can process further.

Usage
-----
    from scraper import scrape_website

    pages = scrape_website("https://example.com", max_pages=50)
    for page in pages:
        print(page["url"], "–", len(page["text"]), "chars")
"""

import logging
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tags whose content we always discard (navigation noise, code, etc.)
_STRIP_TAGS = {
    "script", "style", "noscript", "header", "footer",
    "nav", "aside", "form", "button", "svg", "iframe",
}

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; RAG-Scraper/1.0; "
        "+https://github.com/Vaibhav-Dhaduk12/CHAT-BOT)"
    )
}


def _same_domain(base_url: str, target_url: str) -> bool:
    """Return True when *target_url* lives on the same host as *base_url*."""
    base_netloc = urlparse(base_url).netloc
    target_netloc = urlparse(target_url).netloc
    return target_netloc == base_netloc or target_netloc == ""


def _extract_text(html: str) -> str:
    """Parse *html* and return clean, whitespace-normalised plain text."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _collect_links(html: str, base_url: str) -> list[str]:
    """Return all same-domain <a href> links found in *html*."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        # Ignore anchors, mailto, tel, javascript links
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        full_url = urljoin(base_url, href)
        # Drop query-strings and fragments to avoid duplicate crawls
        parsed = urlparse(full_url)
        clean = parsed._replace(fragment="", query="").geturl()
        if _same_domain(base_url, clean):
            links.append(clean)
    return links


def scrape_website(
    root_url: str,
    max_pages: int = 50,
    timeout: int = 10,
) -> list[dict]:
    """
    Breadth-first crawl starting at *root_url*.

    Parameters
    ----------
    root_url:
        The starting URL (e.g. ``"https://example.com"``).
    max_pages:
        Maximum number of pages to visit (guards against huge sites).
    timeout:
        HTTP request timeout in seconds.

    Returns
    -------
    list of ``{"url": str, "text": str}`` dicts, one per crawled page.
    """
    visited: set[str] = set()
    queue: deque[str] = deque([root_url])
    pages: list[dict] = []

    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)
            continue

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            logger.debug("Skipping non-HTML page: %s", url)
            continue

        html = response.text
        text = _extract_text(html)

        if text:
            pages.append({"url": url, "text": text})
            logger.info("Scraped %s (%d chars)", url, len(text))

        for link in _collect_links(html, url):
            if link not in visited:
                queue.append(link)

    logger.info("Crawl finished – %d pages collected.", len(pages))
    return pages
