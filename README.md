# Weather Packing Advisor

Микросервис для помощи пассажирам авиакомпании в подготовке к поездке. Сервис принимает код аэропорта назначения и даты поездки, запрашивает прогноз погоды и формирует персонализированный список вещей, которые нужно взять с собой.

## Описание

Сервис помогает путешественникам собрать чемодан с учётом погодных условий в месте назначения. На основе IATA-кода аэропорта и дат поездки сервис:

1. Получает координаты города через внутренний Cities API
2. Запрашивает прогноз погоды на указанный период через Open-Meteo API
3. Анализирует погодные условия (температура, осадки, ветер)
4. Формирует персонализированные советы по упаковке вещей
5. Кэширует результаты в MongoDB для ускорения повторных запросов

**Пример использования:**
```
POST /api/v1/packing-advice
{
  "airport_code": "LHR",
  "arrival_date": "2024-03-15",
  "return_date": "2024-03-22"
}
```

Ответ подскажет, что взять с собой в Лондон в марте: зонт, тёплую куртку, водонепроницаемую обувь и другие необходимые вещи.

##  Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git
- Make (опционально, для использования скриптов)

### Запуск сервиса

#### Способ 1: Использование скриптов (рекомендуется)

```bash
# Сделайте скрипты исполняемыми
chmod +x run.sh stop.sh

# Запустите сервис
./run.sh

# Для остановки
./stop.sh
```

#### Способ 2: Ручной запуск

```bash
# Создайте файл .env из примера (если не создан)
cp .env.example .env

# Запустите Docker Compose
cd docker
docker-compose up --build
```

Сервис будет доступен по адресу: http://localhost:8080

### Проверка работоспособности

```bash
# Проверка health статуса
curl http://localhost:8080/api/v1/health

# Корневой эндпоинт
curl http://localhost:8080/
```

##  API Эндпоинты

### Основной эндпоинт

#### `POST /api/v1/packing-advice`

Получить советы по упаковке вещей.

**Request Body:**
```json
{
  "airport_code": "LHR",
  "arrival_date": "2024-03-15",
  "return_date": "2024-03-22"
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|:------------:|----------|
| `airport_code` | string |      +       | IATA-код аэропорта (3 буквы, например LHR, JFK, DXB) |
| `arrival_date` | date |      +       | Дата прилёта в формате YYYY-MM-DD |
| `return_date` | date |      -       | Дата возвращения (если не указана, считается однодневная поездка) |

**Пример запроса с curl:**
```bash
curl -X POST http://localhost:8080/api/v1/packing-advice \
  -H "Content-Type: application/json" \
  -d '{
    "airport_code": "LHR",
    "arrival_date": "2024-03-15",
    "return_date": "2024-03-22"
  }'
```

**Response (200 OK):**
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
    "conditions": ["rain", "partly_cloudy"],
    "will_rain": true,
    "will_snow": false,
    "strong_wind": false
  },
  "packing_advice": {
    "essentials": [
      "Зонт или дождевик — ожидаются дожди",
      "Тёплая куртка или пальто — температура 6–14°C"
    ],
    "recommended": [
      "Водонепроницаемая обувь",
      "Свитер или джемпер — прохладная погода"
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
- `200` — Успешный ответ
- `400` — Некорректные входные данные (невалидный код аэропорта, дата возврата раньше даты прилёта)
- `404` — Аэропорт не найден в Cities API
- `422` — Ошибка валидации Pydantic
- `503` — Внешний сервис недоступен (Cities API или Weather API)

### Системные эндпоинты

#### `GET /api/v1/health`

Проверка работоспособности сервиса.

```bash
curl http://localhost:8080/api/v1/health
```

**Response:**
```json
{
  "status": "ok",
  "mongodb": "connected",
  "cities_api": "ok",
  "weather_api": "ok"
}
```

#### `GET /api/v1/cache/{airport_code}`

Получить все кэшированные записи для указанного аэропорта (для отладки).

```bash
curl http://localhost:8080/api/v1/cache/LHR
```

#### `DELETE /api/v1/cache/{airport_code}`

Очистить кэш для указанного аэропорта.

```bash
curl -X DELETE http://localhost:8080/api/v1/cache/LHR
```

#### `GET /`

Корневой эндпоинт с информацией о сервисе.

```bash
curl http://localhost:8080/
```

##  Переменные окружения

Все настройки сервиса задаются через файл `.env`:

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `MONGODB_URL` | URL подключения к MongoDB | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Имя базы данных | `weather_service` |
| `CITIES_API_BASE_URL` | Базовый URL Cities API | `https://b.utair.ru` |
| `CITIES_API_TIMEOUT_SECONDS` | Таймаут запросов к Cities API (сек) | `5` |
| `WEATHER_API_BASE_URL` | Базовый URL Weather API | `https://api.open-meteo.com/v1` |
| `WEATHER_API_TIMEOUT_SECONDS` | Таймаут запросов к Weather API (сек) | `10` |
| `CACHE_TTL_HOURS` | Время жизни кэша в часах | `24` |
| `APP_ENV` | Окружение (development/production/test) | `development` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

