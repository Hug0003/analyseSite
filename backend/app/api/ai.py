from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel 
from app.services.ai_advisor import generate_executive_summary, AiSummaryResponse
# from app.api.analyze import last_analysis_result # Removed unused import
# Ideally we should fetch from DB, but for now let's assume we pass the result or fetch last
# For this implementation, let's accept the analysis result in the body OR fetch from a cache.
# To keep it STATELESS and simple for now, the frontend will send the analysis JSON back (or ID).
# BETTER: The frontend sends the analysis ID, but we don't have a DB for ad-hoc scans yet.
# SO: We will accept the scan result as body (filtered by frontend?) OR just full body.
# Given payload size, it's better if Frontend sends the full JSON, and Backend minimizes it.

router = APIRouter()

class GenerateSummaryRequest(BaseModel):
    scan_results: dict

@router.post("/summary", response_model=AiSummaryResponse)
async def get_ai_summary(request: GenerateSummaryRequest):
    """
    Generates an AI Executive Summary based on the provided scan results.
    """
    if not request.scan_results:
        raise HTTPException(status_code=400, detail="Scan results are required")
        
    return await generate_executive_summary(request.scan_results)
