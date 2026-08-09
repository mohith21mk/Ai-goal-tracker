import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load backend/.env file
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    APP_NAME: str = "AI Goal Coach API"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


settings = Settings()
