from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional

class Period(BaseModel):

    arrival: date
    # Используем alias 'return' для сериализации в JSON,
    # но в коде используем return_date для избежания конфликта с зарезервированным словом
    return_date: date = Field(..., alias="return", description="Дата возвращения")

    class Config:
        # Позволяет принимать как по алиасу (return), так и по имени поля (return_date)
        populate_by_name = True
        # Пример JSON схемы для документации
        json_schema_extra = {
            "example": {
                "arrival": "2024-03-15",
                "return": "2024-03-22"
            }
        }

class WeatherSummary(BaseModel):

    temperature_min: float = Field(..., description="Минимальная температура за период, °C")
    temperature_max: float = Field(..., description="Максимальная температура за период, °C")
    conditions: List[str] = Field(..., description="Список погодных условий (ясно, дождь, снег и т.д.)")
    will_rain: bool = Field(..., description="Будет ли дождь")
    will_snow: bool = Field(..., description="Будет ли снег")
    strong_wind: bool = Field(..., description="Будет ли сильный ветер (>40 км/ч)")

    class Config:
        json_schema_extra = {
            "example": {
                "temperature_min": 6.2,
                "temperature_max": 13.8,
                "conditions": ["rain", "partly_cloudy"],
                "will_rain": True,
                "will_snow": False,
                "strong_wind": False
            }
        }

class PackingAdvice(BaseModel):

    essentials: List[str] = Field(..., description="Обязательно взять с собой")
    recommended: List[str] = Field(..., description="Рекомендуется взять")
    optional: List[str] = Field(..., description="Можно взять по желанию")

    class Config:
        json_schema_extra = {
            "example": {
                "essentials": [
                    "Зонт или дождевик — ожидаются дожди",
                    "Тёплая куртка или пальто — температура 6–14°C"
                ],
                "recommended": [
                    "Водонепроницаемая обувь",
                    "Свитер или джемпер — прохладная погода"
                ],
                "optional": [
                    "Лёгкий пуловер на случай прохладных вечеров"
                ]
            }
        }

class PackingResponse(BaseModel):

    airport_code: str = Field(..., description="IATA код аэропорта назначения")
    city: str = Field(..., description="Название города")
    country: str = Field(..., description="Название страны")
    period: Period = Field(..., description="Период поездки")
    weather_summary: WeatherSummary = Field(..., description="Сводка погоды")
    packing_advice: PackingAdvice = Field(..., description="Советы по упаковке")
    cached: bool = Field(False, description="Был ли ответ получен из кэша")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Время генерации ответа")

    class Config:
        json_schema_extra = {
            "example": {
                "airport_code": "LHR",
                "city": "London",
                "country": "United Kingdom",
                "period": {
                    "arrival": "2024-03-15",
                    "return": "2024-03-22"
                },
                "weather_summary": {
                    "temperature_min": 6.2,
                    "temperature_max": 13.8,
                    "conditions": ["rain", "partly_cloudy"],
                    "will_rain": True,
                    "will_snow": False,
                    "strong_wind": False
                },
                "packing_advice": {
                    "essentials": [
                        "Зонт или дождевик — ожидаются дожди",
                        "Тёплая куртка или пальто — температура 6–14°C"
                    ],
                    "recommended": [
                        "Водонепроницаемая обувь",
                        "Свитер или джемпер — прохладная погода"
                    ],
                    "optional": []
                },
                "cached": False,
                "generated_at": "2024-03-10T12:00:00Z"
            }
        }

class HealthCheckResponse(BaseModel):

    status: str = Field("ok", description="Статус сервиса (ok/degraded)")
    mongodb: str = Field(..., description="Статус подключения к MongoDB")
    cities_api: str = Field(..., description="Статус доступности Cities API")
    weather_api: str = Field(..., description="Статус доступности Weather API")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "mongodb": "connected",
                "cities_api": "ok",
                "weather_api": "ok"
            }
        }