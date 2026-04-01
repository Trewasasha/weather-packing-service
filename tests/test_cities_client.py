import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.cities_client import CitiesClient
import httpx


@pytest.mark.asyncio
async def test_get_city_by_airport_success():
    """Тест успешного получения информации о городе"""
    mock_response_data = {
        "data": [{
            "name": "London",
            "country_name": "United Kingdom",
            "airports": [{
                "code": "LHR",
                "coordinates": {"lat": 51.47, "lon": -0.45}
            }]
        }]
    }

    # Создаем мок для ответа
    mock_response = AsyncMock()
    mock_response.status_code = 200
    # json должен быть функцией, возвращающей словарь
    mock_response.json = MagicMock(return_value=mock_response_data)

    # Создаем мок для клиента
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    # Патчим конструктор AsyncClient
    with patch('httpx.AsyncClient', return_value=mock_client):
        client = CitiesClient()
        result = await client.get_city_by_airport("LHR")

        assert result is not None
        assert result["city"] == "London"
        assert result["country"] == "United Kingdom"
        assert result["latitude"] == 51.47
        assert result["longitude"] == -0.45


@pytest.mark.asyncio
async def test_get_city_by_airport_not_found():
    """Тест: аэропорт не найден (404)"""
    # Создаем мок для ответа 404
    mock_response = AsyncMock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient', return_value=mock_client):
        client = CitiesClient()
        result = await client.get_city_by_airport("XXX")

        assert result is None


@pytest.mark.asyncio
async def test_get_city_by_airport_http_error():
    """Тест: HTTP ошибка при запросе"""
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
        "500 Error", request=MagicMock(), response=mock_response
    ))

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient', return_value=mock_client):
        client = CitiesClient()

        with pytest.raises(httpx.HTTPStatusError):
            await client.get_city_by_airport("LHR")


@pytest.mark.asyncio
async def test_get_city_by_airport_timeout():
    """Тест: таймаут при запросе"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

    with patch('httpx.AsyncClient', return_value=mock_client):
        client = CitiesClient()

        with pytest.raises(httpx.TimeoutException):
            await client.get_city_by_airport("LHR")