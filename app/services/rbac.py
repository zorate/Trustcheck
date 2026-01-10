from fastapi import HTTPException, status

def ensure_admin(user_payload: dict):
    scopes = user_payload.get("scp", [])
    if "admin" not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
