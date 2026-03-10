# 🛫 Техническое задание: Микросервис Weather Packing Assistant

**Проект:** Weather Packing Advisor 
**Срок выполнения:** 2 недели  
**Стек:** Python 3.12+, FastAPI, MongoDB, Docker

---

## 1. Описание задачи

Необходимо разработать микросервис, который помогает пассажирам авиакомпании подготовиться к поездке. Сервис принимает код аэропорта назначения и даты поездки, запрашивает погоду в городе назначения и формирует персонализированный список вещей, которые нужно взять с собой.

**Пример пользовательского сценария:**  
Пассажир летит из Москвы в Лондон 15 марта, обратно 22 марта. Сервис смотрит погоду в Лондоне на эти даты и говорит: _«Возьмите зонт и тёплую куртку — ожидается дождь и +8°C»_.

---

## 2. Архитектура сервиса

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT REQUEST                     │
│   airport_code, arrival_date, departure_date         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Microservice                    │
│                                                      │
│  1. Запрос в Cities API → получить координаты        │
│  2. Запрос в Weather API → получить прогноз          │
│  3. Анализ погоды → сформировать список вещей        │
│  4. Сохранить результат в MongoDB (кэш)              │
│  5. Вернуть ответ пользователю                       │
└─────────────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────────┐
│   Cities API    │    │      MongoDB          │
│ (внутренний)    │    │  (кэш запросов)       │
└─────────────────┘    └──────────────────────┘
         │
         ▼
┌─────────────────┐
│   Weather API   │
│ (Open-Meteo,    │
│  бесплатный)    │
└─────────────────┘
```

---

## 3. Внешние API

### 3.1. Cities API (внутренний)

Внутренний API авиакомпании. Принимает IATA-код аэропорта, возвращает информацию о городе.

**Base URL:** `https://b.utair.ru`  

**Эндпоинт:**
```
GET /cities/api/v3/cities?q=VKO&limit=7
```
 
**Коды ошибок:**
- `404` — аэропорт не найден
- `500` — внутренняя ошибка сервиса

### 3.2. Weather API (Open-Meteo)

Бесплатный публичный API без ключа. Документация: https://open-meteo.com/en/docs

**Эндпоинт для прогноза:**
```
GET https://api.open-meteo.com/v1/forecast
```

**Параметры запроса:**

| Параметр | Описание | Пример |
|---|---|---|
| `latitude` | Широта | `51.4775` |
| `longitude` | Долгота | `-0.4614` |
| `daily` | Список дневных метрик | `temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode` |
| `start_date` | Начало периода | `2024-03-15` |
| `end_date` | Конец периода | `2024-03-22` |
| `timezone` | Часовой пояс | `Europe/London` |

**Пример запроса:**
```
GET https://api.open-meteo.com/v1/forecast?latitude=51.4775&longitude=-0.4614&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode&start_date=2026-03-15&end_date=2026-03-22&timezone=Europe/London
```

**WMO Weather Codes (weathercode)** — коды, которые возвращает API:

| Код | Описание |
|-----|----------|
| 0 | Ясно |
| 1–3 | Преимущественно ясно, переменная облачность |
| 45, 48 | Туман |
| 51–67 | Морось, дождь |
| 71–77 | Снег |
| 80–82 | Ливни |
| 85–86 | Снегопад |
| 95–99 | Гроза |

---

## 4. API микросервиса

### 4.1. Основной эндпоинт

```
POST /api/v1/packing-advice
```

**Request Body (JSON):**
```json
{
  "airport_code": "LHR",
  "arrival_date": "2024-03-15",
  "return_date": "2024-03-22"
}
```

**Описание полей:**

| Поле | Тип | Обязательное | Описание |
|------|-----|:-----------:|---------|
| `airport_code` | string | ✅ | IATA-код аэропорта назначения (3 буквы, uppercase) |
| `arrival_date` | string | ✅ | Дата прилёта в формате `YYYY-MM-DD` |
| `return_date` | string | ❌ | Дата обратного вылета в формате `YYYY-MM-DD` |