##  Запуск тестов

### Локальный запуск тестов

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск всех тестов
pytest tests/ -v

# Запуск с покрытием
pytest tests/ --cov=app --cov-report=term-missing

# Запуск конкретного тестового файла
pytest tests/test_advice_engine.py -v
```

### Запуск тестов в Docker

```bash
# Запуск тестов в контейнере
docker-compose run --rm app pytest tests/ -v
```

##  Логика формирования советов

### Категория `essentials` (обязательно взять)

| Условие | Совет |
|---------|-------|
| `will_rain == True` | «Зонт или дождевик — ожидаются дожди» |
| `temperature_max < 5°C` | «Тёплая зимняя куртка — температура ниже 5°C» |
| `5°C ≤ temperature_max < 15°C` | «Тёплая куртка или пальто — температура {min}–{max}°C» |
| `will_snow == True` | «Тёплая непромокаемая обувь, шапка и перчатки — ожидается снег» |
| `strong_wind == True` (> 40 км/ч) | «Ветрозащитная куртка — ожидается сильный ветер» |

### Категория `recommended` (рекомендуется взять)

| Условие | Совет |
|---------|-------|
| `temperature_min < 10°C` | «Свитер или джемпер — прохладная погода» |
| `will_rain == True` | «Водонепроницаемая обувь» |
| `temperature_max > 25°C` | «Солнцезащитный крем — ожидается жаркая погода» |
| `will_snow == True` | «Шарф и шапка» |

### Категория `optional` (можно взять по желанию)

| Условие | Совет |
|---------|-------|
| `temperature_max > 20°C` | «Лёгкая одежда для прогулок — тёплая погода» |
| `temperature_min < 5°C` и `temperature_max > 15°C` | «Одежда слоями — ожидаются перепады температур» |
| Туман (weathercode 45, 48) | «Яркая одежда — видимость снижена из-за тумана» |

### Дефолтный совет

Если не сработало ни одно правило для `essentials`, добавляется дефолтный совет:
- Для комфортной погоды (15–25°C): «Комфортная одежда по сезону — погода благоприятная»
- Для остальных случаев: «Одежда по сезону — проверьте прогноз перед вылетом»

##  Кэширование

Сервис использует MongoDB для кэширования результатов запросов:

- **Ключ кэша:** `{airport_code}_{arrival_date}_{return_date}`
- **TTL:** 24 часа (настраивается через `CACHE_TTL_HOURS`)
- **Автоматическое удаление:** TTL-индекс MongoDB автоматически удаляет просроченные записи

При повторном запросе с теми же параметрами сервис возвращает кэшированный ответ (поле `cached: true`) и не обращается к внешним API.

##  Архитектура проекта

```
weather-packing-service/
├── app/                          # Основной код приложения
│   ├── main.py                   # Точка входа FastAPI
│   ├── config.py                 # Настройки через pydantic-settings
│   ├── models/
│   │   ├── request.py            # Pydantic модели запросов
│   │   └── response.py           # Pydantic модели ответов
│   ├── services/
│   │   ├── cities_client.py      # HTTP-клиент для Cities API
│   │   ├── weather_client.py     # HTTP-клиент для Open-Meteo
│   │   └── advice_engine.py      # Логика формирования советов
│   ├── repositories/
│   │   └── cache_repository.py   # Работа с MongoDB (кэш)
│   └── routers/
│       ├── packing.py            # Основной эндпоинт
│       └── health.py             # Health check эндпоинт
├── tests/                        # Тесты
│   ├── conftest.py               # Фикстуры pytest
│   ├── test_advice_engine.py     # Тесты логики советов
│   ├── test_packing_router.py    # Интеграционные тесты API
│   ├── test_error_handling.py    # Тесты обработки ошибок
│   ├── test_cities_client.py     # Тесты Cities API клиента
│   ├── test_weather_client.py    # Тесты Weather API клиента
│   ├── test_cache_repository.py  # Тесты кэша
│   ├── test_health_router.py     # Тесты health check
│   └── mocks/                    # Заглушки внешних API
│       ├── cities_api_mock.py    # Mock Cities API
│       └── weather_api_mock.py   # Mock Weather API
├── docker/
│   ├── Dockerfile                # Docker образ приложения
│   └── docker-compose.yml        # Оркестрация сервисов
├── .env.example                  # Пример переменных окружения
├── requirements.txt              # Зависимости Python
├── run.sh                        # Скрипт запуска
├── stop.sh                       # Скрипт остановки
└── README.md                     # Документация
```

##  Разработка

### Локальный запуск без Docker

1. Установите MongoDB локально или запустите через Docker:
```bash
docker run -d -p 27017:27017 mongo:7
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

