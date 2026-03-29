import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from app.config import settings

logger = logging.getLogger(__name__)


class CacheRepository:

    def __init__(self):
        self.collection = None
        self.client = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        # Проверка на запуск тестов
        is_test = self._is_test_environment()

        if is_test:
            logger.info("Test environment detected, skipping MongoDB initialization")
            self._initialized = True
            return

        try:
            from motor.motor_asyncio import AsyncIOMotorClient

            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")

            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000
            )

            # Проверяем подключение
            await self.client.admin.command('ping')
            logger.info("MongoDB connection successful")

            db = self.client[settings.MONGODB_DB_NAME]
            self.collection = db["weather_cache"]

            # Создаем TTL индекс
            try:
                # Получаем существующие индексы
                existing_indexes = await self.collection.index_information()

                # Проверяем, существует ли уже индекс expires_at
                expires_at_index_exists = False
                for index_name, index_info in existing_indexes.items():
                    if 'key' in index_info and 'expires_at' in index_info['key']:
                        expires_at_index_exists = True
                        logger.info(f"TTL index already exists with name: {index_name}")
                        break

                if not expires_at_index_exists:
                    # Создание нового индекса если его нет
                    await self.collection.create_index(
                        "expires_at",
                        expireAfterSeconds=0,
                        name="expires_at_ttl"
                    )
                    logger.info("TTL index created successfully")
                else:
                    logger.info("TTL index already exists, skipping creation")

            except Exception as e:
                logger.warning(f"Failed to create TTL index: {e}")

            self._initialized = True
            logger.info("MongoDB cache repository initialized successfully")

        except Exception as e:
            logger.error(f"Ошибка подключения к MongoDB: {e}")
            self._initialized = False
            raise

    def _is_test_environment(self) -> bool:
        # Проверяем наличие pytest в sys.modules
        if 'pytest' in os.sys.modules:
            return True

        # Проверяем переменные окружения pytest
        if os.getenv('PYTEST_CURRENT_TEST'):
            return True

        # Проверяем кастомную переменную
        if os.getenv('PYTEST_RUNNING') == '1':
            return True

        # Проверяем APP_ENV
        if settings.APP_ENV == 'test':
            return True

        return False

    def _generate_cache_key(self, airport_code: str, arrival_date: str, return_date: Optional[str] = None) -> str:
        if return_date:
            return f"{airport_code}_{arrival_date}_{return_date}".upper()
        return f"{airport_code}_{arrival_date}".upper()

    async def get_cached_advice(
            self,
            airport_code: str,
            arrival_date: str,
            return_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:

        # Проверяем, инициализирован ли репозиторий и есть ли коллекция
        if not self._initialized or self.collection is None:
            logger.debug("Cache repository not initialized, skipping cache read")
            return None

        try:
            cache_key = self._generate_cache_key(airport_code, arrival_date, return_date)

            result = await self.collection.find_one({"cache_key": cache_key})

            if result:
                logger.info(f"Cache hit for key: {cache_key}")
                result.pop("_id", None)
                return result.get("advice_result")
            else:
                logger.debug(f"Cache miss for key: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            return None

    async def save_advice(
            self,
            airport_code: str,
            arrival_date: str,
            return_date: Optional[str],
            city_info: Dict[str, Any],
            weather_data: Dict[str, Any],
            advice_result: Dict[str, Any]
    ):

        # Проверяем, инициализирован ли репозиторий и есть ли коллекция
        if not self._initialized or self.collection is None:
            logger.debug("Cache repository not initialized, skipping cache write")
            return

        try:
            cache_key = self._generate_cache_key(airport_code, arrival_date, return_date)

            # TTL в секундах (из настроек, по умолчанию 24 часа)
            ttl_seconds = settings.CACHE_TTL_HOURS * 3600
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

            cache_document = {
                "cache_key": cache_key,
                "airport_code": airport_code.upper(),
                "arrival_date": arrival_date,
                "return_date": return_date,
                "city_info": city_info,
                "weather_data": weather_data,
                "advice_result": advice_result,
                "created_at": datetime.now(timezone.utc),
                "expires_at": expires_at
            }


            result = await self.collection.replace_one(
                {"cache_key": cache_key},
                cache_document,
                upsert=True
            )

            if result.upserted_id:
                logger.info(f"New cache entry created for key: {cache_key}")
            elif result.modified_count:
                logger.info(f"Cache entry updated for key: {cache_key}")
            else:
                logger.debug(f"Cache entry unchanged for key: {cache_key}")

        except Exception as e:
            logger.error(f"Error saving to cache: {e}")


    async def get_cache_by_airport(self, airport_code: str) -> List[Dict[str, Any]]:

        if not self._initialized or self.collection is None:
            return []

        try:
            cursor = self.collection.find({"airport_code": airport_code.upper()})
            cursor.sort("created_at", -1)

            results = []
            async for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)

            logger.info(f"Found {len(results)} cache entries for airport {airport_code}")
            return results

        except Exception as e:
            logger.error(f"Error reading cache by airport: {e}")
            return []

    async def delete_cache_by_airport(self, airport_code: str) -> int:
        """
        Удаление всех кэшированных записей для аэропорта

        Args:
            airport_code: Код аэропорта

        Returns:
            Количество удаленных записей
        """
        if not self._initialized or self.collection is None:
            return 0

        try:
            result = await self.collection.delete_many({"airport_code": airport_code.upper()})
            logger.info(f"Deleted {result.deleted_count} cache entries for airport {airport_code}")
            return result.deleted_count

        except Exception as e:
            logger.error(f"Error deleting cache by airport: {e}")
            return 0

    async def delete_expired_cache(self) -> int:

        if not self._initialized or self.collection is None:
            return 0

        try:
            result = await self.collection.delete_many({
                "expires_at": {"$lt": datetime.now(timezone.utc)}
            })
            logger.info(f"Deleted {result.deleted_count} expired cache entries")
            return result.deleted_count

        except Exception as e:
            logger.error(f"Error deleting expired cache: {e}")
            return 0

    async def clear_all_cache(self) -> int:

        if not self._initialized or self.collection is None:
            return 0

        try:
            result = await self.collection.delete_many({})
            logger.info(f"Cleared all cache, deleted {result.deleted_count} entries")
            return result.deleted_count

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    async def check_connection(self) -> bool:

        if not self._initialized or self.client is None:
            return False

        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False

    async def close(self):

        if self.client is not None:
            try:
                self.client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")

        self.collection = None
        self.client = None
        self._initialized = False