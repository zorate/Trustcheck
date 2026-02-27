from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "TrustCheck"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PHONE_HASH_SALT: str
    BCRYPT_ROUNDS: int = 12

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "trustcheck"

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_long(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("PHONE_HASH_SALT")
    @classmethod
    def salt_must_be_long(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("PHONE_HASH_SALT must be at least 16 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()