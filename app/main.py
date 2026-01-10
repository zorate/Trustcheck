import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.middleware.audit import AuditMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.business import router as business_router
from app.api.v1.users import router as users_router
from app.api.v1.persons import router as persons_router
from app.api.v1.payments import router as payments_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.system import router as system_router

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origins] if isinstance(settings.cors_origins, str) else settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)

app.include_router(auth_router)
app.include_router(business_router)
app.include_router(users_router)
app.include_router(persons_router)
app.include_router(payments_router)
app.include_router(scoring_router)
app.include_router(system_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
