import httpx
from typing import Optional, Dict, Any, Union
from datetime import date, datetime
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class WeatherClient:
    def __init__(self):
        self.base_url = settings.WEATHER_API_BASE_URL
        self.timeout = settings.WEATHER_API_TIMEOUT_SECONDS
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def get_forecast(
            self,
            latitude: float,
            longitude: float,
            start_date: Union[date, str],
            end_date: Union[date, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Получение прогноза погоды от Open-Meteo
        """
        try:
            # Функция для преобразования даты в строку
            def format_date(d):
                if isinstance(d, (date, datetime)):
                    return d.isoformat()
                return str(d)

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
                "start_date": format_date(start_date),
                "end_date": format_date(end_date),
                "timezone": "auto"
            }

            response = await self.client.get(
                f"{self.base_url}/forecast",
                params=params
            )

            response.raise_for_status()
            data = response.json()
            return data

        except httpx.TimeoutException:
            logger.error("Timeout при запросе к Weather API")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при запросе к Weather API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к Weather API: {e}")
            raise

    async def close(self):
        await self.client.aclose()