**Response Body (200 OK):**
```json
{
  "airport_code": "LHR",
  "city": "London",
  "country": "United Kingdom",
  "period": {
    "arrival": "2024-03-15",
    "return": "2024-03-22"
  },
  "weather_summary": {
    "temperature_min": 6.2,
    "temperature_max": 13.8,
    "conditions": ["rain", "cloudy", "partly_cloudy"],
    "will_rain": true,
    "will_snow": false,
    "strong_wind": false
  },
  "packing_advice": {
    "essentials": [
      "Зонт или дождевик — ожидаются дожди",
      "Тёплая куртка — температура 6–14°C"
    ],
    "recommended": [
      "Водонепроницаемая обувь",
      "Свитер или джемпер",
      "Шарф"
    ],
    "optional": [
      "Лёгкий пуловер на случай прохладных вечеров"
    ]
  },
  "cached": false,
  "generated_at": "2024-03-10T12:00:00Z"
}
```

**Коды ответов:**

| Код | Описание |
|-----|----------|
| `200` | Успешный ответ |
| `400` | Некорректные входные данные (невалидный код, неверный формат дат) |
| `404` | Аэропорт не найден в Cities API |
| `422` | Ошибка валидации Pydantic |
| `503` | Недоступен внешний сервис (Cities API или Weather API) |

### 4.2. Дополнительные эндпоинты

```
GET /api/v1/health
```
Проверка работоспособности сервиса. Должен вернуть статус подключения к MongoDB и доступность внешних API.

```json
{
  "status": "ok",
  "mongodb": "connected",
  "cities_api": "ok",
  "weather_api": "ok"
}
```

```
GET /api/v1/cache/{airport_code}
```
Получить кэшированные данные по аэропорту (для отладки).

```
DELETE /api/v1/cache/{airport_code}
```
Очистить кэш по аэропорту (для отладки).

---

## 5. Логика формирования советов

Логика должна быть вынесена в отдельный модуль `advice_engine.py`.

### 5.1. Правила для категории `essentials` (обязательно взять)

| Условие | Совет |
|---------|-------|
| `will_rain == True` | «Зонт или дождевик» |
| `temperature_max < 5°C` | «Тёплая зимняя куртка» |
| `5°C ≤ temperature_max < 15°C` | «Тёплая куртка или пальто» |
| `will_snow == True` | «Тёплая непромокаемая обувь, шапка и перчатки» |
| `strong_wind == True` (> 40 км/ч) | «Ветрозащитная куртка» |

### 5.2. Правила для `recommended`

| Условие | Совет |
|---------|-------|
| `temperature_min < 10°C` | «Свитер или джемпер» |
| `will_rain == True` | «Водонепроницаемая обувь» |
| `temperature_max > 25°C` | «Солнцезащитный крем» |
| `will_snow == True` | «Шарф и шапка» |

### 5.3. Правила для `optional`

| Условие | Совет |
|---------|-------|
| `temperature_max > 20°C` | «Лёгкая одежда для прогулок» |
| `temperature_min < 5°C` AND `temperature_max > 15°C` | «Одежда слоями — перепады температур» |
| Туман (weathercode 45, 48) | «Яркая одежда — видимость снижена» |

> ⚠️ Если за весь период нашлось 0 советов в `essentials` — это ошибка логики. Нужно добавить дефолтный совет.

---

## 6. MongoDB — схема хранения

### Коллекция: `weather_cache`

```json
{
  "_id": "LHR_2024-03-15_2024-03-22",
  "airport_code": "LHR",
  "arrival_date": "2024-03-15",
  "return_date": "2024-03-22",
  "city_data": { ... },
  "weather_data": { ... },
  "advice_result": { ... },
  "created_at": "2024-03-10T12:00:00Z",
  "expires_at": "2024-03-11T12:00:00Z"
}
```

**Правила кэширования:**
- TTL кэша: **24 часа** (настраивается через переменную окружения `CACHE_TTL_HOURS`)
- Ключ кэша: `{airport_code}_{arrival_date}_{return_date}`
- При наличии валидного кэша — не ходить во внешние API, вернуть кэшированный ответ с `"cached": true`
- Создать TTL-индекс в MongoDB на поле `expires_at`

---

## 7. Структура проекта

