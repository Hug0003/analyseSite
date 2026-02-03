"""
Scanner Service
Orchestrates the analysis of URLs using various specialized analyzers.
"""
import asyncio
import time
import json
from datetime import datetime
from typing import List, Optional, AsyncGenerator
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
    Process a single URL (Wrapper around stream).
    Maintains backward compatibility.
    """
    final_result = None
    async for chunk in process_url_stream(url, lang):
        try:
            data = json.loads(chunk)
            if data.get("type") == "complete":
                final_result = AnalyzeResponse(**data["data"])
        except:
            pass
            
    if not final_result:
        raise Exception("Analysis stream completed without result")
        
    return final_result


async def process_url_stream(url: str, lang: str = "en") -> AsyncGenerator[str, None]:
    """
    Generator that streams analysis progress and final result.
    Yields JSON strings (NDJSON format).
    """
    start_time = time.time()
    
    # 1. Yield Start
    yield json.dumps({"type": "log", "step": "init", "message": f"Starting analysis for {url}..."}) + "\n"

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
        rendered_html = None
        headers = None
        
        # 2. Check Accessibility (Pre-flight check)
        yield json.dumps({"type": "log", "step": "network", "message": "Checking site accessibility..."}) + "\n"
        try:
             async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
                 # Check if site is reachable
                 try:
                    response = await client.head(url)
                    headers = dict(response.headers)
                    if response.status_code >= 400:
                        # try GET if HEAD failed
                         response = await client.get(url)
                         headers = dict(response.headers)
                 except httpx.ConnectError:
                      # DNS or connection failure
                      raise Exception(f"Could not connect to {url}. The site may not exist or is unreachable.")
                 except Exception as e:
                      # Other network error, try one last GET
                      try:
                           response = await client.get(url)
                           headers = dict(response.headers)
                      except Exception:
                           raise Exception(f"Could not connect to {url}. Is the URL correct?")
                 
                 # Final verification
                 if response.status_code >= 500:
                      yield json.dumps({"type": "log", "step": "network", "message": f"Warning: Server returned {response.status_code}."}) + "\n"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Pre-flight check failed for {url}: {e}")
            yield json.dumps({"type": "error", "message": error_msg}) + "\n"
            return
            
        yield json.dumps({"type": "log", "step": "network", "message": "Site is accessible."}) + "\n"

        # 3. Fetch Rendered DOM
        yield json.dumps({"type": "log", "step": "rendering", "message": "Simulating browser visit (Puppeteer)..."}) + "\n"
        try:
            rendered_html = await RenderingService.fetch_rendered_html(url)
            yield json.dumps({"type": "log", "step": "rendering", "message": "Page rendered successfully."}) + "\n"
        except Exception as e:
            logger.error(f"Deep Scan failed for {url}: {e}")
            yield json.dumps({"type": "log", "step": "rendering", "message": "Rendering failed, falling back to static analysis."}) + "\n"
        
        # 4. Prepare Parallel Tasks
        yield json.dumps({"type": "log", "step": "analysis", "message": "Running specialized scanners..."}) + "\n"
        
        async def run_wrapper(name, coro):
            try:
                res = await coro
                return name, res
            except Exception as e:
                return name, e

        tasks = [
            run_wrapper("seo", seo_analyzer.analyze(url, lang, html_content=rendered_html)),
            run_wrapper("security", security_analyzer.analyze(url)),
            run_wrapper("tech", tech_analyzer.analyze(url, html_content=rendered_html, headers=headers)),
            run_wrapper("links", links_analyzer.analyze(url, html_content=rendered_html)),
            run_wrapper("gdpr", gdpr_analyzer.analyze(url)),
            run_wrapper("smo", smo_analyzer.analyze(url, html_content=rendered_html)),
            run_wrapper("green", green_analyzer.analyze(url, html_content=rendered_html)),
            run_wrapper("dns", dns_analyzer.analyze(url))
        ]
        
        results_map = {}
        
        # 5. Run and yield as completed
        for future in asyncio.as_completed(tasks):
             name, result = await future
             results_map[name] = result
             
             # Yield progress log
             clean_name = name.upper() if len(name) < 4 else name.title()
             if isinstance(result, Exception):
                 yield json.dumps({"type": "log", "step": name, "message": f"❌ {clean_name} failed."}) + "\n"
             else:
                 yield json.dumps({"type": "log", "step": name, "message": f"✅ {clean_name} completed."}) + "\n"

        # 6. Aggregate Results
        yield json.dumps({"type": "log", "step": "finalize", "message": "Aggregating results..."}) + "\n"
        
        # Helper to extract or handle error
        def get_res(key, default_cls, err_append):
            res = results_map.get(key)
            if isinstance(res, Exception):
                err_append.append(f"{key.upper()} analysis failed: {str(res)}")
                return default_cls(error=str(res))
            return res or default_cls(error="Result missing")

        seo_result = get_res("seo", SEOResult, errors)
        security_result = get_res("security", SecurityResult, errors)
        tech_result = get_res("tech", TechStackResult, errors)
        links_result = get_res("links", BrokenLinksResult, errors)
        gdpr_result = get_res("gdpr", GDPRResult, errors)
        smo_result = get_res("smo", SMOResult, errors)
        green_result = get_res("green", GreenResult, errors)
        dns_result = get_res("dns", DNSHealthResult, errors)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Build response
        final_response = AnalyzeResponse(
            url=url,
            analyzed_at=datetime.utcnow(),
            status=AuditStatus.COMPLETED,
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
        final_response.calculate_global_score()

        # 7. Yield Final Result
        yield json.dumps({
            "type": "complete", 
            "data": final_response.model_dump(mode='json')
        }) + "\n"

    except Exception as e:
        logger.error(f"Stream failed: {e}")
        yield json.dumps({"type": "error", "message": str(e)}) + "\n"
        raise e
