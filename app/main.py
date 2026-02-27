import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.database import close_db, connect_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import RequestIDMiddleware, SecurityHeadersMiddleware
from app.utils.exceptions import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TrustCheck %s starting up [env=%s]", settings.APP_VERSION, settings.ENVIRONMENT)
    await connect_db()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down TrustCheck")
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="TrustCheck",
        description=(
            "Behaviour-based payment trust scoring for SMEs, landlords, "
            "cooperatives, and B2B vendors.\n\n"
            "**This system is NOT a credit bureau.** "
            "It uses only data entered by businesses and observed payment behaviour."
        ),
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware, per_minute=settings.RATE_LIMIT_PER_MINUTE)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    register_exception_handlers(app)
    app.include_router(v1_router)

    return app


app = create_app()