from fastapi import APIRouter
from app.api.v1 import health, day_ahead

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(day_ahead.router, tags=["day-ahead"])

