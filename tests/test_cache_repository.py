import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from app.repositories.cache_repository import CacheRepository
from app.config import settings

@pytest.mark.asyncio
async def test_save_and_get_cache():
    """Тест сохранения и получения из кэша"""
    repo = CacheRepository()

    mock_collection = AsyncMock()
    mock_collection.replace_one = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value={
        "_id": "LHR_2026-03-13_2026-03-13",
        "advice_result": {"cached": False, "test": "data"}
    })

    repo.collection = mock_collection

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

    result = await repo.delete_cache_by_airport("LHR")
    assert result == 3

@pytest.mark.asyncio
async def test_get_cache_by_airport():
    """Тест получения кэша по аэропорту"""
    repo = CacheRepository()

    # Создаем мок для курсора
    mock_cursor = AsyncMock()
    # Настраиваем to_list как корутину, которая возвращает список
    mock_cursor.to_list = AsyncMock(return_value=[{"_id": "test1"}, {"_id": "test2"}])

    mock_collection = AsyncMock()
    mock_collection.find = MagicMock(return_value=mock_cursor)

    repo.collection = mock_collection

    result = await repo.get_cache_by_airport("LHR")
    assert len(result) == 2
    assert result[0]["_id"] == "test1"
    assert result[1]["_id"] == "test2"