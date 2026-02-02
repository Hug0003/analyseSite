"""
Scanner Service
Orchestrates the analysis of URLs using various specialized analyzers.
"""
import asyncio
import time
from datetime import datetime
from typing import List, Optional
import httpx
import logging
from .rendering import RenderingService

logger = logging.getLogger(__name__)

from ..models import (
    AnalyzeResponse, 
    AuditStatus,
    SEOResult,
    SecurityResult,
    TechStackResult,
    BrokenLinksResult,
    GDPRResult,
    SMOResult,
    GreenResult,
    DNSHealthResult
)

from .seo import SEOAnalyzer
from .security import SecurityAnalyzer
from .tech import TechStackAnalyzer
from .links import BrokenLinksAnalyzer
from .gdpr import GDPRAnalyzer
from .smo import SMOAnalyzer
from .green_it import GreenITAnalyzer
from .dns_health import DNSAnalyzer

async def process_url(url: str, lang: str = "en") -> AnalyzeResponse:
    """
    Process a single URL.
    Runs all analyzers in parallel.
    """
    start_time = time.time()
    
    # Initialize analyzers
    seo_analyzer = SEOAnalyzer()
    security_analyzer = SecurityAnalyzer()
    tech_analyzer = TechStackAnalyzer()
    links_analyzer = BrokenLinksAnalyzer()
    gdpr_analyzer = GDPRAnalyzer()
    smo_analyzer = SMOAnalyzer()
    green_analyzer = GreenITAnalyzer()
    dns_analyzer = DNSAnalyzer()
    
    errors = []
    
    try:
        # Run all analyses in parallel
    

        rendered_html = None
        headers = None
        
        # 1. Fetch Headers (Lightweight)
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
                 h_resp = await client.head(url)
                 headers = dict(h_resp.headers)
                 if not headers or len(headers) < 3:
                     h_resp = await client.get(url)  # Fallback
                     headers = dict(h_resp.headers)
        except Exception as e:
            logger.warning(f"Failed to fetch initial headers for {url}: {e}")

        # 2. Fetch Rendered DOM (Deep Scan)
        try:
            rendered_html = await RenderingService.fetch_rendered_html(url)
        except Exception as e:
            logger.error(f"Deep Scan failed for {url}: {e}")
            # Analyzers will fall back to their own fetching if html is None
        
        # Run all analyses in parallel
        seo_result, security_result, tech_result, links_result, gdpr_result, smo_result, green_result, dns_result = await asyncio.gather(
            seo_analyzer.analyze(url, lang, html_content=rendered_html),
            security_analyzer.analyze(url),
            tech_analyzer.analyze(url, html_content=rendered_html, headers=headers),
            links_analyzer.analyze(url, html_content=rendered_html),
            gdpr_analyzer.analyze(url),
            smo_analyzer.analyze(url, html_content=rendered_html),
            green_analyzer.analyze(url, html_content=rendered_html),
            dns_analyzer.analyze(url),
            return_exceptions=True
        )
        
        # Handle any exceptions from individual analyzers
        if isinstance(seo_result, Exception):
            errors.append(f"SEO analysis failed: {str(seo_result)}")
            seo_result = SEOResult(error=str(seo_result))
        
        if isinstance(security_result, Exception):
            errors.append(f"Security analysis failed: {str(security_result)}")
            security_result = SecurityResult(error=str(security_result))
        
        if isinstance(tech_result, Exception):
            errors.append(f"Tech stack analysis failed: {str(tech_result)}")
            tech_result = TechStackResult(error=str(tech_result))
        
        if isinstance(links_result, Exception):
            errors.append(f"Broken links analysis failed: {str(links_result)}")
            links_result = BrokenLinksResult(error=str(links_result))

        if isinstance(gdpr_result, Exception):
            errors.append(f"GDPR analysis failed: {str(gdpr_result)}")
            gdpr_result = GDPRResult(error=str(gdpr_result))

        if isinstance(smo_result, Exception):
            errors.append(f"SMO analysis failed: {str(smo_result)}")
            smo_result = SMOResult(error=str(smo_result))

        if isinstance(green_result, Exception):
            errors.append(f"Green IT analysis failed: {str(green_result)}")
            green_result = GreenResult(error=str(green_result))

        if isinstance(dns_result, Exception):
            errors.append(f"DNS analysis failed: {str(dns_result)}")
            dns_result = DNSHealthResult(error=str(dns_result))
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Build response
        response = AnalyzeResponse(
            url=url,
            analyzed_at=datetime.utcnow(),
            status=AuditStatus.COMPLETED if not errors else AuditStatus.COMPLETED,
            seo=seo_result,
            security=security_result,
            tech_stack=tech_result,
            broken_links=links_result,
            gdpr=gdpr_result,
            smo=smo_result,
            green_it=green_result,
            dns_health=dns_result,
            scan_duration_seconds=round(duration, 2),
            errors=errors
        )
        
        # Calculate global score
        response.calculate_global_score()
        
        return response
        
    except Exception as e:
        # Ensure we don't crash the whole parallel execution if one site completely fails before gathering
        raise e
