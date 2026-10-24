import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

_project_root = Path(__file__).resolve().parents[3]
_default_db = str(_project_root / "data" / "cache.db")

class Settings(BaseSettings):
    PROJECT_NAME: str = "UK Wind Day-Ahead Forecast Platform"
    API_V1_STR: str = "/api/v1"
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]

    ELEXON_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
    ELEXON_TIMEOUT_SECONDS: float = 20.0
    
    DB_PATH: str = os.getenv("DB_PATH", _default_db)
    DEFAULT_DECISION_MONTH: str = "2026-01"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )

settings = Settings()
