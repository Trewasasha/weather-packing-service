import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    with patch('app.routers.packing.get_cache_repository') as mock_get_repo:
        # Создаем мок репозитория
        mock_repo = AsyncMock()
        mock_repo.get_cached_advice = AsyncMock(return_value=None)
        mock_repo.save_advice = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_repo.check_connection = AsyncMock(return_value=True)
        mock_get_repo.return_value = mock_repo

        yield TestClient(app)


@pytest.fixture
def mock_cache_repo():
    mock_repo = AsyncMock()
    mock_repo.get_cached_advice = AsyncMock(return_value=None)
    mock_repo.save_advice = AsyncMock()
    mock_repo.initialize = AsyncMock()
    mock_repo.close = AsyncMock()
    mock_repo.check_connection = AsyncMock(return_value=True)
    return mock_repo