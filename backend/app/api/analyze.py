"""
Analysis Endpoint
Main API route for URL analysis
"""
import asyncio
import time
import validators
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models import AnalyzeRequest, AnalyzeResponse, AuditStatus
from ..services import (
    SEOAnalyzer,
    SecurityAnalyzer, 
    TechStackAnalyzer,
    BrokenLinksAnalyzer,
    GDPRAnalyzer,
    SMOAnalyzer,
    GreenITAnalyzer,
    DNSAnalyzer
)


router = APIRouter(prefix="/api", tags=["Analysis"])


from ..services.scanner import process_url


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a URL for SEO, Security, Technology Stack, and Broken Links.
    If competitor_url is provided, analyzes both in parallel.
    """
    url = request.url
    
    # Validate URLs
    if not validators.url(url):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid URL format: {url}"
        )
    
    if request.competitor_url and not validators.url(request.competitor_url):
         raise HTTPException(
            status_code=400,
            detail=f"Invalid Competitor URL format: {request.competitor_url}"
        )
    
    try:
        # Prepare tasks
        tasks = [process_url(url, request.lang)]
        
        if request.competitor_url:
            tasks.append(process_url(request.competitor_url, request.lang))
        
        # Run in parallel
        results = await asyncio.gather(*tasks)
        
        main_response = results[0]
        
        # Attach competitor result if present
        if len(results) > 1:
            main_response.competitor = results[1]
            
        return main_response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.post("/analyze/seo")
async def analyze_seo_only(request: AnalyzeRequest):
    """Analyze only SEO and Performance"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = SEOAnalyzer()
    result = await analyzer.analyze(url, request.lang)
    return result


@router.post("/analyze/security")
async def analyze_security_only(request: AnalyzeRequest):
    """Analyze only Security"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = SecurityAnalyzer()
    result = await analyzer.analyze(url)
    return result


@router.post("/analyze/tech")
async def analyze_tech_only(request: AnalyzeRequest):
    """Analyze only Technology Stack"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = TechStackAnalyzer()
    result = await analyzer.analyze(url)
    return result


@router.post("/analyze/links")
async def analyze_links_only(request: AnalyzeRequest):
    """Analyze only Broken Links"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = BrokenLinksAnalyzer()
    result = await analyzer.analyze(url)
    return result
