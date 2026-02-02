from fastapi import APIRouter, Depends, HTTPException, Header, Response, status
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from sqlmodel import Session
from ..database import get_session
from ..services.api_keys import get_api_key_by_prefix, update_last_used
from ..services.scanner import process_url
from ..models.api_key import ApiKey
from ..models.schemas import AnalyzeResponse

router = APIRouter(prefix="/api/v1", tags=["DevGuard CI/CD"])

class PipelineScanRequest(BaseModel):
    url: str = Field(..., description="Target URL to scan")
    threshold: int = Field(80, ge=0, le=100, description="Minimum acceptable global score")
    fail_on_error: bool = Field(True, description="Fail pipeline if scan errors occur")

class PipelineScanResponse(BaseModel):
    status: str = "success" # success, fail, error
    score: int
    threshold: int
    issues: List[str]
    report_url: str

async def verify_api_key(
    x_api_key: str = Header(..., description="Your API Key"),
    session: Session = Depends(get_session)
) -> ApiKey:
    """
    Dependency to validate API Key from Header.
    """
    api_key_obj = get_api_key_by_prefix(session, x_api_key)
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    
    # Update usage stats
    update_last_used(session, api_key_obj.id)
    
    return api_key_obj

@router.post("/scan", response_model=PipelineScanResponse, summary="Trigger CI/CD Security Scan")
async def trigger_pipeline_scan(
    request: PipelineScanRequest,
    response: Response,
    api_key: ApiKey = Depends(verify_api_key)
):
    """
    Run a full security & quality scan for CI/CD pipelines.
    
    - **Authentication**: Requires `X-API-Key` header.
    - **Behavior**: Returns 409/422 if score < threshold (to break the build).
    """
    try:
        # Run the standard scan
        scan_result: AnalyzeResponse = await process_url(request.url)
        
        # Calculate global score (ensure it's calculated)
        score = scan_result.global_score
        
        # Identify key issues for the report
        issues = []
        if scan_result.security.score < 80:
            issues.append(f"Security score is low ({scan_result.security.score}/100)")
        if scan_result.seo.scores.performance and scan_result.seo.scores.performance < 50:
             issues.append(f"Performance is critical ({scan_result.seo.scores.performance}/100)")
        
        if scan_result.errors:
             issues.extend(scan_result.errors)

        # Build Response
        result = PipelineScanResponse(
            status="success",
            score=score,
            threshold=request.threshold,
            issues=issues,
            # In a real app, this would link to the persisted report. 
            # For now, we return a mock or current view link.
            report_url=f"https://siteauditor.com/report?url={request.url}" 
        )
        
        # Check Fail Conditions
        if score < request.threshold:
            result.status = "fail"
            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY # Logic failure specific code
            # Or 409 Conflict check pipeline preference. 
            # 422 is semantically "request well-formed but unable to follow instructions due to semantic errors" (score too low)
        
        if request.fail_on_error and scan_result.errors:
             result.status = "error"
             response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        return result
        
    except Exception as e:
        if request.fail_on_error:
            raise HTTPException(status_code=500, detail=str(e))
        return PipelineScanResponse(
            status="error",
            score=0,
            threshold=request.threshold,
            issues=[str(e)],
            report_url=""
        )
