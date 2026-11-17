import os

from dotenv import load_dotenv

load_dotenv()


def _database_url():
    url = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def _csv_env(name, default):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


class Config:
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    CORS_ORIGINS = _csv_env(
        "CORS_ORIGINS",
        "https://notsting.github.io,http://localhost:5173,http://127.0.0.1:5173",
    )
    AI_RATE_LIMIT = os.environ.get("AI_RATE_LIMIT", "10 per hour")
