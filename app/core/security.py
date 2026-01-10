import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(
    schemes=[settings.password_hash_scheme],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_token(subject: str, business_id: Optional[str], scopes: list[str], expires_minutes: int, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "bid": business_id,
        "scp": scopes,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "typ": token_type,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

def create_access_token(user_id: str, business_id: str, scopes: list[str]) -> str:
    return create_token(user_id, business_id, scopes, settings.jwt_access_exp_minutes, "access")

def create_refresh_token(user_id: str, business_id: str, scopes: list[str]) -> str:
    return create_token(user_id, business_id, scopes, settings.jwt_refresh_exp_minutes, "refresh")
