from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select
from ..database import get_session
from ..models.user import User
from ..api.auth import get_current_user
from ..models.lead import Lead
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/leads", tags=["Leads"])

class LeadRead(BaseModel):
    id: int
    prospect_email: str
    prospect_url: str
    scan_score: int
    created_at: datetime
    status: str

@router.get("/", response_model=List[LeadRead])
async def get_agency_leads(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all leads captured by the current user's widget.
    """
    statement = select(Lead).where(Lead.agency_id == current_user.id).order_by(Lead.created_at.desc())
    leads = session.exec(statement).all()
    return leads
