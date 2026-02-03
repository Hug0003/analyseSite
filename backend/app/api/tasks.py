from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Dict, Any

from ..database import get_session
from ..models.task import ScanTask
from ..models import AnalyzeResponse

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task_status(task_id: str, session: Session = Depends(get_session)):
    """
    Get the status and result of a background scan task.
    """
    task = session.get(ScanTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = {
        "id": task.id,
        "status": task.status,
        "created_at": task.created_at,
        "finished_at": task.finished_at,
        "url": task.url,
    }
    
    if task.result:
        response["result"] = task.result
        
    if task.error:
        response["error"] = task.error
        
    return response
