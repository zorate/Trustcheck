import os
from pydantic import BaseModel, Field, ValidationError
from typing import Optional


class Settings(BaseModel):
    app_name: str = "TrustCheck"
    environment: str = Field(default="production", pattern="^(development|staging|production)$")
    debug: bool = False

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_exp_minutes: int = 30
    jwt_refresh_exp_minutes: int = 60 * 24 * 14  # 14 days

    password_hash_scheme: str = "bcrypt"
    rate_limit_requests_per_minute: int = 60

    # Security toggles
    enforce_tenant_isolation: bool = True
    phone_hash_salt: str

    # CORS
    cors_origins: Optional[str] = "*"

    class Config:
        extra = "ignore"


def get_settings() -> Settings:
    try:
        return Settings(
            app_name=os.getenv("APP_NAME", "TrustCheck"),
            environment=os.getenv("ENVIRONMENT", "production"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            database_url=os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/trust"),
            jwt_secret=os.getenv("JWT_SECRET", "change-this-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_access_exp_minutes=int(os.getenv("JWT_ACCESS_EXP_MINUTES", "30")),
            jwt_refresh_exp_minutes=int(os.getenv("JWT_REFRESH_EXP_MINUTES", str(60 * 24 * 14))),
            password_hash_scheme=os.getenv("PASSWORD_HASH_SCHEME", "bcrypt"),
            rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
            enforce_tenant_isolation=os.getenv("ENFORCE_TENANT_ISOLATION", "true").lower() == "true",
            phone_hash_salt=os.getenv("PHONE_HASH_SALT", "replace-with-strong-salt"),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
        )
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}")
