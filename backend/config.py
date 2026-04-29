"""Centralised configuration. Reads from environment variables (.env locally,
EB env vars in production)."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "5432"))
    DB_NAME = os.environ.get("DB_NAME", "ecotech")
    DB_USER = os.environ.get("DB_USER", "ecotech_user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "change_me")

    CORS_ORIGINS = [
        o.strip()
        for o in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if o.strip()
    ]

    PORT = int(os.environ.get("PORT", "8000"))
    DEBUG = os.environ.get("FLASK_ENV", "production") == "development"

    POOL_MIN = int(os.environ.get("DB_POOL_MIN", "1"))
    POOL_MAX = int(os.environ.get("DB_POOL_MAX", "10"))
