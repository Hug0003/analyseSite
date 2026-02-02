"""
Lead Model
Tracks leads generated via the external widget.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Lead(SQLModel, table=True):
    """Lead captured from Agency Widget"""
    __tablename__ = "leads"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    agency_id: int = Field(foreign_key="users.id", index=True)
    
    prospect_email: str = Field(index=True)
    prospect_url: str
    scan_score: int
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="new") # new, contacted, converted
