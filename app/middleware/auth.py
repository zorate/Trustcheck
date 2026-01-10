from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from typing import Optional

bearer = HTTPBearer(auto_error=False)

async def get_current_user(request: Request) -> dict:
    credentials: Optional[HTTPAuthorizationCredentials] = await bearer(request)
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    request.state.user = payload
    return payload

def require_scope(required: str):
    async def dependency(request: Request):
        user = await get_current_user(request)
        scopes = user.get("scp", [])
        if required not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return user
    return dependency
