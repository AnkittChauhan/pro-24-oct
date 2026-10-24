from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from app.services.cache_service import cache_service

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    service: str
    cache_stats: dict

@router.get("", response_model=HealthResponse)
async def check_health():
    stats = cache_service.get_cache_stats()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        service="UK Wind Day-Ahead Forecast Engine",
        cache_stats=stats
    )
