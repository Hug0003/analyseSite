"""
Monitor Model - SQLModel ORM
Defines the Monitor table for the Watchdog feature
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import Field, SQLModel

class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"

class Monitor(SQLModel, table=True):
    """Monitor model for persistent URL watching"""
    __tablename__ = "monitors"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    url: str = Field(max_length=2048)
    frequency: Frequency = Field(default=Frequency.DAILY)
    is_active: bool = Field(default=True)
    last_score: Optional[int] = Field(default=None)
    threshold: int = Field(default=80)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked_at: Optional[datetime] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "frequency": "daily",
                "threshold": 80
            }
        }

class MonitorCreate(SQLModel):
    """Schema for creating a new monitor"""
    url: str = Field(max_length=2048)
    frequency: Frequency = Field(default=Frequency.DAILY)
    threshold: int = Field(default=80, ge=0, le=100)

class MonitorRead(SQLModel):
    """Schema for reading monitor data"""
    id: int
    user_id: int
    url: str
    frequency: Frequency
    is_active: bool
    last_score: Optional[int]
    threshold: int
    created_at: datetime
    last_checked_at: Optional[datetime]

class MonitorUpdate(SQLModel):
    """Schema for updating monitor"""
    is_active: Optional[bool] = None
    frequency: Optional[Frequency] = None
    threshold: Optional[int] = None
