from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List

class Period(BaseModel):
    arrival: date
    return_date: date = Field(..., alias="return")

class WeatherSummary(BaseModel):
    temperature_min: float
    temperature_max: float
    conditions: List[str]
    will_rain: bool
    will_snow: bool
    strong_wind: bool

class PackingAdvice(BaseModel):
    essentials: List[str]
    recommended: List[str]
    optional: List[str]

class PackingResponse(BaseModel):
    airport_code: str
    city: str
    country: str
    period: Period
    weather_summary: WeatherSummary
    packing_advice: PackingAdvice
    cached: bool = False
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class HealthCheckResponse(BaseModel):
    status: str = "ok"
    mongodb: str
    cities_api: str
    weather_api: str