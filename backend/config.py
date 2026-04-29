import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = int(os.environ.get("DB_PORT", "5432"))
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

    CORS_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "*").split(",")
        if o.strip()
    ]

    PORT = int(os.environ.get("PORT", "8000"))
    DEBUG = os.environ.get("FLASK_ENV", "production") == "development"

    POOL_MIN = int(os.environ.get("DB_POOL_MIN", "1"))
    POOL_MAX = int(os.environ.get("DB_POOL_MAX", "10"))

    @staticmethod
    def validate():
        required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        missing = [k for k in required if not os.environ.get(k)]

        if missing:
            raise Exception(f"Missing env variables: {missing}")