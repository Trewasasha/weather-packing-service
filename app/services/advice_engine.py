from typing import Dict, Any, List, Tuple
from datetime import date
import logging

logger = logging.getLogger(__name__)

class AdviceEngine:
    # Константы для погодных условий
    WMO_CODES = {
        "clear": [0],
        "partly_cloudy": [1, 2, 3],
        "fog": [45, 48],
        "drizzle": [51, 53, 55, 56, 57],
        "rain": [61, 63, 65, 66, 67, 80, 81, 82],
        "snow": [71, 73, 75, 77, 85, 86],
        "thunderstorm": [95, 96, 99]
    }

    def analyze_weather(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализ погодных данных за весь период
        """
        daily = weather_data.get("daily", {})

        # Агрегируем данные за весь период
        temps_min = daily.get("temperature_2m_min", [])
        temps_max = daily.get("temperature_2m_max", [])
        precip = daily.get("precipitation_sum", [])
        wind_speed = daily.get("windspeed_10m_max", [])
        weather_codes = daily.get("weathercode", [])

        if not temps_min or not temps_max:
            return {
                "temperature_min": 0,
                "temperature_max": 0,
                "conditions": ["unknown"],
                "will_rain": False,
                "will_snow": False,
                "strong_wind": False
            }

        # Минимальная и максимальная температура за период
        temp_min = min(temps_min)
        temp_max = max(temps_max)

        # Анализируем погодные условия
        conditions = set()
        will_rain = False
        will_snow = False
        strong_wind = any(w > 40 for w in wind_speed) if wind_speed else False

        for code in weather_codes:
            condition = self._get_weather_condition(code)
            conditions.add(condition)

            if condition in ["rain", "drizzle", "thunderstorm"]:
                will_rain = True
            elif condition == "snow":
                will_snow = True

        # Проверяем осадки через precipitation_sum
        if precip and any(p > 0 for p in precip):
            will_rain = True

        return {
            "temperature_min": round(temp_min, 1),
            "temperature_max": round(temp_max, 1),
            "conditions": list(conditions),
            "will_rain": will_rain,
            "will_snow": will_snow,
            "strong_wind": strong_wind
        }

    def _get_weather_condition(self, code: int) -> str:
        """Определение погодного условия по WMO коду"""
        for condition, codes in self.WMO_CODES.items():
            if code in codes:
                return condition
        return "unknown"

    def generate_packing_advice(self, weather_summary: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Генерация советов по упаковке вещей на основе анализа погоды
        """
        essentials = []
        recommended = []
        optional = []

        temp_min = weather_summary["temperature_min"]
        temp_max = weather_summary["temperature_max"]
        will_rain = weather_summary["will_rain"]
        will_snow = weather_summary["will_snow"]
        strong_wind = weather_summary["strong_wind"]
        conditions = weather_summary["conditions"]

        if will_rain:
            essentials.append("Зонт или дождевик — ожидаются дожди")

        if temp_max < 5:
            essentials.append("Тёплая зимняя куртка — температура ниже 5°C")
        elif 5 <= temp_max < 15:
            essentials.append(f"Тёплая куртка или пальто — температура {temp_min}–{temp_max}°C")

        if will_snow:
            essentials.append("Тёплая непромокаемая обувь, шапка и перчатки — ожидается снег")

        if strong_wind:
            essentials.append("Ветрозащитная куртка — ожидается сильный ветер")

        # RECOMMENDED
        if temp_min < 10:
            recommended.append("Свитер или джемпер — прохладная погода")

        if will_rain:
            recommended.append("Водонепроницаемая обувь")

        if temp_max > 25:
            recommended.append("Солнцезащитный крем — ожидается жаркая погода")

        if will_snow:
            recommended.append("Шарф и шапка")

        # OPTIONAL
        if temp_max > 20:
            optional.append("Лёгкая одежда для прогулок — тёплая погода")

        if temp_min < 5 and temp_max > 15:
            optional.append("Одежда слоями — ожидаются перепады температур")

        if "fog" in conditions:
            optional.append("Яркая одежда — видимость снижена из-за тумана")

        if not essentials:
            essentials.append("Одежда по сезону — проверьте прогноз перед вылетом")

        return {
            "essentials": self._deduplicate_and_sort(essentials),
            "recommended": self._deduplicate_and_sort(recommended),
            "optional": self._deduplicate_and_sort(optional)
        }

    def _deduplicate_and_sort(self, items: List[str]) -> List[str]:
        seen = set()
        unique_items = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        return unique_items