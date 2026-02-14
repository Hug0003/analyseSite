"""
Audit Routes
Endpoints for managing scan history
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, desc, delete
from ..database import get_session
from ..models.user import User
from ..models.audit import Audit, AuditRead, AuditDetail, AuditCreate
from ..deps import get_current_user
import json

router = APIRouter(prefix="/api/audits", tags=["Audits"])


@router.post("", response_model=AuditRead, status_code=status.HTTP_201_CREATED)
async def create_audit(
    audit_in: AuditCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Save a new audit result
    """
    # Check Quota
    from datetime import date
    from ..core.permissions import FeatureGuard
    
    if not FeatureGuard.check_scan_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Daily scan quota reached. Upgrade your plan for more."
        )

    # Update Usage
    today = date.today()
    if current_user.last_scan_date != today:
        current_user.scans_count_today = 1
        current_user.last_scan_date = today
    else:
        current_user.scans_count_today += 1
    
    session.add(current_user)

    audit = Audit(
        user_id=current_user.id,
        url=audit_in.url,
        score=audit_in.score,
        summary=json.dumps(audit_in.summary)
    )
    
    session.add(audit)
    session.commit()
    session.refresh(audit)
    
    return audit


@router.get("", response_model=List[AuditRead])
async def read_audits(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user's audit history
    """
    # Enforce History Limits
    from datetime import datetime, timedelta
    from ..core.permissions import FeatureGuard
    
    plan = current_user.plan_tier or "starter"
    config = FeatureGuard.get_plan_config(plan)
    days_limit = config.get("history_days", 7)
        
    cutoff_date = datetime.utcnow() - timedelta(days=days_limit)
    
    statement = select(Audit).where(
        Audit.user_id == current_user.id,
        Audit.created_at >= cutoff_date
    ).order_by(desc(Audit.created_at)).offset(skip).limit(limit)
    
    audits = session.exec(statement).all()
    return audits


@router.get("/{audit_id}", response_model=AuditDetail)
async def read_audit(
    audit_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get detailed audit result by ID
    """
    statement = select(Audit).where(Audit.id == audit_id, Audit.user_id == current_user.id)
    audit = session.exec(statement).first()
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    return audit


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(
    audit_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete a specific audit result
    """
    statement = select(Audit).where(Audit.id == audit_id, Audit.user_id == current_user.id)
    audit = session.exec(statement).first()
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    session.delete(audit)
    session.commit()
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_audits(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete all audit history for the current user
    """
    statement = delete(Audit).where(Audit.user_id == current_user.id)
    session.exec(statement)
    session.commit()
    return None
