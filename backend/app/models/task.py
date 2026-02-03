from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from datetime import datetime
from .schemas import AuditStatus

class ScanTask(SQLModel, table=True):
    """
    Model to track background scan tasks.
    """
    id: str = Field(primary_key=True)  # UUID string
    status: AuditStatus = Field(default=AuditStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    url: str
    
    # Store the full AnalyzeResponse as JSON
    # using sa_column=Column(JSON) acts as a generic JSON field
    result: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    error: Optional[str] = None
