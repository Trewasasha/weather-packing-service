import pytest
from unittest.mock import patch, AsyncMock
from datetime import date
from app.services.weather_client import WeatherClient

@pytest.mark.asyncio
async def test_get_forecast_success():
    """Тест успешного получения прогноза погоды"""
    mock_response = {
        "daily": {
            "temperature_2m_max": [11.3],
            "temperature_2m_min": [3.4],
            "precipitation_sum": [7.5],
            "windspeed_10m_max": [34.6],
            "weathercode": [63]
        }
    }

    # Создаем мок для ответа
    mock_http_response = AsyncMock()
    mock_http_response.status_code = 200
    mock_http_response.json = AsyncMock(return_value=mock_response)

    # Создаем мок для клиента
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_http_response)

    with patch('httpx.AsyncClient', return_value=mock_client):
        client = WeatherClient()

        result = await client.get_forecast(
            51.47, -0.45,
            date(2026, 3, 13),
            date(2026, 3, 13)
        )

        assert result is not None
        assert "daily" in result
        assert result["daily"]["temperature_2m_max"][0] == 11.3