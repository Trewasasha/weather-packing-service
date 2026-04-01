import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


class TestErrorHandling:
    """Тесты для обработки ошибок внешних сервисов"""

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    def test_cities_api_timeout(self, mock_cities, client):
        """Тест: Таймаут при запросе к Cities API"""
        mock_cities.side_effect = httpx.TimeoutException("Timeout")

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 503
        assert "Внешний сервис временно недоступен" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    def test_cities_api_connection_error(self, mock_cities, client):
        """Тест: Ошибка подключения к Cities API"""
        mock_cities.side_effect = httpx.ConnectError("Connection failed")

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 503
        assert "Внешний сервис временно недоступен" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    def test_cities_api_http_500(self, mock_cities, client):
        """Тест: Cities API возвращает 500 ошибку"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_cities.side_effect = httpx.HTTPStatusError(
            "500 Server Error",
            request=MagicMock(),
            response=mock_response
        )

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 503
        assert "Внешний сервис временно недоступен" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    def test_cities_api_404_not_found(self, mock_cities, client):
        """Тест: Аэропорт не найден (404)"""
        mock_cities.return_value = None

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "XXX",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 404
        assert "Аэропорт с кодом XXX не найден" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_weather_api_timeout(self, mock_weather, mock_cities, client):
        """Тест: Таймаут при запросе к Weather API"""
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.4775,
            "longitude": -0.4614
        }
        mock_weather.side_effect = httpx.TimeoutException("Timeout")

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 503
        assert "Внешний сервис временно недоступен" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_weather_api_http_500(self, mock_weather, mock_cities, client):
        """Тест: Weather API возвращает 500 ошибку"""
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.4775,
            "longitude": -0.4614
        }

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_weather.side_effect = httpx.HTTPStatusError(
            "500 Server Error",
            request=MagicMock(),
            response=mock_response
        )

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 503
        assert "Внешний сервис временно недоступен" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_weather_api_returns_none(self, mock_weather, mock_cities, client):
        """Тест: Weather API возвращает None (пустой ответ)"""
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.4775,
            "longitude": -0.4614
        }
        mock_weather.return_value = None

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 503
        assert "Не удалось получить данные о погоде" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_weather_api_invalid_data(self, mock_weather, mock_cities, client):
        """Тест: Weather API возвращает некорректные данные (нет daily)"""
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.4775,
            "longitude": -0.4614
        }
        # Возвращаем данные без поля daily
        mock_weather.return_value = {"invalid": "data"}

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        # Должен вернуть 503, так как данные некорректны
        assert response.status_code == 503
        assert "Некорректные данные о погоде" in response.json()["detail"]

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_mongodb_read_error_but_service_continues(self, mock_weather, mock_cities, client):
        """Тест: Ошибка при чтении из MongoDB, но сервис продолжает работу"""
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.4775,
            "longitude": -0.4614
        }

        mock_weather.return_value = {
            "daily": {
                "temperature_2m_min": [6.2, 7.1],
                "temperature_2m_max": [13.8, 14.5],
                "precipitation_sum": [0.5, 0],
                "windspeed_10m_max": [25, 30],
                "weathercode": [61, 1]
            }
        }

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        # Должен вернуть 200
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False
        assert data["airport_code"] == "LHR"
        assert data["city"] == "London"

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_mongodb_write_error_but_service_continues(self, mock_weather, mock_cities, client):
        """Тест: Ошибка при записи в MongoDB, но сервис продолжает работу"""
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.4775,
            "longitude": -0.4614
        }

        mock_weather.return_value = {
            "daily": {
                "temperature_2m_min": [6.2, 7.1],
                "temperature_2m_max": [13.8, 14.5],
                "precipitation_sum": [0.5, 0],
                "windspeed_10m_max": [25, 30],
                "weathercode": [61, 1]
            }
        }

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        # Должен вернуть 200
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False
        assert data["airport_code"] == "LHR"
        assert data["city"] == "London"

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_all_services_fail_gracefully(self, mock_weather, mock_cities, client):
        """Тест: Все сервисы недоступны - graceful degradation"""
        mock_cities.side_effect = Exception("Cities API failed")

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        assert response.status_code == 503
        assert "Внешний сервис временно недоступен" in response.json()["detail"]
        mock_weather.assert_not_called()

    @patch('app.routers.packing.CitiesClient.get_city_by_airport')
    @patch('app.routers.packing.WeatherClient.get_forecast')
    def test_partial_data_after_weather_failure(self, mock_weather, mock_cities, client):
        """Тест: Частичные данные после сбоя Weather API"""
        mock_cities.return_value = {
            "city": "London",
            "country": "United Kingdom",
            "latitude": 51.4775,
            "longitude": -0.4614
        }

        # Weather API возвращает неполные данные (отсутствуют обязательные поля)
        mock_weather.return_value = {
            "daily": {
                "temperature_2m_min": [6.2],
                # Отсутствуют другие обязательные поля
            }
        }

        response = client.post(
            "/api/v1/packing-advice",
            json={
                "airport_code": "LHR",
                "arrival_date": "2026-03-15",
                "return_date": "2026-03-22"
            }
        )

        # Должен вернуть 503, так как данные неполные
        assert response.status_code == 503
        assert "Некорректные данные о погоде" in response.json()["detail"]


# Отдельные тесты для health check
def test_health_check_degraded_when_mongodb_down(client):
    """Тест: Health check показывает degraded когда MongoDB недоступна"""
    with patch('app.routers.health.check_mongodb', new_callable=AsyncMock) as mock_mongo, \
            patch('app.routers.health.check_cities_api', new_callable=AsyncMock) as mock_cities, \
            patch('app.routers.health.check_weather_api', new_callable=AsyncMock) as mock_weather:

        mock_mongo.return_value = "disconnected"
        mock_cities.return_value = "ok"
        mock_weather.return_value = "ok"

        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["mongodb"] == "disconnected"


def test_health_check_degraded_when_cities_api_down(client):
    """Тест: Health check показывает degraded когда Cities API недоступен"""
    with patch('app.routers.health.check_mongodb', new_callable=AsyncMock) as mock_mongo, \
            patch('app.routers.health.check_cities_api', new_callable=AsyncMock) as mock_cities, \
            patch('app.routers.health.check_weather_api', new_callable=AsyncMock) as mock_weather:

        mock_mongo.return_value = "connected"
        mock_cities.return_value = "unavailable"
        mock_weather.return_value = "ok"

        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["cities_api"] == "unavailable"


def test_health_check_degraded_when_weather_api_down(client):
    """Тест: Health check показывает degraded когда Weather API недоступен"""
    with patch('app.routers.health.check_mongodb', new_callable=AsyncMock) as mock_mongo, \
            patch('app.routers.health.check_cities_api', new_callable=AsyncMock) as mock_cities, \
            patch('app.routers.health.check_weather_api', new_callable=AsyncMock) as mock_weather:

        mock_mongo.return_value = "connected"
        mock_cities.return_value = "ok"
        mock_weather.return_value = "unavailable"

        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["weather_api"] == "unavailable"