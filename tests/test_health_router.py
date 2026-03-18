from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_health_endpoint():
    """Тест health check эндпоинта"""
    with patch('app.routers.health.check_mongodb', new_callable=AsyncMock) as mock_mongo, \
            patch('app.routers.health.check_cities_api', new_callable=AsyncMock) as mock_cities, \
            patch('app.routers.health.check_weather_api', new_callable=AsyncMock) as mock_weather:

        mock_mongo.return_value = "connected"
        mock_cities.return_value = "ok"
        mock_weather.return_value = "ok"

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["mongodb"] == "connected"
        assert data["cities_api"] == "ok"
        assert data["weather_api"] == "ok"