"""
Broken Links Detection Service
Crawls the homepage and checks for broken links
"""
import httpx
import asyncio
from typing import Optional, List, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from ..config import get_settings
from ..models import BrokenLinksResult, BrokenLink


class BrokenLinksAnalyzer:
    """Detects broken links on a webpage"""
    
    # Maximum links to check per page
    MAX_LINKS = 50
    
    # Concurrent requests limit
    CONCURRENCY = 10
    
    def __init__(self):
        self.settings = get_settings()
    
    async def analyze(self, url: str, html_content: Optional[str] = None) -> BrokenLinksResult:
        """
        Check for broken links on the given URL
        
        Args:
            url: The URL to analyze
            html_content: Optional pre-rendered HTML (Deep Scan)
            
        Returns:
            BrokenLinksResult with all detected broken links
        """
        result = BrokenLinksResult()
        
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            html = ""
            
            if html_content:
                html = html_content
            else:
                # Fetch the page
                async with httpx.AsyncClient(
                    timeout=self.settings.request_timeout,
                    follow_redirects=True,
                    verify=False
                ) as client:
                    response = await client.get(url)
                    html = response.text
                
            # Extract all links
            links = self._extract_links(html, url, base_url)
            
            # Limit number of links to check
            links = list(links)[:self.MAX_LINKS]
            result.total_links_checked = len(links)
            
            # Check all links concurrently with rate limiting
            broken_links = await self._check_links(links, base_url)
            result.broken_links = broken_links
            result.broken_count = len(broken_links)
            
            # Count internal vs external
            result.internal_broken = sum(1 for link in broken_links if link.is_internal)
            result.external_broken = sum(1 for link in broken_links if not link.is_internal)
                
        except httpx.TimeoutException:
            result.error = "Request timed out while fetching page"
        except Exception as e:
            result.error = f"Link checking error: {str(e)}"
        
        return result
    
    def _extract_links(self, html: str, page_url: str, base_url: str) -> Set[Tuple[str, str, bool]]:
        """
        Extract all links from HTML
        
        Returns:
            Set of tuples (url, anchor_text, is_internal)
        """
        links = set()
        soup = BeautifulSoup(html, "lxml")
        
        # Find all anchor tags
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "").strip()
            anchor_text = a_tag.get_text(strip=True)[:100]  # Limit text length
            
            # Skip empty, javascript, and anchor-only links
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            
            # Resolve relative URLs
            full_url = urljoin(page_url, href)
            
            # Check if internal link
            parsed_link = urlparse(full_url)
            parsed_base = urlparse(base_url)
            is_internal = parsed_link.netloc == parsed_base.netloc
            
            # Only include http/https links
            if parsed_link.scheme in ("http", "https"):
                links.add((full_url, anchor_text, is_internal))
        
        # Also check images
        for img_tag in soup.find_all("img", src=True):
            src = img_tag.get("src", "").strip()
            if not src or src.startswith("data:"):
                continue
            
            full_url = urljoin(page_url, src)
            parsed_link = urlparse(full_url)
            parsed_base = urlparse(base_url)
            is_internal = parsed_link.netloc == parsed_base.netloc
            
            if parsed_link.scheme in ("http", "https"):
                links.add((full_url, f"[Image: {img_tag.get('alt', 'no alt')[:50]}]", is_internal))
        
        return links
    
    async def _check_links(
        self, 
        links: List[Tuple[str, str, bool]], 
        base_url: str
    ) -> List[BrokenLink]:
        """Check links concurrently with rate limiting"""
        semaphore = asyncio.Semaphore(self.CONCURRENCY)
        broken = []
        
        async def check_single_link(link_info: Tuple[str, str, bool]) -> Optional[BrokenLink]:
            url, anchor_text, is_internal = link_info
            
            async with semaphore:
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8"
                    }

                    async with httpx.AsyncClient(
                        timeout=10.0,
                        follow_redirects=True,
                        verify=False,
                        headers=headers
                    ) as client:
                        # Use HEAD request first (faster)
                        try:
                            response = await client.head(url)
                        except httpx.RequestError:
                            # Fallback to GET if HEAD fails connection
                            response = await client.get(url)
                        
                        # If HEAD returns error, try GET (some servers don't support HEAD)
                        if response.status_code >= 400:
                            response = await client.get(url)
                        
                        status_code = response.status_code
                        
                        # Logic split based on User feedback:
                        # "Broken links should only be those that lead to nothing"
                        if is_internal:
                            # Internal links: Strict. Any error is an issue on OUR site.
                            if status_code >= 400:
                                return BrokenLink(
                                    url=url,
                                    status_code=status_code,
                                    source_text=anchor_text if anchor_text else None,
                                    is_internal=is_internal,
                                    error_type="http_error"
                                )
                        else:
                            # External links: Lenient.
                            # Only flag if content definitely missing (404, 410).
                            # We ignore 403 (WAF/Forbidden), 405, 5xx (Server Error), etc. to avoid false positives.
                            if status_code in [404, 410]:
                                return BrokenLink(
                                    url=url,
                                    status_code=status_code,
                                    source_text=anchor_text if anchor_text else None,
                                    is_internal=is_internal,
                                    error_type="http_error"
                                )
                            # All other codes for external links are treated as "OK" (or at least reachable)
                        
                except httpx.TimeoutException:
                    return BrokenLink(
                        url=url,
                        status_code=0,
                        source_text=anchor_text if anchor_text else None,
                        is_internal=is_internal,
                        error_type="timeout"
                    )
                except httpx.ConnectError:
                    return BrokenLink(
                        url=url,
                        status_code=0,
                        source_text=anchor_text if anchor_text else None,
                        is_internal=is_internal,
                        error_type="connection_error"
                    )
                except Exception:
                    return BrokenLink(
                        url=url,
                        status_code=0,
                        source_text=anchor_text if anchor_text else None,
                        is_internal=is_internal,
                        error_type="unknown_error"
                    )
            
            return None
        
        # Check all links concurrently
        tasks = [check_single_link(link) for link in links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        for result in results:
            if isinstance(result, BrokenLink):
                broken.append(result)
        
        return broken
