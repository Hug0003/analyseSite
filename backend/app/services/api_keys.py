"""
API Key Service
Handles generation, hashing, and validation of API keys.
"""
import secrets
from typing import Tuple, Optional
from sqlmodel import Session, select
from ..models.api_key import ApiKey
from ..core.security import get_password_hash, verify_password

def generate_api_key() -> str:
    """Generate a secure random API key with prefix"""
    return f"sk_live_{secrets.token_urlsafe(32)}"

def create_api_key(session: Session, user_id: int, name: str) -> Tuple[ApiKey, str]:
    """
    Create a new API key for a user.
    Returns: (ApiKey_db_obj, raw_key_string)
    The raw_key_string is shown ONLY ONCE.
    """
    raw_key = generate_api_key()
    key_hash = get_password_hash(raw_key)
    
    db_obj = ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        prefix=raw_key[:12], # Store prefix for identification (sk_live_xxxx)
        name=name
    )
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    
    return db_obj, raw_key

def get_api_key_by_prefix(session: Session, raw_key: str) -> Optional[ApiKey]:
    """
    Find and validate API key.
    Performance optimization: Search by prefix first, then check hash.
    """
    # Assuming prefix is always sk_live_ + 4 chars or so for lookup, 
    # but since stored prefix length is fixed or semi-fixed, we can try to math it.
    # Our generated keys are "sk_live_" + 32 bytes urlsafe.
    # Stored prefix is first 12 chars: "sk_live_XXXX"
    
    if len(raw_key) < 12:
        return None
        
    prefix = raw_key[:12]
    
    # query all active keys with this prefix (should be very few, ideally 1)
    statement = select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.is_active == True)
    results = session.exec(statement).all()
    
    for key_obj in results:
        if verify_password(raw_key, key_obj.key_hash):
            return key_obj
            
    return None

def update_last_used(session: Session, api_key_id: int):
    """Update the last_used_at timestamp"""
    from datetime import datetime
    key = session.get(ApiKey, api_key_id)
    if key:
        key.last_used_at = datetime.utcnow()
        session.add(key)
        session.commit()