```
weather-packing-service/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Точка входа FastAPI
│   ├── config.py                # Настройки через pydantic-settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py           # Pydantic модели запросов
│   │   └── response.py          # Pydantic модели ответов
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cities_client.py     # HTTP-клиент для Cities API
│   │   ├── weather_client.py    # HTTP-клиент для Open-Meteo
│   │   └── advice_engine.py     # Логика формирования советов
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── cache_repository.py  # Работа с MongoDB
│   └── routers/
│       ├── __init__.py
│       ├── packing.py           # Основной эндпоинт
│       └── health.py            # Health check
├── tests/
│   ├── __init__.py
│   ├── test_advice_engine.py    # Unit-тесты логики советов
│   ├── test_packing_router.py   # Интеграционные тесты API
│   └── mocks/
│       ├── cities_api_mock.py   # Заглушка Cities API
│       └── weather_api_mock.py  # Заглушка Weather API
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. Конфигурация (переменные окружения)

Все настройки через `.env` файл и `pydantic-settings`.

**Файл `.env.example`:**
```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=weather_service

# Cities API
CITIES_API_BASE_URL=http://cities-api:8080
CITIES_API_TIMEOUT_SECONDS=5

# Weather API
WEATHER_API_BASE_URL=https://api.open-meteo.com/v1
WEATHER_API_TIMEOUT_SECONDS=10

# Cache settings
CACHE_TTL_HOURS=24

# App
APP_ENV=development
LOG_LEVEL=INFO
```

---

## 9. Docker

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
Должен содержать:
- Сервис `weather-service` (основной микросервис)
- Сервис `mongodb` (база данных)
- Сервис `cities-api-mock` — **заглушка внутреннего Cities API** (реализовать самостоятельно как простой FastAPI-сервис с набором тестовых аэропортов)

```yaml
version: '3.8'
services:
  weather-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - CITIES_API_BASE_URL=http://cities-api-mock:8080
    depends_on:
      - mongodb
      - cities-api-mock

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  cities-api-mock:
    build: ./mock_cities_api
    ports:
      - "8080:8080"

volumes:
  mongo_data:
```

---

## 10. Тесты

Минимальное покрытие тестами — **70%**.

### Обязательные тест-кейсы:

**`test_advice_engine.py`**
- [ ] Дождь → советует зонт
- [ ] Снег → советует тёплую обувь и шапку
- [ ] Жара (> 25°C) → советует солнцезащитный крем
- [ ] Сильный мороз (< 0°C) → советует зимнюю куртку
- [ ] Идеальная погода (20°C, без осадков) → минимальный набор советов
- [ ] Переменчивая погода (большой перепад min/max) → совет про слои одежды

**`test_packing_router.py`**
- [ ] Успешный запрос возвращает 200
- [ ] Невалидный код аэропорта (например, "XX") → 400
- [ ] Дата прилёта позже даты возврата → 400
- [ ] Аэропорт не найден в Cities API → 404
- [ ] Cities API недоступен → 503
- [ ] Повторный запрос с теми же параметрами → `"cached": true`

---

## 11. README.md

Обязательно написать `README.md` с разделами:
1. Описание сервиса (2–3 предложения)
2. Быстрый старт (`docker-compose up`)
3. Описание всех эндпоинтов с примерами curl-запросов
4. Описание переменных окружения
5. Запуск тестов
6. Описание логики формирования советов

---

## 12. Критерии приёмки

Задача считается выполненной, если:

- [ ] Сервис поднимается командой `docker-compose up` без ошибок
- [ ] Все три эндпоинта (`POST /packing-advice`, `GET /health`, `GET /cache/:code`) работают корректно
- [ ] Кэш работает: повторный запрос с теми же данными не идёт во внешние API
- [ ] Написаны тесты с покрытием ≥ 70%
- [ ] Код оформлен в соответствии с PEP 8
- [ ] Присутствует валидация входных данных через Pydantic
- [ ] Логируются все обращения к внешним API (уровень INFO) и ошибки (уровень ERROR)
- [ ] README.md написан и понятен

---

## 13. Советы и ссылки

- FastAPI docs: https://fastapi.tiangolo.com/
- Motor (async MongoDB driver): https://motor.readthedocs.io/
- Open-Meteo API: https://open-meteo.com/en/docs
- httpx (async HTTP client): https://www.python-httpx.org/
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- pytest: https://docs.pytest.org/

> 💡 **Подсказка:** Для заглушки Cities API достаточно сделать маленький FastAPI-сервис с хардкоженным словарём из 10–15 аэропортов (Москва, Лондон, Дубай, Нью-Йорк и т.д.).

> 💡 **Подсказка:** Используй `httpx.AsyncClient` — он работает асинхронно и дружит с FastAPI.

> 💡 **Подсказка:** TTL-индекс в MongoDB создаётся так: `db.weather_cache.create_index("expires_at", expireAfterSeconds=0)`
