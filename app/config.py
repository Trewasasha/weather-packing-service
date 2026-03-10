from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Настройки из ТЗ
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "weather_service"

    CITIES_API_BASE_URL: str = "https://b.utair.ru"
    CITIES_API_TIMEOUT_SECONDS: int = 5

    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1"
    WEATHER_API_TIMEOUT_SECONDS: int = 10

    CACHE_TTL_HOURS: int = 24

    # Чтение из .env файла
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()