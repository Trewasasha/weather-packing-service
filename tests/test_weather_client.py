import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import date
from app.services.weather_client import WeatherClient
import httpx


@pytest.mark.asyncio
async def test_get_forecast_success():
    """Тест успешного получения прогноза погоды"""
    mock_response_data = {
        "daily": {
            "temperature_2m_max": [11.3],
            "temperature_2m_min": [3.4],
            "precipitation_sum": [7.5],
            "windspeed_10m_max": [34.6],
            "weathercode": [63]
        }
    }

    # Создаем мок для ответа
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value=mock_response_data)

    # Создаем мок для клиента
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

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


@pytest.mark.asyncio
async def test_get_forecast_http_error():
    """Тест: HTTP ошибка при запросе погоды"""
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
        "500 Error", request=MagicMock(), response=mock_response
    ))

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient', return_value=mock_client):
        client = WeatherClient()

        with pytest.raises(httpx.HTTPStatusError):
            await client.get_forecast(51.47, -0.45, date(2026, 3, 13), date(2026, 3, 13))


@pytest.mark.asyncio
async def test_get_forecast_timeout():
    """Тест: таймаут при запросе погоды"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

    with patch('httpx.AsyncClient', return_value=mock_client):
        client = WeatherClient()

        with pytest.raises(httpx.TimeoutException):
            await client.get_forecast(51.47, -0.45, date(2026, 3, 13), date(2026, 3, 13))