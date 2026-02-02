"""
Social Media Optimization (SMO) Analyzer Service
Extracts and validates Open Graph and Twitter Card metadata for social previews.
"""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional

from ..models.schemas import SMOResult

class SMOAnalyzer:
    def __init__(self):
        # Mimic a standard browser/bot
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SiteAuditorBot/1.0; +http://example.com/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    async def analyze(self, url: str, html_content: Optional[str] = None) -> SMOResult:
        result = SMOResult()
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0, headers=self.headers, verify=False) as client:
                html = ""
                
                if html_content:
                    html = html_content
                else:
                    try:
                        response = await client.get(url)
                    except Exception as e:
                        result.error = f"Connection error: {str(e)}"
                        return result

                    if response.status_code >= 400:
                        result.error = f"Failed to fetch page: {response.status_code}"
                        return result

                    html = response.text
                soup = BeautifulSoup(html, "html.parser")

                # --- 1. Extraction ---
                og_title = self._get_meta(soup, "og:title")
                og_desc = self._get_meta(soup, "og:description")
                og_image = self._get_meta(soup, "og:image")
                og_url = self._get_meta(soup, "og:url")
                og_site_name = self._get_meta(soup, "og:site_name")

                twitter_card = self._get_meta(soup, "twitter:card", "name")
                twitter_title = self._get_meta(soup, "twitter:title", "name")
                twitter_desc = self._get_meta(soup, "twitter:description", "name")
                twitter_image = self._get_meta(soup, "twitter:image", "name")

                # Basic Meta Fallbacks
                page_title = soup.title.string.strip() if soup.title and soup.title.string else None
                meta_desc_tag = soup.find("meta", attrs={"name": "description"})
                meta_desc = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.get("content") else None

                # --- 2. Intelligent Logic (Fallbacks) ---
                
                # Title: Prefer OG, then Twitter, then Page Title
                result.title = og_title or twitter_title or page_title
                result.twitter_title = twitter_title or result.title

                # Description: Prefer OG, then Twitter, then Meta Description
                result.description = og_desc or twitter_desc or meta_desc
                result.twitter_description = twitter_desc or result.description

                # Image: Prefer Twitter if checking for twitter card specifically, but usually OG is master
                # Need to resolve URLs first before assigning final
                
                # URL Resolution
                if og_image:
                    og_image = urljoin(url, og_image)
                if twitter_image:
                    twitter_image = urljoin(url, twitter_image)
                
                result.image = og_image
                result.twitter_image = twitter_image or og_image # Fallback to OG image for twitter
                
                result.url = og_url or url
                result.site_name = og_site_name
                result.twitter_card = twitter_card or "summary_large_image" # Default to large image if missing

                # --- 3. Image Validation ---
                
                # We check the main image that would be displayed
                img_to_check = result.twitter_image or result.image
                
                if img_to_check:
                    is_valid = await self._check_image(client, img_to_check)
                    result.image_status = "valid" if is_valid else "broken"
                else:
                    result.image_status = "missing"

                # --- 4. Scoring & Validation ---
                missing = []
                if not og_title and not twitter_title: missing.append("og:title")
                if not og_desc and not twitter_desc: missing.append("og:description")
                if not og_image and not twitter_image: missing.append("og:image")
                
                result.missing_tags = missing
                
                # Simple Score Logic
                score = 100
                if not result.title: score -= 30
                if not result.description: score -= 20
                if not result.image: score -= 40
                elif result.image_status == "broken": score -= 40 # Penalty for broken image even if tag exists
                
                result.score = max(0, score)

        except Exception as e:
            result.error = f"Analysis error: {str(e)}"

        return result

    def _get_meta(self, soup, property_name: str, attr="property") -> Optional[str]:
        """Helper to safely extract meta content"""
        # Try finding by property (og:*) or name (twitter:*)
        tag = soup.find("meta", attrs={attr: property_name})
        
        # Fallback: sometimes people swap name/property
        if not tag:
             alt_attr = "name" if attr == "property" else "property"
             tag = soup.find("meta", attrs={alt_attr: property_name})
        
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    async def _check_image(self, client, url: str) -> bool:
        """HEAD request to validate image presence"""
        try:
            # First try HEAD
            try:
                head_res = await client.head(url)
                if head_res.status_code < 400:
                    return True
            except:
                pass # Fallback to GET
                
            # Retry with GET (Range)
            headers = {"Range": "bytes=0-1024"} # First 1KB
            get_res = await client.get(url, headers=headers)
            return get_res.status_code < 400
        except:
            return False
