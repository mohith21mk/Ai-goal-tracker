import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load backend/.env file
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    APP_NAME: str = "AI Goal Coach API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    DEBUG: bool = os.getenv("DEBUG", "False" if os.getenv("ENVIRONMENT") == "production" else "True").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{(Path(__file__).resolve().parent / 'app.db').as_posix()}")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    # Frontend URL for CORS and links
    FRONTEND_URL: str = os.getenv("FRONTEND_URL") or os.getenv("APP_FRONTEND_URL") or "http://localhost:5173"
    APP_FRONTEND_URL: str = FRONTEND_URL.rstrip("/")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    
    cors_env = os.getenv("CORS_ORIGINS") or os.getenv("ALLOWED_ORIGINS")
    configured_origins = [origin.strip().rstrip("/") for origin in cors_env.split(",") if origin.strip()] if cors_env else []
    
    default_dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        APP_FRONTEND_URL,
    ]
    
    if ENVIRONMENT == "production" and configured_origins:
        ALLOWED_ORIGINS: list[str] = list(dict.fromkeys(configured_origins))
    else:
        ALLOWED_ORIGINS: list[str] = list(dict.fromkeys(configured_origins + default_dev_origins))

    # Security & Cookie Session Configurations
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "True" if ENVIRONMENT == "production" else "False").lower() == "true"
    SESSION_COOKIE_SAMESITE: str = os.getenv("SESSION_COOKIE_SAMESITE", "none" if ENVIRONMENT == "production" else "lax")

    # SMTP Production Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@masterykeycoach.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Mastery Key Coach")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"


settings = Settings()

# Production safety checks
if settings.ENVIRONMENT == "production":
    _unsafe_keys = {"fallback-secret-key-change-in-production", "change_this_to_a_secure_random_64_char_secret_key", ""}
    if settings.SECRET_KEY in _unsafe_keys:
        raise RuntimeError(
            "FATAL: SECRET_KEY is not set or uses an unsafe default. "
            "Set a secure random SECRET_KEY environment variable for production."
        )

