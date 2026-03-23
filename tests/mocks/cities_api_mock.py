from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Модели данных
class Coordinates(BaseModel):
    lat: float
    lon: float

class Airport(BaseModel):
    name: str
    time_zone: str
    country_code: str
    city_code: str
    code: str
    searchable: bool
    coordinates: Coordinates
    name_translations: Dict[str, str]

class CityData(BaseModel):
    code: str
    name: str
    time_zone: str
    name_translations: Dict[str, str]
    country_code: str
    coordinates: Coordinates
    airports: List[Airport]
    country_name: str

class CitiesResponse(BaseModel):
    data: List[CityData]
    meta: Dict[str, Any]

mock_app = FastAPI(title="Cities API Mock", version="1.0.0")

mock_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Тестовые данные аэропортов
MOCK_AIRPORTS = {
    "LHR": {
        "city": "London",
        "country": "United Kingdom",
        "country_code": "GB",
        "city_code": "LON",
        "latitude": 51.469604,
        "longitude": -0.453566,
        "timezone": "Europe/London"
    },
    "CDG": {
        "city": "Paris",
        "country": "France",
        "country_code": "FR",
        "city_code": "PAR",
        "latitude": 49.0097,
        "longitude": 2.5479,
        "timezone": "Europe/Paris"
    },
    "FCO": {
        "city": "Rome",
        "country": "Italy",
        "country_code": "IT",
        "city_code": "ROM",
        "latitude": 41.8003,
        "longitude": 12.2389,
        "timezone": "Europe/Rome"
    },
    "DXB": {
        "city": "Dubai",
        "country": "United Arab Emirates",
        "country_code": "AE",
        "city_code": "DXB",
        "latitude": 25.2532,
        "longitude": 55.3657,
        "timezone": "Asia/Dubai"
    },
    "JFK": {
        "city": "New York",
        "country": "USA",
        "country_code": "US",
        "city_code": "NYC",
        "latitude": 40.6413,
        "longitude": -73.7781,
        "timezone": "America/New_York"
    },
    "SVO": {
        "city": "Moscow",
        "country": "Russia",
        "country_code": "RU",
        "city_code": "MOW",
        "latitude": 55.9721,
        "longitude": 37.4146,
        "timezone": "Europe/Moscow"
    }
}

# Города
MOCK_CITIES = {
    "LON": {
        "name": "London",
        "country": "United Kingdom",
        "country_code": "GB",
        "latitude": 51.51,
        "longitude": 0.06,
        "airports": ["LHR", "LGW", "STN", "LTN", "LCY", "SEN"]
    },
    "PAR": {
        "name": "Paris",
        "country": "France",
        "country_code": "FR",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "airports": ["CDG", "ORY"]
    },
    "ROM": {
        "name": "Rome",
        "country": "Italy",
        "country_code": "IT",
        "latitude": 41.9028,
        "longitude": 12.4964,
        "airports": ["FCO", "CIA"]
    },
    "NYC": {
        "name": "New York",
        "country": "USA",
        "country_code": "US",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "airports": ["JFK", "LGA", "EWR"]
    },
    "MOW": {
        "name": "Moscow",
        "country": "Russia",
        "country_code": "RU",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "airports": ["SVO", "DME", "VKO"]
    }
}

@mock_app.get("/cities/api/v3/cities")
async def get_cities(q: Optional[str] = None, limit: int = 7):

    if not q:
        return {"data": [], "meta": {"total": 0, "next_cursor": None}}

    search_term = q.upper()
    result_cities = []

    # Поиск по коду аэропорта
    if search_term in MOCK_AIRPORTS:
        airport = MOCK_AIRPORTS[search_term]
        city_code = airport["city_code"]
        city = MOCK_CITIES.get(city_code, {})

        # Создаем список аэропортов для города
        airports = []
        for airport_code in city.get("airports", []):
            if airport_code in MOCK_AIRPORTS:
                a = MOCK_AIRPORTS[airport_code]
                airports.append({
                    "name": f"{a['city']} {airport_code} Airport",
                    "time_zone": a["timezone"],
                    "country_code": a["country_code"],
                    "city_code": city_code,
                    "code": airport_code,
                    "searchable": True,
                    "coordinates": {
                        "lon": a["longitude"],
                        "lat": a["latitude"]
                    },
                    "name_translations": {
                        "en": f"{a['city']} {airport_code} Airport",
                        "ru": f"Аэропорт {a['city']} {airport_code}"
                    }
                })

        city_data = {
            "code": city_code,
            "name": city.get("name", airport["city"]),
            "time_zone": airport["timezone"],
            "name_translations": {
                "en": city.get("name", airport["city"]),
                "ru": city.get("name", airport["city"])
            },
            "country_code": airport["country_code"],
            "coordinates": {
                "lon": city.get("longitude", airport["longitude"]),
                "lat": city.get("latitude", airport["latitude"])
            },
            "airports": airports,
            "country_name": airport["country"]
        }
        result_cities.append(city_data)

    # Поиск по коду города
    elif search_term in MOCK_CITIES:
        city = MOCK_CITIES[search_term]

        airports = []
        for airport_code in city.get("airports", []):
            if airport_code in MOCK_AIRPORTS:
                a = MOCK_AIRPORTS[airport_code]
                airports.append({
                    "name": f"{a['city']} {airport_code} Airport",
                    "time_zone": a["timezone"],
                    "country_code": a["country_code"],
                    "city_code": search_term,
                    "code": airport_code,
                    "searchable": True,
                    "coordinates": {
                        "lon": a["longitude"],
                        "lat": a["latitude"]
                    },
                    "name_translations": {
                        "en": f"{a['city']} {airport_code} Airport",
                        "ru": f"Аэропорт {a['city']} {airport_code}"
                    }
                })

        city_data = {
            "code": search_term,
            "name": city["name"],
            "time_zone": "Europe/London",  # Упрощенно
            "name_translations": {
                "en": city["name"],
                "ru": city["name"]
            },
            "country_code": city["country_code"],
            "coordinates": {
                "lon": city["longitude"],
                "lat": city["latitude"]
            },
            "airports": airports,
            "country_name": city["country"]
        }
        result_cities.append(city_data)

    if not result_cities:
        raise HTTPException(status_code=404, detail="Airport or city not found")

    return {
        "data": result_cities[:limit],
        "meta": {
            "total": len(result_cities),
            "next_cursor": None
        }
    }

@mock_app.get("/health")
async def health():
    return {"status": "ok"}

# Для запуска заглушки отдельно
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="0.0.0.0", port=8081)