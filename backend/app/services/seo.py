"""
SEO & Performance Analysis Service
Uses Google PageSpeed Insights API (Lighthouse)
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from ..config import get_settings
from ..models import SEOResult, CoreWebVitals, LighthouseScores

# Configure logging
logger = logging.getLogger(__name__)


class SEOAnalyzer:
    """Analyzes SEO and performance using Google PageSpeed Insights"""
    
    PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.google_pagespeed_api_key
    
    async def analyze(self, url: str, lang: str = "en", html_content: Optional[str] = None) -> SEOResult:
        """
        Run PageSpeed Insights analysis on the given URL, with local fallback.
        
        Args:
            url: The URL to analyze
            lang: Language code for results (en, fr)
            html_content: Optional pre-rendered HTML (Deep Scan) for fallback analysis
            
        Returns:
            SEOResult with Lighthouse scores or local fallback
        """
        logger.info(f"📊 Starting SEO analysis for: {url} (lang: {lang})")
        
        # Check API key status
        has_api_key = bool(self.api_key and self.api_key != "your_api_key_here" and len(self.api_key) > 10)
        
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                params = {
                    "url": url,
                    "strategy": "mobile",
                    "category": ["performance", "seo", "accessibility", "best-practices"],
                    "locale": lang
                }
                
                if has_api_key:
                    params["key"] = self.api_key
                else:
                    logger.warning("⚠️ No API key - using anonymous mode (rate limited)")
                
                logger.info(f"🌐 Sending request to PageSpeed API...")
                
                response = await client.get(self.PAGESPEED_API_URL, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Got PageSpeed response successfully")
                    return self._parse_response(data)
                
                # API Failed (429, 400, 500, etc.)
                logger.warning(f"⚠️ PageSpeed API error: {response.status_code}. Response: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"❌ SEO API connection error: {str(e)}")
        
        # --- Fallback: Local Analysis ---
        target_html = html_content
        
        if not target_html:
            logger.info("⚠️ No Deep Scan HTML available. Attempting simple fetch for local fallback...")
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False, headers={"User-Agent": "Mozilla/5.0 (compatible; SiteAuditorBot/1.0)"}) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        target_html = resp.text
            except Exception as e:
                logger.error(f"❌ Fallback fetch failed: {e}")

        if target_html:
            logger.info("⚡ Executing Local SEO Analysis")
            return self._local_analyze(target_html, url)
            
        return SEOResult(error="PageSpeed API failed and all local fetch attempts failed.")

    def _local_analyze(self, html: str, url: str) -> SEOResult:
        """Perform basic SEO analysis locally using BeautifulSoup"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            result = SEOResult()
            result.scores = LighthouseScores(performance=0, seo=0, accessibility=0, best_practices=0)
            
            audits = []
            score_acc = 0
            
            # 1. Title
            title = soup.title.string.strip() if soup.title and soup.title.string else None
            has_title = bool(title)
            score_acc += 20 if has_title else 0
            audits.append({
                "id": "document-title", 
                "title": "Document has a title", 
                "passed": has_title, 
                "displayValue": title if title else "Missing"
            })
            
            # 2. Meta Description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            has_desc = bool(meta_desc and meta_desc.get("content"))
            score_acc += 20 if has_desc else 0
            audits.append({
                "id": "meta-description", 
                "title": "Document has a meta description", 
                "passed": has_desc,
                "displayValue": meta_desc["content"][:50] + "..." if has_desc else "Missing"
            })
            
            # 3. H1
            h1s = soup.find_all("h1")
            has_h1 = len(h1s) == 1
            score_acc += 20 if has_h1 else (10 if len(h1s) > 0 else 0)
            audits.append({
                "id": "heading-order", 
                "title": "Heading structure", 
                "passed": has_h1,
                "displayValue": f"Found {len(h1s)} H1 tags"
            })
            
            # 4. Image Alts
            imgs = soup.find_all("img")
            imgs_missing_alt = [img for img in imgs if not img.get("alt")]
            passed_alts = len(imgs) > 0 and len(imgs_missing_alt) == 0
            score_acc += 20 if passed_alts else 0
            audits.append({
                "id": "image-alt",
                "title": "Images have alt attributes",
                "passed": passed_alts,
                "displayValue": f"{len(imgs_missing_alt)} images missing alt text"
            })
            
            # 5. Viewport
            viewport = soup.find("meta", attrs={"name": "viewport"})
            has_viewport = bool(viewport and viewport.get("content"))
            score_acc += 20 if has_viewport else 0
            audits.append({
                "id": "viewport",
                "title": "Has viewport meta tag",
                "passed": has_viewport
            })

            # Calculate pseudo-score
            result.scores.seo = score_acc
            # 6. EST. Performance Score
            perf_score = 100
            
            # Penalty for HTML size (> 200KB)
            html_size_kb = len(html) / 1024
            if html_size_kb > 200: perf_score -= 10
            if html_size_kb > 1000: perf_score -= 20
            
            # Penalty for too many scripts (> 20)
            scripts_count = len(soup.find_all("script"))
            if scripts_count > 20: perf_score -= 10
            if scripts_count > 50: perf_score -= 15
            
            # Penalty for missing lazy loading
            imgs_no_lazy = [img for img in imgs if img.get("loading") != "lazy"]
            if len(imgs_no_lazy) > 5: perf_score -= 5
            
            result.scores.performance = max(30, min(95, perf_score))
            result.audits = audits
            
            # Add a warning note
            result.diagnostics = [{
                "id": "local-fallback",
                "title": "Local Analysis Mode",
                "description": "Google PageSpeed API was unreachable. Results are estimated locally from Deep Scan data.",
                "score": 0.5
            }]
            
            return result
            
        except Exception as e:
            logger.error(f"Local analysis failed: {e}")
            return SEOResult(error=f"Local analysis failed: {e}")
    
    def _parse_response(self, data: Dict[str, Any]) -> SEOResult:
        """Parse PageSpeed Insights API response"""
        result = SEOResult()
        
        try:
            lighthouse = data.get("lighthouseResult", {})
            categories = lighthouse.get("categories", {})
            audits = lighthouse.get("audits", {})
            
            logger.info(f"📊 Parsing Lighthouse results...")
            
            # Extract category scores (0-1 scale, convert to 0-100)
            perf_score = self._extract_score(categories.get("performance"))
            seo_score = self._extract_score(categories.get("seo"))
            a11y_score = self._extract_score(categories.get("accessibility"))
            bp_score = self._extract_score(categories.get("best-practices"))
            
            logger.info(f"   Performance: {perf_score}")
            logger.info(f"   SEO: {seo_score}")
            logger.info(f"   Accessibility: {a11y_score}")
            logger.info(f"   Best Practices: {bp_score}")
            
            result.scores = LighthouseScores(
                performance=perf_score,
                seo=seo_score,
                accessibility=a11y_score,
                best_practices=bp_score
            )
            
            # Extract Core Web Vitals
            result.core_web_vitals = self._extract_core_web_vitals(audits, data)
            
            # Extract detailed audits
            result.audits = self._extract_audits(audits)
            
            # Extract opportunities (performance improvements)
            result.opportunities = self._extract_opportunities(audits)
            
            # Extract diagnostics
            result.diagnostics = self._extract_diagnostics(audits)
            
            logger.info(f"✅ SEO analysis complete")
            
        except Exception as e:
            logger.error(f"❌ Error parsing PageSpeed response: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            result.error = f"Error parsing response: {str(e)}"
        
        return result
    
    def _extract_score(self, category: Optional[Dict]) -> Optional[int]:
        """Extract score from category data"""
        if category and "score" in category:
            score = category["score"]
            if score is not None:
                return int(score * 100)
        return None
    
    def _extract_core_web_vitals(self, audits: Dict, data: Dict) -> CoreWebVitals:
        """Extract Core Web Vitals metrics"""
        vitals = CoreWebVitals()
        
        # Try to get from loading experience (real user data) first
        loading_exp = data.get("loadingExperience", {}).get("metrics", {})
        
        # LCP - Largest Contentful Paint
        lcp_data = loading_exp.get("LARGEST_CONTENTFUL_PAINT_MS", {})
        if lcp_data:
            vitals.lcp = lcp_data.get("percentile", 0) / 1000  # Convert to seconds
            vitals.lcp_score = lcp_data.get("category", "").lower().replace("_", "-")
        elif "largest-contentful-paint" in audits:
            vitals.lcp = audits["largest-contentful-paint"].get("numericValue", 0) / 1000
            vitals.lcp_score = self._get_metric_rating(vitals.lcp, 2.5, 4.0)
        
        # FID - First Input Delay (or INP as replacement)
        fid_data = loading_exp.get("FIRST_INPUT_DELAY_MS", {})
        if fid_data:
            vitals.fid = fid_data.get("percentile", 0)
            vitals.fid_score = fid_data.get("category", "").lower().replace("_", "-")
        
        # INP - Interaction to Next Paint (newer metric)
        inp_data = loading_exp.get("INTERACTION_TO_NEXT_PAINT", {})
        if inp_data:
            vitals.inp = inp_data.get("percentile", 0)
        elif "experimental-interaction-to-next-paint" in audits:
            vitals.inp = audits["experimental-interaction-to-next-paint"].get("numericValue")
        
        # CLS - Cumulative Layout Shift
        cls_data = loading_exp.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {})
        if cls_data:
            vitals.cls = cls_data.get("percentile", 0) / 100
            vitals.cls_score = cls_data.get("category", "").lower().replace("_", "-")
        elif "cumulative-layout-shift" in audits:
            vitals.cls = audits["cumulative-layout-shift"].get("numericValue", 0)
            vitals.cls_score = self._get_metric_rating(vitals.cls, 0.1, 0.25)
        
        # FCP - First Contentful Paint
        if "first-contentful-paint" in audits:
            vitals.fcp = audits["first-contentful-paint"].get("numericValue", 0) / 1000
        
        # TTFB - Time to First Byte
        if "server-response-time" in audits:
            vitals.ttfb = audits["server-response-time"].get("numericValue")
        
        return vitals
    
    def _get_metric_rating(self, value: float, good_threshold: float, poor_threshold: float) -> str:
        """Get rating based on thresholds"""
        if value <= good_threshold:
            return "good"
        elif value <= poor_threshold:
            return "needs-improvement"
        return "poor"
    
    def _extract_audits(self, audits: Dict) -> List[Dict[str, Any]]:
        """Extract key audits with their status"""
        key_audits = [
            "meta-description", "document-title", "viewport", "robots-txt",
            "canonical", "hreflang", "structured-data", "http-status-code",
            "is-crawlable", "link-text", "image-alt", "heading-order"
        ]
        
        extracted = []
        for audit_id in key_audits:
            if audit_id in audits:
                audit = audits[audit_id]
                extracted.append({
                    "id": audit_id,
                    "title": audit.get("title", ""),
                    "description": audit.get("description", ""),
                    "score": audit.get("score"),
                    "displayValue": audit.get("displayValue", ""),
                    "passed": audit.get("score", 0) == 1
                })
        
        return extracted
    
    def _extract_opportunities(self, audits: Dict) -> List[Dict[str, Any]]:
        """Extract performance improvement opportunities"""
        opportunity_ids = [
            "render-blocking-resources", "unused-css-rules", "unused-javascript",
            "modern-image-formats", "uses-optimized-images", "uses-responsive-images",
            "efficient-animated-content", "preload-lcp-image", "total-byte-weight",
            "uses-text-compression", "uses-rel-preconnect"
        ]
        
        opportunities = []
        for audit_id in opportunity_ids:
            if audit_id in audits:
                audit = audits[audit_id]
                score = audit.get("score", 1)
                
                # Only include if there's room for improvement
                if score is not None and score < 1:
                    opportunities.append({
                        "id": audit_id,
                        "title": audit.get("title", ""),
                        "description": audit.get("description", ""),
                        "score": score,
                        "savings": audit.get("numericValue"),
                        "displayValue": audit.get("displayValue", "")
                    })
        
        # Sort by score (lowest first = most impactful)
        opportunities.sort(key=lambda x: x.get("score", 1))
        
        return opportunities[:10]  # Return top 10
    
    def _extract_diagnostics(self, audits: Dict) -> List[Dict[str, Any]]:
        """Extract diagnostic information"""
        diagnostic_ids = [
            "dom-size", "critical-request-chains", "largest-contentful-paint-element",
            "layout-shift-elements", "long-tasks", "main-thread-work-breakdown",
            "bootup-time", "font-display", "third-party-summary"
        ]
        
        diagnostics = []
        for audit_id in diagnostic_ids:
            if audit_id in audits:
                audit = audits[audit_id]
                diagnostics.append({
                    "id": audit_id,
                    "title": audit.get("title", ""),
                    "description": audit.get("description", ""),
                    "displayValue": audit.get("displayValue", ""),
                    "score": audit.get("score")
                })
        
        return diagnostics
