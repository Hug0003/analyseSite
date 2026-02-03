"""
Green IT / Eco-Index Analyzer Service
Estimates CO2 impact based on resource weight.
"""
import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Set, Tuple, Optional

from ..config import get_settings
from ..models.schemas import GreenResult

class GreenITAnalyzer:
    def __init__(self):
        self.settings = get_settings()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; EcoIndexBot/1.0; +http://example.com)"
        }

    async def analyze(self, url: str, html_content: Optional[str] = None) -> GreenResult:
        result = GreenResult()
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, verify=False, headers=self.headers) as client:
                # 1. Fetch Main Page
                try:
                    if html_content:
                        html = html_content
                        html_size = len(html.encode("utf-8"))
                    else:
                        resp = await client.get(url)
                        if resp.status_code >= 400:
                            result.error = f"HTTP Error {resp.status_code}"
                            return result
                        html_size = len(resp.content)
                        html = resp.text
                except Exception as e:
                    result.error = f"Failed to fetch page: {str(e)}"
                    return result

                # 2. Extract Resources
                soup = BeautifulSoup(html, "html.parser")
                resources = self._extract_resources(soup, url)
                
                # 3. Get Sizes Concurrently
                total_bytes = html_size
                
                # Limit concurrency
                sem = asyncio.Semaphore(10)
                
                async def get_size(res_url):
                    async with sem:
                        try:
                            # HEAD request for size
                            head = await client.head(res_url, timeout=5.0)
                            cl = head.headers.get("content-length")
                            if cl:
                                return int(cl)
                            return 0
                        except:
                            return 0
                
                if resources:
                    tasks = [get_size(r) for r in resources]
                    sizes = await asyncio.gather(*tasks)
                    total_bytes += sum(sizes)
                
                result.resource_count = len(resources) + 1 # +1 for HTML
                
                # 4. Calculate CO2
                total_mb = total_bytes / (1024 * 1024)
                result.total_size_mb = round(total_mb, 3)
                
                # Formula: 0.6g CO2 per MB
                result.co2_grams = round(total_mb * 0.6, 3)
                
                # 5. Grading
                result.grade, result.score = self._calculate_grade(result.co2_grams)

        except Exception as e:
            result.error = str(e)
            
        return result

    def _extract_resources(self, soup, base_url) -> Set[str]:
        urls = set()
        
        # Images
        for img in soup.find_all("img", src=True):
            src = img.get("src")
            if src and not src.startswith("data:"):
                urls.add(urljoin(base_url, src))
                
        # Scripts
        for script in soup.find_all("script", src=True):
            src = script.get("src")
            if src:
                urls.add(urljoin(base_url, src))
                
        # Styles
        for link in soup.find_all("link", rel="stylesheet", href=True):
            href = link.get("href")
            if href:
                urls.add(urljoin(base_url, href))
                
        # Media (Video/Audio)
        for source in soup.find_all("source", src=True):
            src = source.get("src")
            if src:
                urls.add(urljoin(base_url, src))
                
        # Iframe sources? usually other pages, but contribute to load.
        # Often external, complicated. Let's stick to core assets.

        return urls

    def _calculate_grade(self, co2: float) -> Tuple[str, int]:
        # A: < 0.5g
        # B: 0.5 - 1
        # C: 1 - 1.5
        # D: 1.5 - 2
        # E: 2 - 3
        # F: 3 - 5
        # G: > 5
        
        if co2 < 0.5: return "A", 100
        if co2 < 1.0: return "B", 85
        if co2 < 1.5: return "C", 70
        if co2 < 2.0: return "D", 55
        if co2 < 3.0: return "E", 40
        if co2 < 5.0: return "F", 25
        return "G", 10
