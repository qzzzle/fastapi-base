"""
Portable settings
- Keep the same field names you already use.
- Remove ENV→DB name mapping so we can reuse this core anywhere.
- Provide a safe CORS list (main.py already expects it).
"""

import os
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Configs(BaseSettings):
    # Which environment we are running in (dev|stage|prod)
    ENV: str = Field(default=os.getenv("ENV", "dev"))

    # API prefixes used across the project
    API: ClassVar[str] = "/api"
    API_V1_STR: ClassVar[str] = "/api/v1"
    API_V2_STR: ClassVar[str] = "/api/v2"

    PROJECT_NAME: ClassVar[str] = "fastapi-base"

    # JWT
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", ""))  # must be set in real deployments
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # DB driver: "postgresql" (psycopg/pg8000/etc) or "mysql" (we use mysql+pymysql)
    DB: str = Field(default=os.getenv("DB", "postgresql"))
    DB_USER: str = Field(default=os.getenv("DB_USER", ""))
    DB_PASSWORD: str = Field(default=os.getenv("DB_PASSWORD", ""))
    DB_HOST: str = Field(default=os.getenv("DB_HOST", "localhost"))
    DB_PORT: str = Field(default=os.getenv("DB_PORT", ""))  # if empty, we infer below
    DB_NAME: str = Field(default=os.getenv("DB_NAME", "app"))  # portable: use explicit DB_NAME

    # CORS (main.py references this already)
    # Keep it simple: an optional comma-separated list, split into a list at runtime.
    BACKEND_CORS_ORIGINS: str = Field(default=os.getenv("BACKEND_CORS_ORIGINS", ""))

    class Config:
        env_file = ".env"

    @property
    def BACKEND_CORS_ORIGINS(self) -> list[str]:
        # Why: main.py expects a list; keep it forgiving for env values
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS_RAW.split(",") if o.strip()]

    @property
    def DB_ENGINE(self) -> str:
        # Why: minimal mapping without extra settings
        return "mysql+pymysql" if self.DB.lower().startswith("mysql") else "postgresql"

    @property
    def EFFECTIVE_DB_PORT(self) -> str:
        # Why: pick a sensible default if not provided; no new settings added
        if self.DB_PORT:
            return self.DB_PORT
        return "3306" if self.DB_ENGINE.startswith("mysql") else "5432"

    @property
    def DATABASE_URI(self) -> str:
        # Why: one canonical DSN used everywhere
        return f"{self.DB_ENGINE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.EFFECTIVE_DB_PORT}/{self.DB_NAME}"


configs = Configs()

# Optional startup sanity check (kept tiny, no extra settings):
if not configs.SECRET_KEY:
    # Reason: prevent accidental insecure deployments
    # Keep it a warning (print) instead of raising to stay minimally invasive.
    print("[config] WARNING: SECRET_KEY is empty. Set SECRET_KEY in .env for production.")
