from fastapi import Request, HTTPException, status

async def enforce_business_scope(request: Request, resource_business_id: str):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token_bid = user.get("bid")
    if not token_bid or str(token_bid) != str(resource_business_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access denied")
