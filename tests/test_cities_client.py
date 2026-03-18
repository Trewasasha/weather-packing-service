import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.cities_client import CitiesClient

@pytest.mark.asyncio
async def test_get_city_by_airport_success():
    """Тест успешного получения информации о городе"""
    mock_response = {
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
    mock_http_response = AsyncMock()
    mock_http_response.status_code = 200
    mock_http_response.json = AsyncMock(return_value=mock_response)

    # Создаем мок для клиента
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_http_response)

    # Патчим конструктор AsyncClient
    with patch('httpx.AsyncClient', return_value=mock_client):
        client = CitiesClient()

        result = await client.get_city_by_airport("LHR")

        assert result is not None
        assert result["city"] == "London"
        assert result["country"] == "United Kingdom"
        assert result["latitude"] == 51.47
        assert result["longitude"] == -0.45