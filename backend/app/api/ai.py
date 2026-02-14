"""
AI Endpoints
Routes for AI-powered summary and fix generation.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..deps import get_current_user
from ..models.user import User
from ..core.permissions import FeatureGuard
from ..services.ai_advisor import generate_executive_summary, AiSummaryResponse
from ..services.ai_fixer import generate_fix

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI"])


# ── Request Schemas ──

class AiSummaryRequest(BaseModel):
    scan_results: Dict[str, Any]


class AiFixRequest(BaseModel):
    issue_type: str
    context: Dict[str, Any] = {}


# ── Routes ──

@router.post("/summary", response_model=AiSummaryResponse)
async def ai_summary(
    request: AiSummaryRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an AI executive summary from scan results."""
    if not FeatureGuard.can_perform_action(current_user, "ai_assistant"):
        raise HTTPException(
            status_code=403,
            detail="L'accès IA nécessite un abonnement Pro ou Agency."
        )
    try:
        result = await generate_executive_summary(request.scan_results)
        return result
    except Exception as e:
        logger.error(f"AI Summary endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI summary generation failed: {str(e)}")


@router.post("/fix")
async def ai_fix(
    request: AiFixRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an AI-powered fix guide for a specific issue."""
    if not FeatureGuard.can_perform_action(current_user, "ai_assistant"):
        raise HTTPException(
            status_code=403,
            detail="L'accès IA nécessite un abonnement Pro ou Agency."
        )
    try:
        result = await generate_fix(request.issue_type, request.context)
        return result
    except Exception as e:
        logger.error(f"AI Fix endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI fix generation failed: {str(e)}")

