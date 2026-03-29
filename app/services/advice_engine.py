from typing import Dict, Any, List, Tuple, Set
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

    # Обязательные поля для валидации
    REQUIRED_FIELDS = [
        "temperature_2m_min",
        "temperature_2m_max",
        "precipitation_sum",
        "windspeed_10m_max",
        "weathercode"
    ]

    def analyze_weather(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:

        # Проверяем наличие daily
        if not weather_data:
            logger.error("Weather data is None or empty")
            raise ValueError("Weather data is empty")

        daily = weather_data.get("daily")
        if not daily:
            logger.error("Missing 'daily' field in weather data")
            raise ValueError("Missing 'daily' field in weather data")

        # Проверяем наличие всех обязательных полей
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in daily:
                missing_fields.append(field)

        if missing_fields:
            logger.error(f"Missing required fields in weather data: {missing_fields}")
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Проверяем, что все поля имеют данные
        temps_min = daily["temperature_2m_min"]
        temps_max = daily["temperature_2m_max"]
        precip = daily["precipitation_sum"]
        wind_speed = daily["windspeed_10m_max"]
        weather_codes = daily["weathercode"]

        # Проверяем, что поля не пустые
        if not temps_min or not temps_max:
            logger.error("Temperature data is empty")
            raise ValueError("Temperature data is empty")

        # Проверяем, что все поля имеют одинаковую длину
        lengths = [
            len(temps_min),
            len(temps_max),
            len(precip),
            len(wind_speed),
            len(weather_codes)
        ]

        if len(set(lengths)) != 1:
            logger.error(f"Inconsistent data lengths: {lengths}")
            raise ValueError("Inconsistent data lengths in weather data")

        # Если данных нет (0 дней) - это тоже ошибка
        if lengths[0] == 0:
            logger.error("No weather data for the specified period")
            raise ValueError("No weather data for the specified period")

        # Агрегируем данные за весь период
        try:
            # Минимальная и максимальная температура за период
            temp_min = min(temps_min)
            temp_max = max(temps_max)
        except (TypeError, ValueError) as e:
            logger.error(f"Error processing temperature data: {e}")
            raise ValueError("Invalid temperature data")

        # Анализируем погодные условия
        conditions = set()
        will_rain = False
        will_snow = False
        strong_wind = False

        try:
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

        except (TypeError, ValueError) as e:
            logger.error(f"Error processing weather conditions: {e}")
            raise ValueError("Invalid weather condition data")

        logger.info(f"Weather analysis completed: temp_min={temp_min}, temp_max={temp_max}, "
                    f"will_rain={will_rain}, will_snow={will_snow}, strong_wind={strong_wind}")

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
        conditions = weather_summary.get("conditions", [])

        # обязательно
        if will_rain:
            essentials.append("Зонт или дождевик — ожидаются дожди")

        if temp_max < 5:
            essentials.append("Тёплая зимняя куртка — температура ниже 5°C")
        elif 5 <= temp_max < 15:
            essentials.append(f"Тёплая куртка или пальто — температура {temp_min}–{temp_max}°C")
        elif temp_max >= 25:
            # Если жарко, не нужна теплая куртка
            pass

        if will_snow:
            essentials.append("Тёплая непромокаемая обувь, шапка и перчатки — ожидается снег")

        if strong_wind:
            essentials.append("Ветрозащитная куртка — ожидается сильный ветер")

        # рекомендуется
        if temp_min < 10:
            recommended.append("Свитер или джемпер — прохладная погода")

        if will_rain:
            recommended.append("Водонепроницаемая обувь")

        if temp_max > 25:
            recommended.append("Солнцезащитный крем — ожидается жаркая погода")

        if will_snow:
            recommended.append("Шарф и шапка")

        # опционально
        if temp_max > 20:
            optional.append("Лёгкая одежда для прогулок — тёплая погода")

        if temp_min < 5 and temp_max > 15:
            optional.append("Одежда слоями — ожидаются перепады температур")

        if "fog" in conditions:
            optional.append("Яркая одежда — видимость снижена из-за тумана")

        # Если нет обязательных советов, добавляем дефолтный
        if not essentials:
            if temp_max >= 15 and temp_max <= 25:
                essentials.append("Комфортная одежда по сезону — погода благоприятная")
            else:
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