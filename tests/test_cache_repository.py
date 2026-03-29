import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories.cache_repository import CacheRepository
from app.config import settings


@pytest.mark.asyncio
async def test_save_and_get_cache():
    """Тест сохранения и получения из кэша"""
    repo = CacheRepository()

    # Создаем мок коллекции
    mock_collection = AsyncMock()
    mock_collection.replace_one = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value={
        "_id": "LHR_2026-03-13_2026-03-13",
        "advice_result": {"cached": False, "test": "data"}
    })

    repo.collection = mock_collection
    repo._initialized = True

    # Тест сохранения
    await repo.save_advice(
        "LHR", "2026-03-13", "2026-03-13",
        {"city": "London"}, {"temp": 10}, {"advice": "test"}
    )
    mock_collection.replace_one.assert_called_once()

    # Тест получения
    result = await repo.get_cached_advice("LHR", "2026-03-13", "2026-03-13")
    assert result is not None
    assert result["test"] == "data"


@pytest.mark.asyncio
async def test_delete_cache():
    """Тест удаления из кэша"""
    repo = CacheRepository()

    mock_result = MagicMock()
    mock_result.deleted_count = 3

    mock_collection = AsyncMock()
    mock_collection.delete_many = AsyncMock(return_value=mock_result)

    repo.collection = mock_collection
    repo._initialized = True

    result = await repo.delete_cache_by_airport("LHR")
    assert result == 3


@pytest.mark.asyncio
async def test_get_cache_by_airport():
    """Тест получения кэша по аэропорту"""
    repo = CacheRepository()

    # Создаем список результатов (без _id, так как в репозитории он удаляется)
    mock_results = [
        {"cache_key": "key1", "airport_code": "LHR", "advice_result": {"test": "data1"}},
        {"cache_key": "key2", "airport_code": "LHR", "advice_result": {"test": "data2"}}
    ]

    # Создаем асинхронный итератор
    async def async_iterator():
        for item in mock_results:
            yield item

    # Создаем мок курсора
    mock_cursor = AsyncMock()
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.__aiter__ = MagicMock(return_value=async_iterator())

    mock_collection = AsyncMock()
    mock_collection.find = MagicMock(return_value=mock_cursor)

    repo.collection = mock_collection
    repo._initialized = True

    result = await repo.get_cache_by_airport("LHR")
    assert len(result) == 2
    assert result[0]["cache_key"] == "key1"
    assert result[1]["cache_key"] == "key2"
    assert "advice_result" in result[0]


@pytest.mark.asyncio
async def test_clear_all_cache():
    """Тест очистки всего кэша"""
    repo = CacheRepository()

    mock_result = MagicMock()
    mock_result.deleted_count = 5

    mock_collection = AsyncMock()
    mock_collection.delete_many = AsyncMock(return_value=mock_result)

    repo.collection = mock_collection
    repo._initialized = True

    result = await repo.clear_all_cache()
    assert result == 5


@pytest.mark.asyncio
async def test_check_connection():
    """Тест проверки подключения"""
    repo = CacheRepository()

    # Мок клиента
    mock_client = AsyncMock()
    mock_client.admin.command = AsyncMock(return_value={"ok": 1})

    repo.client = mock_client
    repo._initialized = True

    result = await repo.check_connection()
    assert result is True


@pytest.mark.asyncio
async def test_check_connection_failed():
    """Тест проверки подключения при ошибке"""
    repo = CacheRepository()

    mock_client = AsyncMock()
    mock_client.admin.command = AsyncMock(side_effect=Exception("Connection failed"))

    repo.client = mock_client
    repo._initialized = True

    result = await repo.check_connection()
    assert result is False


@pytest.mark.asyncio
async def test_get_cached_advice_not_initialized():
    """Тест получения кэша когда репозиторий не инициализирован"""
    repo = CacheRepository()
    repo._initialized = False

    result = await repo.get_cached_advice("LHR", "2026-03-13", "2026-03-13")
    assert result is None