3. Создайте файл `.env`:
```bash
cp .env.example .env
```

4. Запустите сервис:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Запуск заглушек API для тестирования

Для изолированного тестирования можно запустить mock-серверы внешних API:

```bash
python tests/mocks/run_mocks.py
```

Заглушки будут доступны:
- Cities API Mock: http://localhost:8081
- Weather API Mock: http://localhost:8082

### Форматирование кода

Проект следует стандарту PEP 8. Для проверки можно использовать:
```bash
# Установка инструментов
pip install black flake8

# Проверка стиля
flake8 app/ tests/

# Автоматическое форматирование
black app/ tests/
```

##  Логирование

Сервис логирует:
- **INFO:** успешные запросы к внешним API, кэширование
- **ERROR:** ошибки подключения, таймауты, некорректные данные
- **WARNING:** проблемы с индексами MongoDB, валидация данных

Логи выводятся в консоль с форматом:
```
2024-03-10 12:00:00 - app.services.cities_client - INFO - Получен город London для аэропорта LHR
```

##  Устранение неполадок

### Сервис не запускается
- Проверьте, что все порты (8080, 27017) свободны
- Убедитесь, что файл `.env` существует и содержит корректные настройки
- Проверьте логи: `docker-compose logs app`

### Ошибка подключения к MongoDB
- Убедитесь, что MongoDB запущен: `docker-compose ps mongodb`
- Проверьте переменную `MONGODB_URL` в `.env`
- В логах MongoDB: `docker-compose logs mongodb`

### Cities API возвращает 404
- Проверьте корректность IATA-кода (должно быть 3 буквы)
- Убедитесь, что Cities API доступен: `curl https://b.utair.ru/cities/api/v3/cities?q=LHR`

### Weather API недоступен
- Проверьте интернет-соединение
- Убедитесь, что URL корректный: `https://api.open-meteo.com/v1/forecast`

### Тесты не проходят
- Убедитесь, что все зависимости установлены
- Запустите тесты с флагом `-v` для детального вывода
- Проверьте, что нет конфликтов с локальными сервисами

##  Лицензия

Проект разработан в рамках тестового задания. Все права принадлежат разработчику.