"""
Monitor Routes
Endpoints for managing URL monitors (Watchdog)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from ..database import get_session
from ..models.user import User
from ..models.monitor import Monitor, MonitorCreate, MonitorRead, MonitorUpdate
from ..deps import get_current_user
from ..services.monitoring import check_monitors

router = APIRouter(prefix="/api/monitors", tags=["Monitoring"])

@router.post("/", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    monitor_in: MonitorCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new URL monitor (Watchdog)
    """
    # Check limit? (Optional)
    
    monitor = Monitor(
        user_id=current_user.id,
        url=monitor_in.url,
        frequency=monitor_in.frequency,
        threshold=monitor_in.threshold
    )
    
    session.add(monitor)
    session.commit()
    session.refresh(monitor)
    return monitor

@router.get("/", response_model=List[MonitorRead])
async def read_monitors(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    List all active monitors for the current user
    """
    statement = select(Monitor).where(Monitor.user_id == current_user.id)
    monitors = session.exec(statement).all()
    return monitors

@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete a monitor
    """
    statement = select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == current_user.id)
    monitor = session.exec(statement).first()
    
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    session.delete(monitor)
    session.commit()
    return None

@router.patch("/{monitor_id}", response_model=MonitorRead)
async def update_monitor(
    monitor_id: int,
    monitor_update: MonitorUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update monitor (e.g., toggle active state)
    """
    statement = select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == current_user.id)
    monitor = session.exec(statement).first()
    
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    monitor_data = monitor_update.model_dump(exclude_unset=True)
    for key, value in monitor_data.items():
        setattr(monitor, key, value)
        
    session.add(monitor)
    session.commit()
    session.refresh(monitor)
    return monitor

@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_check(
    current_user: User = Depends(get_current_user)
):
    """
    Manual trigger for testing (Admin only ideally, but open for now)
    """
    if not current_user.is_superuser:
         raise HTTPException(status_code=403, detail="Admin access required")
    
    await check_monitors()
    return {"status": "Job triggered"}
