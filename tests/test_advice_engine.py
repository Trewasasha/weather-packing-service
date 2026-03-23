import pytest
from app.services.advice_engine import AdviceEngine

@pytest.fixture
def engine():
    return AdviceEngine()

def test_rain_advice(engine):
    weather_summary = {
        "temperature_min": 10,
        "temperature_max": 15,
        "conditions": ["rain"],
        "will_rain": True,
        "will_snow": False,
        "strong_wind": False
    }

    advice = engine.generate_packing_advice(weather_summary)

    assert "Зонт или дождевик — ожидаются дожди" in advice["essentials"]
    assert "Водонепроницаемая обувь" in advice["recommended"]

def test_snow_advice(engine):
    weather_summary = {
        "temperature_min": -5,
        "temperature_max": 0,
        "conditions": ["snow"],
        "will_rain": False,
        "will_snow": True,
        "strong_wind": False
    }

    advice = engine.generate_packing_advice(weather_summary)

    assert "Тёплая непромокаемая обувь, шапка и перчатки — ожидается снег" in advice["essentials"]
    assert "Шарф и шапка" in advice["recommended"]

def test_hot_weather(engine):
    weather_summary = {
        "temperature_min": 25,
        "temperature_max": 35,
        "conditions": ["clear"],
        "will_rain": False,
        "will_snow": False,
        "strong_wind": False
    }

    advice = engine.generate_packing_advice(weather_summary)

    assert "Солнцезащитный крем — ожидается жаркая погода" in advice["recommended"]
    assert "Лёгкая одежда для прогулок — тёплая погода" in advice["optional"]

def test_cold_weather(engine):
    weather_summary = {
        "temperature_min": -10,
        "temperature_max": -2,
        "conditions": ["clear"],
        "will_rain": False,
        "will_snow": False,
        "strong_wind": False
    }

    advice = engine.generate_packing_advice(weather_summary)

    assert "Тёплая зимняя куртка — температура ниже 5°C" in advice["essentials"]

def test_temperature_range(engine):
    weather_summary = {
        "temperature_min": 2,
        "temperature_max": 18,
        "conditions": ["clear"],
        "will_rain": False,
        "will_snow": False,
        "strong_wind": False
    }

    advice = engine.generate_packing_advice(weather_summary)

    assert "Одежда слоями — ожидаются перепады температур" in advice["optional"]

def test_strong_wind(engine):
    weather_summary = {
        "temperature_min": 10,
        "temperature_max": 15,
        "conditions": ["clear"],
        "will_rain": False,
        "will_snow": False,
        "strong_wind": True
    }

    advice = engine.generate_packing_advice(weather_summary)

    assert "Ветрозащитная куртка — ожидается сильный ветер" in advice["essentials"]

def test_default_advice(engine):
    weather_summary = {
        "temperature_min": 20,
        "temperature_max": 22,
        "conditions": ["clear"],
        "will_rain": False,
        "will_snow": False,
        "strong_wind": False
    }

    advice = engine.generate_packing_advice(weather_summary)

    assert len(advice["essentials"]) > 0