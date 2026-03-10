from fastapi import FastAPI
from app.routers import packing, health
from app.config import settings

app = FastAPI(
    title="Weather Packing Advisor",
    description="Микросервис для формирования списка вещей на основе прогноза погоды",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Подключаем роутеры из структуры
app.include_router(packing.router, prefix="/api/v1", tags=["Packing"])
app.include_router(health.router, prefix="/api/v1", tags=["System"])

@app.get("/")
async def root():
    return {"message": "Weather Packing Service is running. Go to /docs for API documentation."}