@pytest.mark.asyncio
async def test_save_advice_not_initialized():
    """Тест сохранения когда репозиторий не инициализирован"""
    repo = CacheRepository()
    repo._initialized = False

    # Не должно вызвать ошибку
    await repo.save_advice(
        "LHR", "2026-03-13", "2026-03-13",
        {"city": "London"}, {"temp": 10}, {"advice": "test"}
    )
    # Если дошли сюда - тест пройден


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Тест генерации ключа кэша"""
    repo = CacheRepository()

    # С возвратной датой
    key = repo._generate_cache_key("LHR", "2026-03-13", "2026-03-22")
    assert key == "LHR_2026-03-13_2026-03-22"

    # Без возвратной даты
    key = repo._generate_cache_key("LHR", "2026-03-13", None)
    assert key == "LHR_2026-03-13"

    # С uppercase
    key = repo._generate_cache_key("lhr", "2026-03-13", "2026-03-22")
    assert key == "LHR_2026-03-13_2026-03-22"


@pytest.mark.asyncio
async def test_delete_expired_cache():
    """Тест удаления просроченного кэша"""
    repo = CacheRepository()

    mock_result = MagicMock()
    mock_result.deleted_count = 2

    mock_collection = AsyncMock()
    mock_collection.delete_many = AsyncMock(return_value=mock_result)

    repo.collection = mock_collection
    repo._initialized = True

    result = await repo.delete_expired_cache()
    assert result == 2
    # Проверяем, что delete_many был вызван с правильным фильтром
    mock_collection.delete_many.assert_called_once()
    args = mock_collection.delete_many.call_args[0][0]
    assert "expires_at" in args
    assert args["expires_at"]["$lt"] is not None


@pytest.mark.asyncio
async def test_save_advice_with_ttl():
    """Тест сохранения с правильным TTL"""
    repo = CacheRepository()

    # Создаем мок коллекции
    mock_collection = AsyncMock()
    mock_collection.replace_one = AsyncMock()

    repo.collection = mock_collection
    repo._initialized = True

    await repo.save_advice(
        "LHR", "2026-03-13", "2026-03-22",
        {"city": "London"},
        {"temp": 10},
        {"advice": "test"}
    )

    # Проверяем, что replace_one был вызван
    mock_collection.replace_one.assert_called_once()

    # Получаем аргументы вызова
    call_args = mock_collection.replace_one.call_args
    filter_doc = call_args[0][0]  # первый позиционный аргумент
    document = call_args[0][1]    # второй позиционный аргумент

    # Проверяем фильтр
    assert filter_doc == {"cache_key": "LHR_2026-03-13_2026-03-22"}

    # Проверяем структуру документа
    assert document["cache_key"] == "LHR_2026-03-13_2026-03-22"
    assert document["airport_code"] == "LHR"
    assert document["arrival_date"] == "2026-03-13"
    assert document["return_date"] == "2026-03-22"
    assert "created_at" in document
    assert "expires_at" in document

    # Проверяем, что expires_at установлен правильно (примерно через 24 часа)
    expires_at = document["expires_at"]
    created_at = document["created_at"]
    time_diff = (expires_at - created_at).total_seconds()
    expected_ttl = settings.CACHE_TTL_HOURS * 3600
    assert abs(time_diff - expected_ttl) < 10  # допустимая погрешность 10 секунд


@pytest.mark.asyncio
async def test_save_advice_with_upsert():
    """Тест сохранения с upsert"""
    repo = CacheRepository()

    mock_result = MagicMock()
    mock_result.upserted_id = "test_id"
    mock_result.modified_count = 0

    mock_collection = AsyncMock()
    mock_collection.replace_one = AsyncMock(return_value=mock_result)

    repo.collection = mock_collection
    repo._initialized = True

    await repo.save_advice(
        "LHR", "2026-03-13", "2026-03-22",
        {"city": "London"},
        {"temp": 10},
        {"advice": "test"}
    )

    mock_collection.replace_one.assert_called_once_with(
        {"cache_key": "LHR_2026-03-13_2026-03-22"},
        mock_collection.replace_one.call_args[0][1],
        upsert=True
    )


@pytest.mark.asyncio
async def test_save_advice_update_existing():
    """Тест обновления существующей записи"""
    repo = CacheRepository()

    mock_result = MagicMock()
    mock_result.upserted_id = None
    mock_result.modified_count = 1

    mock_collection = AsyncMock()
    mock_collection.replace_one = AsyncMock(return_value=mock_result)

    repo.collection = mock_collection
    repo._initialized = True

    await repo.save_advice(
        "LHR", "2026-03-13", "2026-03-22",
        {"city": "London"},
        {"temp": 10},
        {"advice": "test"}
    )

    mock_collection.replace_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_cache_by_airport_empty():
    """Тест получения кэша для аэропорта без записей"""
    repo = CacheRepository()

    # Создаем асинхронный итератор без результатов
    async def async_iterator():
        if False:
            yield  # пустой итератор

    # Создаем мок курсора
    mock_cursor = AsyncMock()
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.__aiter__ = MagicMock(return_value=async_iterator())

    mock_collection = AsyncMock()
    mock_collection.find = MagicMock(return_value=mock_cursor)

    repo.collection = mock_collection
    repo._initialized = True

    result = await repo.get_cache_by_airport("XXX")
    assert len(result) == 0