"""
Widget API
Public endpoint for the lead generation widget.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlmodel import Session
from datetime import datetime, timedelta
from typing import Dict
from ..database import get_session
from ..models.lead import Lead
from ..models.user import User
from ..services.scanner import process_url

router = APIRouter(prefix="/api/widget", tags=["Agency Widget"])

# Simple in-memory rate limiter (for demo purposes, use Redis in prod)
RATE_LIMIT: Dict[str, list] = {}

class WidgetScanRequest(BaseModel):
    url: str
    email: EmailStr
    agency_id: int

class WidgetScanResponse(BaseModel):
    score: int
    message: str

def check_rate_limit(ip: str):
    """Allow max 5 requests per hour per IP"""
    now = datetime.now()
    if ip not in RATE_LIMIT:
        RATE_LIMIT[ip] = []
    
    # Clean old timestamps
    RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if t > now - timedelta(hours=1)]
    
    if len(RATE_LIMIT[ip]) >= 5:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    
    RATE_LIMIT[ip].append(now)

@router.post("/scan", response_model=WidgetScanResponse)
async def widget_scan(
    request: WidgetScanRequest,
    req: Request,
    session: Session = Depends(get_session)
):
    """
    Public endpoint for the Agency Widget.
    Scans a site, saves the lead, and returns a summary score.
    """
    # 1. Rate Limiting
    client_ip = req.client.host
    check_rate_limit(client_ip)
    
    # 2. Verify Agency Exists
    agency = session.get(User, request.agency_id)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
        
    # 3. Validation
    if not request.url.startswith("http"):
        request.url = "https://" + request.url

    try:
        # 4. Run Scan (Standard mode for now)
        # Note: In a real widget, we might want a 'fast' mode that skips heavy Puppeteer stuff
        scan_result = await process_url(request.url)
        
        # 5. Save Lead
        lead = Lead(
            agency_id=request.agency_id,
            prospect_email=request.email,
            prospect_url=request.url,
            scan_score=scan_result.global_score
        )
        session.add(lead)
        session.commit()
        
        # 6. Return Simplified Result
        msg = "Excellent !" if scan_result.global_score >= 80 else \
              "Bon début, mais des améliorations sont nécessaires." if scan_result.global_score >= 50 else \
              "Votre site présente des risques critiques."
              
        return WidgetScanResponse(
            score=scan_result.global_score,
            message=msg
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
