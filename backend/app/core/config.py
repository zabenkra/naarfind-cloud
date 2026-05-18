import os
from pathlib import Path

from dotenv import load_dotenv

# backend/app/core/config.py -> parents[2] = backend root (/app in Docker)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_ROOT.parent

for _env_file in (_PROJECT_ROOT / ".env", _BACKEND_ROOT / ".env"):
    if _env_file.is_file():
        load_dotenv(_env_file, override=False)

ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()
IS_PRODUCTION: bool = ENVIRONMENT == "production"


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return normalize_database_url(url)
    if IS_PRODUCTION:
        raise RuntimeError("DATABASE_URL is required in production")
    return "postgresql://naarfind:naarfind123@db:5432/naarfind"


DATABASE_URL: str = _database_url()

# --- JWT (single source of truth for all encode/decode) ---
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-development").strip()
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256").strip()
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_int(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    _get_int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 1440),
)

FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")

R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "").strip()
R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
R2_BUCKET: str = os.getenv("R2_BUCKET", "").strip()
R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "").strip().rstrip("/")
ALLOWED_MEDIA_URL_PREFIXES: str = os.getenv("ALLOWED_MEDIA_URL_PREFIXES", "").strip()

PORT: int = _get_int("PORT", 8000)


def cors_origins() -> list[str]:
    origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    if FRONTEND_URL:
        origins.add(FRONTEND_URL)
        if FRONTEND_URL.startswith("https://"):
            origins.add(FRONTEND_URL.replace("https://", "http://", 1))
    extra = os.getenv("CORS_ORIGINS", "").strip()
    if extra:
        for origin in extra.split(","):
            origin = origin.strip().rstrip("/")
            if origin:
                origins.add(origin)
    return sorted(origins)


def validate_production_settings() -> None:
    if not IS_PRODUCTION:
        return
    if not JWT_SECRET_KEY or JWT_SECRET_KEY in (
        "change-me",
        "change-me-in-development",
        "change-me-to-a-long-random-secret",
    ):
        raise RuntimeError("Set a strong JWT_SECRET_KEY in production")
    if not FRONTEND_URL or FRONTEND_URL.startswith("http://localhost"):
        raise RuntimeError("Set FRONTEND_URL to your Vercel URL in production")
