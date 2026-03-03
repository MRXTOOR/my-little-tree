#-------------------------------------------------------------------
#
# This code is copyright 2025 by the author.
# Use and modification allowed for personal and educational purposes.
#
#-------------------------------------------------------------------

"""
Локальный сервис погоды на хосте пользователя.
Запускается на 127.0.0.1:8765; по запросу GET /weather отдаёт JSON с погодой.
Погоду получает через Open-Meteo (геолокация по IP).
Запуск: python3 weather_server.py
"""

import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8765
HOST = "127.0.0.1"

WEATHER_SNOW_CODES = {71, 73, 75, 77, 85, 86}
WEATHER_RAIN_CODES = {51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
WEATHER_FOG_CODES = {45, 48}


def get_location():
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=lat,lon",
            headers={"User-Agent": "MyLittleTree-WeatherServer/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("lat", 55.75), data.get("lon", 37.62)
    except Exception:
        return 55.75, 37.62


def fetch_weather():
    lat, lon = get_location()
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,precipitation"
    )
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "MyLittleTree-WeatherServer/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return {
            "temp": 15.0,
            "code": 0,
            "precipitation": 0,
            "is_rain": False,
            "is_snow": False,
            "is_fog": False,
            "description": "нет данных",
        }

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


class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip("/") == "/weather":
            weather = fetch_weather()
            body = json.dumps(weather, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    server = HTTPServer((HOST, PORT), WeatherHandler)
    print(f"Погодный сервис: http://{HOST}:{PORT}/weather")
    print("Остановка: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nВыход.")
    server.server_close()


if __name__ == "__main__":
    main()
