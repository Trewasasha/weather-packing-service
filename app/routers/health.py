from fastapi import APIRouter
from app.models.response import HealthCheckResponse

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    # Позже здесь будет реальная проверка MongoDB и внешних API
    return {
        "status": "ok",
        "mongodb": "pending",
        "cities_api": "pending",
        "weather_api": "pending"
    }