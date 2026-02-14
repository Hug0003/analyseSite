from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.models.api_key import ApiKey, ApiKeyCreate, ApiKeyRead, ApiKeyCreated
from app.deps import get_current_user
from app.core.permissions import FeatureGuard
import secrets
import hashlib

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])

@router.get("", response_model=list[ApiKeyRead])
def list_keys(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    keys = session.exec(select(ApiKey).where(ApiKey.user_id == current_user.id)).all()
    return keys

@router.post("", response_model=ApiKeyCreated)
def create_key(
    key_in: ApiKeyCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not FeatureGuard.can_perform_action(current_user, "api_access"):
        raise HTTPException(status_code=403, detail="API access is restricted to Agency plan.")
    
    # Generate key
    raw_key = "sk_" + secrets.token_urlsafe(32)
    # Prefix for UI
    prefix = raw_key[:8]
    # Hash
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=current_user.id,
        name=key_in.name,
        prefix=prefix,
        hashed_key=hashed_key
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    return ApiKeyCreated(
        **api_key.model_dump(),
        key=raw_key # Return full key only here
    )

@router.delete("/{key_id}")
def delete_key(
    key_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    key = session.get(ApiKey, key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    session.delete(key)
    session.commit()
    return {"ok": True}
