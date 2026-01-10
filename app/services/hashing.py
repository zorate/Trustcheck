import hmac
import hashlib
from app.core.config import get_settings

settings = get_settings()

def hash_phone(phone: str) -> str:
    # Normalize phone: remove spaces, dashes, leading zeros handling is business-specific; keep simple
    normalized = "".join(ch for ch in phone if ch.isdigit())
    return hmac.new(settings.phone_hash_salt.encode("utf-8"), normalized.encode("utf-8"), hashlib.sha256).hexdigest()
