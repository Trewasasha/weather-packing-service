import httpx
from typing import Optional, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CitiesClient:
    def __init__(self):
        self.base_url = settings.CITIES_API_BASE_URL
        self.timeout = settings.CITIES_API_TIMEOUT_SECONDS
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def get_city_by_airport(self, airport_code: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о городе по коду аэропорта
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/cities/api/v3/cities",
                params={"q": airport_code, "limit": 7}
            )

            if response.status_code == 404:
                logger.warning(f"Аэропорт {airport_code} не найден")
                return None

            response.raise_for_status()

            data = response.json()

            if data and "data" in data and len(data["data"]) > 0:
                city_data = data["data"][0]
                # Ищем нужный аэропорт в списке airports
                for airport in city_data.get("airports", []):
                    if airport.get("code") == airport_code.upper():
                        return {
                            "city": city_data.get("name"),
                            "country": city_data.get("country_name"),
                            "latitude": airport.get("coordinates", {}).get("lat"),
                            "longitude": airport.get("coordinates", {}).get("lon")
                        }

                # Если аэропорт не найден в списке, берем координаты города
                coords = city_data.get("coordinates", {})
                return {
                    "city": city_data.get("name"),
                    "country": city_data.get("country_name"),
                    "latitude": coords.get("lat"),
                    "longitude": coords.get("lon")
                }

            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout при запросе к Cities API для {airport_code}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при запросе к Cities API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к Cities API: {e}")
            raise

    async def close(self):
        await self.client.aclose()