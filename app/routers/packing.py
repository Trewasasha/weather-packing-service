from fastapi import APIRouter, HTTPException, status, Depends
from app.models.request import PackingRequest
from app.models.response import PackingResponse, Period, WeatherSummary, PackingAdvice
from app.services.cities_client import CitiesClient
from app.services.weather_client import WeatherClient
from app.services.advice_engine import AdviceEngine
from app.repositories.cache_repository import CacheRepository
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_cities_client():
    """Dependency для получения клиента Cities API"""
    client = CitiesClient()
    try:
        yield client
    finally:
        await client.close()


async def get_weather_client():
    """Dependency для получения клиента Weather API"""
    client = WeatherClient()
    try:
        yield client
    finally:
        await client.close()


async def get_cache_repository():
    """Dependency для получения репозитория кэша"""
    repo = CacheRepository()
    await repo.initialize()
    try:
        yield repo
    finally:
        await repo.close()


@router.post("/packing-advice", response_model=PackingResponse)
async def get_packing_advice(
        request: PackingRequest,
        cities_client: CitiesClient = Depends(get_cities_client),
        weather_client: WeatherClient = Depends(get_weather_client),
        cache_repo: CacheRepository = Depends(get_cache_repository)
):


    try:
        # Проверяем кэш
        arrival_str = request.arrival_date.isoformat()
        return_str = request.return_date.isoformat() if request.return_date else None

        cached_response = await cache_repo.get_cached_advice(
            request.airport_code,
            arrival_str,
            return_str
        )

        if cached_response:
            logger.info(f"Возвращен кэшированный ответ для {request.airport_code}")
            cached_response["cached"] = True
            return cached_response

        # Информация о городе
        city_info = await cities_client.get_city_by_airport(request.airport_code)
        if not city_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Аэропорт с кодом {request.airport_code} не найден"
            )

        start_date = request.arrival_date
        end_date = request.return_date if request.return_date else request.arrival_date

        # Получаем прогноз погоды
        weather_data = await weather_client.get_forecast(
            city_info["latitude"],
            city_info["longitude"],
            start_date,
            end_date
        )

        if not weather_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Не удалось получить данные о погоде"
            )

        # Анализируем погоду
        engine = AdviceEngine()

        try:
            weather_summary = engine.analyze_weather(weather_data)
        except ValueError as e:
            logger.error(f"Ошибка валидации данных погоды: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Некорректные данные о погоде от внешнего сервиса"
            )

        # Генерируем советы
        packing_advice = engine.generate_packing_advice(weather_summary)

        # Формируем ответ
        response = PackingResponse(
            airport_code=request.airport_code,
            city=city_info["city"],
            country=city_info["country"],
            period=Period(
                arrival=request.arrival_date,
                return_date=request.return_date if request.return_date else request.arrival_date
            ),
            weather_summary=WeatherSummary(**weather_summary),
            packing_advice=PackingAdvice(**packing_advice),
            cached=False,
            generated_at=datetime.now(timezone.utc)
        )

        # Преобразуем в словарь для сохранения в кэш (mode='json' преобразует даты в строки)
        response_dict = response.model_dump(mode='json')

        # Сохраняем в кэш (ошибки не должны прерывать выполнение)
        try:
            await cache_repo.save_advice(
                request.airport_code,
                arrival_str,
                return_str,
                city_info,
                weather_data,
                response_dict
            )
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш: {e}")
            # Не пробрасываем исключение, просто логируем

        logger.info(f"Успешно сгенерирован совет для {request.airport_code}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Внешний сервис временно недоступен"
        )


@router.get("/cache/{airport_code}")
async def get_cache_by_airport(
        airport_code: str,
        cache_repo: CacheRepository = Depends(get_cache_repository)
):

    cache_entries = await cache_repo.get_cache_by_airport(airport_code.upper())
    return {
        "airport_code": airport_code.upper(),
        "cache_entries": cache_entries,
        "count": len(cache_entries)
    }


@router.delete("/cache/{airport_code}")
async def delete_cache_by_airport(
        airport_code: str,
        cache_repo: CacheRepository = Depends(get_cache_repository)
):

    deleted_count = await cache_repo.delete_cache_by_airport(airport_code.upper())
    return {
        "message": f"Удалено {deleted_count} записей кэша для аэропорта {airport_code.upper()}",
        "deleted_count": deleted_count
    }