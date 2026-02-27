from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_access_token
from app.models.business_user import BusinessUser

bearer_scheme = HTTPBearer(auto_error=False)
ROLE_RANK = {"staff": 1, "admin": 2, "owner": 3}


@dataclass
class CurrentUser:
    user_id: str
    business_id: str
    role: str
    email: str


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})

    user_id: str = payload.get("sub", "")
    business_id: str = payload.get("bid", "")
    role: str = payload.get("role", "")

    if not user_id or not business_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token claims")

    user = await BusinessUser.find_one(
        BusinessUser.id == user_id,
        BusinessUser.business_id == business_id,
        BusinessUser.is_active == True,
        BusinessUser.deleted_at == None,  # noqa: E711
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User account not found or inactive")

    return CurrentUser(user_id=user_id, business_id=business_id, role=role, email=user.email)


def require_role(minimum_role: str):
    async def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_rank = ROLE_RANK.get(current_user.role, 0)
        required_rank = ROLE_RANK.get(minimum_role, 99)
        if user_rank < required_rank:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient permissions")
        return current_user
    return _check


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None