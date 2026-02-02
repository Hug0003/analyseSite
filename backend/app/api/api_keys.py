from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session, select
from ..database import get_session
from ..models.user import User
from ..api.auth import get_current_user
from ..models.api_key import ApiKey
from ..services.api_keys import create_api_key

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])

from pydantic import BaseModel
from datetime import datetime

# --- Schemas ---

class ApiKeyRead(BaseModel):
    id: int
    prefix: str
    name: str
    created_at: datetime
    last_used_at: datetime | None = None
    is_active: bool

class ApiKeyCreateRequest(BaseModel):
    name: str

class ApiKeyCreateResponse(BaseModel):
    id: int
    name: str
    prefix: str
    key: str # The raw key, shown only once!
    created_at: datetime

# --- Endpoints ---

@router.get("/", response_model=List[ApiKeyRead])
async def list_api_keys(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List all active API keys for the current user"""
    statement = select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)
    keys = session.exec(statement).all()
    return keys

@router.post("/", response_model=ApiKeyCreateResponse)
async def create_new_api_key(
    request: ApiKeyCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Generate a new API Key. The raw key is returned only once."""
    db_obj, raw_key = create_api_key(session, current_user.id, request.name)
    
    return ApiKeyCreateResponse(
        id=db_obj.id,
        name=db_obj.name,
        prefix=db_obj.prefix,
        key=raw_key,
        created_at=db_obj.created_at
    )

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Revoke (delete) an API Key"""
    key = session.get(ApiKey, key_id)
    if not key or key.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="API Key not found")
    
    session.delete(key)
    session.commit()
    return None
