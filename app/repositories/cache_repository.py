from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, date
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CacheRepository:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None

    async def initialize(self):
        """Инициализация подключения к MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.MONGODB_DB_NAME]
            self.collection = self.db["weather_cache"]

            # TTL индекс
            await self.collection.create_index("expires_at", expireAfterSeconds=0)
            logger.info("Подключение к MongoDB установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к MongoDB: {e}")
            raise

    def _generate_cache_key(self, airport_code: str, arrival_date: str, return_date: Optional[str]) -> str:
        #Генерация ключа кэша
        if return_date:
            return f"{airport_code}_{arrival_date}_{return_date}"
        return f"{airport_code}_{arrival_date}"

    def _convert_dates_to_str(self, obj: Any) -> Any:
        """Рекурсивное преобразование date объектов в строки"""
        if isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._convert_dates_to_str(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_dates_to_str(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_dates_to_str(item) for item in obj)
        return obj

    async def get_cached_advice(
            self,
            airport_code: str,
            arrival_date: str,
            return_date: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Получение кэшированного совета"""
        try:
            cache_key = self._generate_cache_key(airport_code, arrival_date, return_date)
            result = await self.collection.find_one({"_id": cache_key})

            if result and "advice_result" in result:
                logger.info(f"Найден кэш для ключа {cache_key}")
                return result["advice_result"]
            return None

        except Exception as e:
            logger.error(f"Ошибка при чтении из кэша: {e}")
            return None

    async def save_advice(
            self,
            airport_code: str,
            arrival_date: str,
            return_date: Optional[str],
            city_data: Dict[str, Any],
            weather_data: Dict[str, Any],
            advice_result: Dict[str, Any]
    ):
        """Сохранение совета в кэш"""
        try:
            cache_key = self._generate_cache_key(airport_code, arrival_date, return_date)
            now = datetime.utcnow()

            city_data_serializable = self._convert_dates_to_str(city_data)
            weather_data_serializable = self._convert_dates_to_str(weather_data)
            advice_result_serializable = self._convert_dates_to_str(advice_result)

            document = {
                "_id": cache_key,
                "airport_code": airport_code,
                "arrival_date": arrival_date,
                "return_date": return_date,
                "city_data": city_data_serializable,
                "weather_data": weather_data_serializable,
                "advice_result": advice_result_serializable,
                "created_at": now,
                "expires_at": now + timedelta(hours=settings.CACHE_TTL_HOURS)
            }

            await self.collection.replace_one(
                {"_id": cache_key},
                document,
                upsert=True
            )
            logger.info(f"Сохранен кэш для ключа {cache_key}")

        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш: {e}")
            raise

    async def get_cache_by_airport(self, airport_code: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.collection.find(
                {"airport_code": airport_code},
                {"_id": 1, "created_at": 1, "expires_at": 1}
            )
            return await cursor.to_list(length=100)
        except Exception as e:
            logger.error(f"Ошибка при получении кэша по аэропорту: {e}")
            return []

    async def delete_cache_by_airport(self, airport_code: str) -> int:
        """Удаление всех кэшированных данных по аэропорту (для отладки)"""
        try:
            result = await self.collection.delete_many({"airport_code": airport_code})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Ошибка при удалении кэша: {e}")
            return 0

    async def check_connection(self) -> bool:
        """Проверка подключения к MongoDB"""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False

    async def close(self):
        """Закрытие подключения к MongoDB"""
        if self.client:
            self.client.close()