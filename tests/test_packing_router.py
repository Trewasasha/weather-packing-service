import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock
from datetime import date

client = TestClient(app)

def test_packing_advice_success():
    """Тест успешного получения совета"""
    with patch('app.routers.packing.CitiesClient.get_city_by_airport', new_callable=AsyncMock) as mock_cities, \
            patch('app.routers.packing.WeatherClient.get_forecast', new_callable=AsyncMock) as mock_weather, \
            patch('app.routers.packing.CacheRepository.get_cached_advice', new_callable=AsyncMock) as mock_cache, \
            patch('app.routers.packing.CacheRepository.save_advice', new_callable=AsyncMock) as mock_save:

        mock_cache.return_value = None
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.47,
            "longitude": -0.45
        }
        mock_weather.return_value = {
            "daily": {
                "temperature_2m_max": [11.3],
                "temperature_2m_min": [3.4],
                "precipitation_sum": [7.5],
                "windspeed_10m_max": [34.6],
                "weathercode": [63]
            }
        }

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-13",
                "return_date": "2026-03-13"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["airport_code"] == "LHR"
        assert data["city"] == "London"
        assert "packing_advice" in data
        assert data["cached"] is False

def test_packing_advice_cached():
    """Тест получения совета из кэша"""
    with patch('app.routers.packing.CacheRepository.get_cached_advice', new_callable=AsyncMock) as mock_cache:

        mock_cache.return_value = {
            "airport_code": "LHR",
            "city": "London",
            "country": "United Kingdom",
            "period": {"arrival": "2026-03-13", "return": "2026-03-13"},
            "weather_summary": {
                "temperature_min": 3.4,
                "temperature_max": 11.3,
                "conditions": ["rain"],
                "will_rain": True,
                "will_snow": False,
                "strong_wind": False
            },
            "packing_advice": {
                "essentials": ["Зонт"],
                "recommended": ["Свитер"],
                "optional": []
            },
            "cached": True
        }

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-13",
                "return_date": "2026-03-13"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True

def test_packing_advice_invalid_airport():
    """Тест с неверным кодом аэропорта"""
    response = client.post(
        "/api/v1/packing-advice",
        json={
            "airport_code": "XX",
            "arrival_date": "2026-03-13",
            "return_date": "2026-03-13"
        }
    )
    assert response.status_code == 422

def test_packing_advice_dates_invalid():
    """Тест с неверными датами (return < arrival)"""
    response = client.post(
        "/api/v1/packing-advice",
        json={
            "airport_code": "LHR",
            "arrival_date": "2026-03-15",
            "return_date": "2026-03-13"
        }
    )
    assert response.status_code == 422

def test_packing_advice_airport_not_found():
    """Тест с несуществующим аэропортом"""
    with patch('app.routers.packing.CitiesClient.get_city_by_airport', new_callable=AsyncMock) as mock_cities:
        mock_cities.return_value = None

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "XXX",
                "arrival_date": "2026-03-13",
                "return_date": "2026-03-13"
            }
        )

        assert response.status_code == 404