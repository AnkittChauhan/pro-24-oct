import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "UK Wind Day-Ahead Forecast Platform"
    API_V1_STR: str = "/api/v1"
    
    # CORS Origins (allow frontend dev and production origins)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]

    # Elexon BMRS Configuration
    ELEXON_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
    ELEXON_TIMEOUT_SECONDS: float = 20.0
    
    # SQLite Cache Path
    DB_PATH: str = os.getenv("DB_PATH", "data/cache.db")
    
    # Target Evaluation Period
    DEFAULT_DECISION_MONTH: str = "2026-01"

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
