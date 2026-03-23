from fastapi import FastAPI
from app.routers import packing, health
from app.config import settings
import logging

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Weather Packing Advisor",
    description="Микросервис для формирования списка вещей на основе прогноза погоды",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Подключаем роутеры
app.include_router(packing.router, prefix="/api/v1", tags=["Packing"])
app.include_router(health.router, prefix="/api/v1", tags=["System"])

@app.get("/")
async def root():
    """
    Корневой эндпоинт для проверки работы сервиса
    """
    return {
        "message": "Weather Packing Service is running",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "POST /api/v1/packing-advice": "Получить советы по упаковке вещей",
            "GET /api/v1/health": "Проверка работоспособности сервиса",
            "GET /api/v1/cache/{airport_code}": "Просмотр кэша (отладка)",
            "DELETE /api/v1/cache/{airport_code}": "Очистка кэша (отладка)"
        }
    }

@app.on_event("startup")
async def startup_event():
    """
    Действия при запуске приложения
    """
    logger.info("=" * 50)
    logger.info("Weather Packing Service запускается...")
    logger.info(f"Режим: {settings.APP_ENV}")
    logger.info(f"MongoDB: {settings.MONGODB_URL}")
    logger.info(f"Cities API: {settings.CITIES_API_BASE_URL}")
    logger.info(f"Weather API: {settings.WEATHER_API_BASE_URL}")
    logger.info(f"Cache TTL: {settings.CACHE_TTL_HOURS} часов")
    logger.info("=" * 50)

    logger.info("Зарегистрированные маршруты:")
    for route in app.routes:
        methods = ",".join(route.methods) if hasattr(route, "methods") else "ANY"
        logger.info(f"  {route.path} [{methods}]")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Действия при остановке приложения
    """
    logger.info("Weather Packing Service останавливается...")

# Обработчики ошибок
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, status

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    errors = []
    for error in exc.errors():
        errors.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Ошибка валидации: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Ошибка валидации входных данных",
            "errors": errors
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):

    logger.error(f"Необработанная ошибка: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Внутренняя ошибка сервера",
            "message": str(exc) if settings.APP_ENV == "development" else None
        }
    )