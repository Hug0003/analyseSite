"""
ApiKey Model
Defines the structure for API Keys used in CI/CD pipelines.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

class ApiKey(SQLModel, table=True):
    """API Key model for machine-to-machine authentication"""
    __tablename__ = "api_keys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Security: Only store hash, never the actual key (except on creation response)
    key_hash: str = Field(index=True)
    
    # Metadata for display
    name: str = Field(max_length=100)  # e.g. "GitHub Actions", "My Laptop"
    prefix: str = Field(max_length=10)  # e.g. "sk_live_..."
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)   
    
    # Relationship likely defined in User too, but we keep it specialized here
    # user: Optional["User"] = Relationship(back_populates="api_keys")
