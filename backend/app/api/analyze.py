"""
Analysis Endpoint
Main API route for URL analysis
"""
# ── Standard Library ──
import asyncio
import logging
import time
import uuid
from datetime import datetime, date
from typing import Optional

# ── Third-Party ──
import validators
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlmodel import Session

# ── Local ──
from ..database import get_session, engine
from ..deps import get_current_user
from ..models.user import User
from ..core.permissions import FeatureGuard
from ..models import AnalyzeRequest, AnalyzeResponse, TaskResponse
from ..models.task import ScanTask, AuditStatus
from ..services import (
    SEOAnalyzer,
    SecurityAnalyzer,
    TechStackAnalyzer,
    BrokenLinksAnalyzer,
    GDPRAnalyzer,
    SMOAnalyzer,
    GreenITAnalyzer,
    DNSAnalyzer,
)
from ..services.scanner import process_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AnalyzeResponse:
    if not FeatureGuard.check_scan_quota(current_user):
        raise HTTPException(
            status_code=403,
            detail="Daily scan quota reached. Upgrade your plan for more.",
        )
    # Increment scan counter
    today = date.today()
    if current_user.last_scan_date != today:
        current_user.scans_count_today = 1
        current_user.last_scan_date = today
    else:
        current_user.scans_count_today += 1
    session.add(current_user)
    session.commit()
    url = request.url
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
            competitor_response = results[1]
            main_response.competitor = competitor_response
            
            # Enable Versus Mode
            main_response.versus_mode = True
            
            # Calculate Winner
            main_score = main_response.global_score
            competitor_score = competitor_response.global_score
            
            if main_score > competitor_score:
                main_response.winner = "target"
            elif main_score < competitor_score:
                main_response.winner = "competitor"
            else:
                main_response.winner = "draw"
            
            logger.info(f"🏆 Battle Mode: {main_response.url} ({main_score}) vs {competitor_response.url} ({competitor_score}) - Winner: {main_response.winner}")
            
        return main_response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


from ..services.scanner import process_url_stream

@router.get("/stream")
async def analyze_stream(
    url: str,
    lang: str = "en",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not FeatureGuard.check_scan_quota(current_user):
        raise HTTPException(
            status_code=403,
            detail="Daily scan quota reached. Upgrade your plan for more.",
        )
    # Increment scan counter
    today = date.today()
    if current_user.last_scan_date != today:
        current_user.scans_count_today = 1
        current_user.last_scan_date = today
    else:
        current_user.scans_count_today += 1
    session.add(current_user)
    session.commit()
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
        
    return StreamingResponse(
        process_url_stream(url, lang), 
        media_type="application/x-ndjson"
    )



async def process_scan_background(task_id: str, url: str, lang: str):
    """
    Background worker for scan processing.
    updates the task status in DB.
    """
    logger.info(f"Starting background scan for task {task_id}")
    
    # Create a new session for this background task
    with Session(engine) as session:
        task = session.get(ScanTask, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = AuditStatus.RUNNING
        session.add(task)
        session.commit()
        
        try:
            # Run the heavy scan (Async)
            # Note: We await it directly since we are in an async function
            result = await process_url(url, lang)
            
            # Save result
            task.result = result.model_dump(mode='json')
            task.status = AuditStatus.COMPLETED
            task.finished_at = datetime.utcnow()
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task.error = str(e)
            task.status = AuditStatus.FAILED
        
        session.add(task)
        session.commit()


@router.post("/analyze/async", response_model=TaskResponse)
async def analyze_url_async(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not FeatureGuard.check_scan_quota(current_user):
        raise HTTPException(
            status_code=403,
            detail="Daily scan quota reached. Upgrade your plan for more.",
        )
    # Increment scan counter
    today = date.today()
    if current_user.last_scan_date != today:
        current_user.scans_count_today = 1
        current_user.last_scan_date = today
    else:
        current_user.scans_count_today += 1
    session.add(current_user)
    session.commit()
    url = request.url
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")

    # Create Task Record
    task_id = str(uuid.uuid4())
    task = ScanTask(
        id=task_id,
        url=url,
        status=AuditStatus.PENDING
    )
    session.add(task)
    session.commit()
    
    # Enqueue Background Job
    background_tasks.add_task(process_scan_background, task_id, url, request.lang)
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        url=url
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.post("/analyze/seo")
async def analyze_seo_only(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze only SEO and Performance"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = SEOAnalyzer()
    result = await analyzer.analyze(url, request.lang)
    return result


@router.post("/analyze/security")
async def analyze_security_only(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze only Security"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = SecurityAnalyzer()
    result = await analyzer.analyze(url)
    return result


@router.post("/analyze/tech")
async def analyze_tech_only(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze only Technology Stack"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = TechStackAnalyzer()
    result = await analyzer.analyze(url)
    return result


@router.post("/analyze/links")
async def analyze_links_only(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze only Broken Links"""
    url = request.url
    
    if not validators.url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    analyzer = BrokenLinksAnalyzer()
    result = await analyzer.analyze(url)
    return result

