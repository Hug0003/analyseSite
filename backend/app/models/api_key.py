from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from .user import User

class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    prefix: str = Field(max_length=10)
    hashed_key: str = Field(max_length=128, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)

class ApiKeyCreate(SQLModel):
    name: str = Field(min_length=1, max_length=50)

class ApiKeyRead(SQLModel):
    id: int
    name: str
    prefix: str
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

class ApiKeyCreated(ApiKeyRead):
    key: str  # The full key, returned only once
