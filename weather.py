#-------------------------------------------------------------------
#
# This code is copyright 2025 by the author.
# Use and modification allowed for personal and educational purposes.
#
#-------------------------------------------------------------------

"""
Погода: сначала запрос на хост пользователя (localhost), иначе Open-Meteo.
"""

import json
import urllib.request
import urllib.error

DEFAULT_WEATHER_HOST_URL = "http://127.0.0.1:8765/weather"

# Коды погоды WMO (Open-Meteo): снег, дождь, ясно
WEATHER_SNOW_CODES = {71, 73, 75, 77, 85, 86}
WEATHER_RAIN_CODES = {51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
WEATHER_FOG_CODES = {45, 48}


def fetch_weather_from_host(host_url=None):
    """
    Запросить погоду у локального сервиса на хосте пользователя.
    host_url — например http://127.0.0.1:8765/weather
    Возвращает dict как fetch_weather или None при ошибке.
    """
    if host_url is None:
        host_url = DEFAULT_WEATHER_HOST_URL
    try:
        req = urllib.request.Request(
            host_url,
            headers={"User-Agent": "MyLittleTree/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return None

    return {
        "temp": float(data.get("temp", 15.0)),
        "code": int(data.get("code", 0)),
        "precipitation": float(data.get("precipitation", 0) or 0),
        "is_rain": bool(data.get("is_rain", False)),
        "is_snow": bool(data.get("is_snow", False)),
        "is_fog": bool(data.get("is_fog", False)),
        "description": str(data.get("description", "нет данных")),
    }


def get_location_by_ip():
    """Получить приближённые широту и долготу по IP (без ключа)."""
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=lat,lon",
            headers={"User-Agent": "MyLittleTree/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("lat", 55.75), data.get("lon", 37.62)
    except Exception:
        return 55.75, 37.62  # Москва по умолчанию


def fetch_weather(lat=None, lon=None):
    """
    Запросить текущую погоду у Open-Meteo.
    Возвращает dict: temp, code, precipitation, is_rain, is_snow, is_fog, description.
    """
    if lat is None or lon is None:
        lat, lon = get_location_by_ip()

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,precipitation"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MyLittleTree/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError:
        return _fallback_weather()
    except (json.JSONDecodeError, KeyError):
        return _fallback_weather()

    current = data.get("current") or {}
    code = int(current.get("weather_code", 0))
    temp = current.get("temperature_2m", 15.0)
    precip = float(current.get("precipitation", 0) or 0)

    is_snow = code in WEATHER_SNOW_CODES
    is_rain = code in WEATHER_RAIN_CODES or (precip > 0 and not is_snow)
    is_fog = code in WEATHER_FOG_CODES

    if is_snow:
        description = "снег"
    elif is_rain:
        description = "дождь"
    elif is_fog:
        description = "туман"
    elif code == 0:
        description = "ясно"
    elif code in (1, 2):
        description = "переменная облачность"
    elif code == 3:
        description = "облачно"
    else:
        description = "погода " + str(code)

    return {
        "temp": temp,
        "code": code,
        "precipitation": precip,
        "is_rain": is_rain,
        "is_snow": is_snow,
        "is_fog": is_fog,
        "description": description,
    }


def _fallback_weather():
    """Погода при недоступности API."""
    return {
        "temp": 15.0,
        "code": 0,
        "precipitation": 0,
        "is_rain": False,
        "is_snow": False,
        "is_fog": False,
        "description": "нет данных",
    }
