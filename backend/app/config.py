import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
# Explicitly load secrets from backend/.env only.
load_dotenv(BACKEND_ROOT / ".env", override=False)


@dataclass
class Settings:
    BASE_DIR: Path = Path(__file__).resolve().parents[1]
    DEBUG: bool = os.getenv("FLASK_ENV", "development") == "development"
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    DB_PATH: str = os.getenv("DB_PATH", "./data/jobmatch.db")
    MAX_AGENT_ITERATIONS: int = int(os.getenv("MAX_AGENT_ITERATIONS", "8"))

    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    @property
    def resolved_db_path(self) -> Path:
        db_path = Path(self.DB_PATH)
        if not db_path.is_absolute():
            db_path = (self.BASE_DIR / db_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path
