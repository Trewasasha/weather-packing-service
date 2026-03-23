from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, timedelta
import random

# Создаем FastAPI приложение для заглушки
mock_app = FastAPI(title="Weather API Mock", version="1.0.0")

mock_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Предопределенные погодные сценарии для разных городов
WEATHER_SCENARIOS = {
    # Лондон
    "LHR": {
        "name": "London",
        "base_temp_min": 5,
        "base_temp_max": 15,
        "rain_probability": 0.8,
        "windy_probability": 0.3,
        "snow_probability": 0.1
    },
    # Дубай
    "DXB": {
        "name": "Dubai",
        "base_temp_min": 25,
        "base_temp_max": 35,
        "rain_probability": 0.05,
        "windy_probability": 0.2,
        "snow_probability": 0.0
    },
    # Москва
    "SVO": {
        "name": "Moscow",
        "base_temp_min": -10,
        "base_temp_max": 0,
        "rain_probability": 0.3,
        "windy_probability": 0.4,
        "snow_probability": 0.7
    },
    # Нью-Йорк
    "JFK": {
        "name": "New York",
        "base_temp_min": 0,
        "base_temp_max": 25,
        "rain_probability": 0.5,
        "windy_probability": 0.3,
        "snow_probability": 0.2
    },
    # Париж
    "CDG": {
        "name": "Paris",
        "base_temp_min": 5,
        "base_temp_max": 20,
        "rain_probability": 0.6,
        "windy_probability": 0.2,
        "snow_probability": 0.1
    }
}

# Коды погоды WMO
WMO_CODES = {
    "clear": 0,
    "partly_cloudy": 2,
    "cloudy": 3,
    "fog": 45,
    "drizzle": 51,
    "rain": 61,
    "snow": 71,
    "showers": 80,
    "thunderstorm": 95
}

def get_weather_code(rain: bool, snow: bool, cloudy: bool = True) -> int:
    """Определение кода погоды на основе условий"""
    if snow:
        return WMO_CODES["snow"]
    elif rain:
        return WMO_CODES["rain"]
    elif cloudy:
        return WMO_CODES["cloudy"]
    else:
        return WMO_CODES["clear"]

@mock_app.get("/v1/forecast")
async def get_forecast(
        latitude: float = Query(...),
        longitude: float = Query(...),
        daily: str = Query(...),
        start_date: str = Query(...),
        end_date: str = Query(...),
        timezone: str = Query("auto")
):
    """
    Mock эндпоинт для получения прогноза погоды
    """
    # Определяем город по координатам (упрощенно)
    city_key = "LHR"  # По умолчанию
    if abs(latitude - 25.2532) < 1 and abs(longitude - 55.3657) < 1:
        city_key = "DXB"
    elif abs(latitude - 55.9721) < 1 and abs(longitude - 37.4146) < 1:
        city_key = "SVO"
    elif abs(latitude - 40.6413) < 1 and abs(longitude - -73.7781) < 1:
        city_key = "JFK"
    elif abs(latitude - 49.0097) < 1 and abs(longitude - 2.5479) < 1:
        city_key = "CDG"

    scenario = WEATHER_SCENARIOS.get(city_key, WEATHER_SCENARIOS["LHR"])

    # Парсим даты
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    days_count = (end - start).days + 1

    # Генерируем данные для каждого дня
    dates = []
    temp_max = []
    temp_min = []
    precip = []
    wind = []
    weather_codes = []

    for i in range(days_count):
        current_date = start + timedelta(days=i)
        dates.append(current_date.strftime("%Y-%m-%d"))

        # Генерируем температуру с небольшими вариациями
        base_min = scenario["base_temp_min"]
        base_max = scenario["base_temp_max"]

        t_min = base_min + random.uniform(-2, 2)
        t_max = base_max + random.uniform(-2, 2)
        temp_min.append(round(t_min, 1))
        temp_max.append(round(t_max, 1))

        # Осадки
        rain = random.random() < scenario["rain_probability"]
        snow = random.random() < scenario["snow_probability"]

        precip.append(round(random.uniform(0, 10) if rain or snow else 0, 1))

        # Ветер
        wind_speed = random.uniform(10, 50) if random.random() < scenario["windy_probability"] else random.uniform(0, 20)
        wind.append(round(wind_speed, 1))

        # Код погоды
        weather_codes.append(get_weather_code(rain, snow))

    # Формируем ответ в формате Open-Meteo
    response = {
        "latitude": latitude,
        "longitude": longitude,
        "generationtime_ms": random.uniform(0.1, 0.3),
        "utc_offset_seconds": 0,
        "timezone": timezone,
        "timezone_abbreviation": "GMT",
        "elevation": random.randint(10, 100),
        "daily_units": {
            "time": "iso8601",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
            "precipitation_sum": "mm",
            "windspeed_10m_max": "km/h",
            "weathercode": "wmo code"
        },
        "daily": {
            "time": dates,
            "temperature_2m_max": temp_max,
            "temperature_2m_min": temp_min,
            "precipitation_sum": precip,
            "windspeed_10m_max": wind,
            "weathercode": weather_codes
        }
    }

    return response

@mock_app.get("/health")
async def health():
    return {"status": "ok"}

# Для запуска заглушки отдельно
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="0.0.0.0", port=8082)