from fastapi import APIRouter, Depends
from app.models.response import HealthCheckResponse
from app.repositories.cache_repository import CacheRepository
from app.services.cities_client import CitiesClient
from app.services.weather_client import WeatherClient
from datetime import date, timedelta
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def check_mongodb() -> str:
    """Проверка подключения к MongoDB"""
    repo = CacheRepository()
    try:
        await repo.initialize()
        if await repo.check_connection():
            return "connected"
        return "disconnected"
    except Exception as e:
        logger.error(f"Ошибка при проверке MongoDB: {e}")
        return "error"
    finally:
        await repo.close()

async def check_cities_api() -> str:
    """Проверка доступности Cities API"""
    client = CitiesClient()
    try:
        await client.get_city_by_airport("LHR")
        return "ok"
    except Exception as e:
        logger.error(f"Ошибка Cities API: {e}")
        return "unavailable"
    finally:
        await client.close()

async def check_weather_api() -> str:
    """Проверка доступности Weather API"""
    client = WeatherClient()
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)

        await client.get_forecast(51.5074, -0.1278, today, tomorrow)
        return "ok"
    except Exception as e:
        logger.error(f"Ошибка Weather API: {e}")
        return "unavailable"
    finally:
        await client.close()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():

    mongodb_status = await check_mongodb()
    cities_api_status = await check_cities_api()
    weather_api_status = await check_weather_api()

    overall_status = "ok"
    if mongodb_status != "connected" or cities_api_status != "ok" or weather_api_status != "ok":
        overall_status = "degraded"

    return HealthCheckResponse(
        status=overall_status,
        mongodb=mongodb_status,
        cities_api=cities_api_status,
        weather_api=weather_api_status
    )