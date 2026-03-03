#-------------------------------------------------------------------
#
# This code is copyright 2025 by the author.
# Use and modification allowed for personal and educational purposes.
#
#-------------------------------------------------------------------

"""
My Little Tree — дерево в терминале, которое растёт в течение дня.

- Отслеживает, как долго программа открыта (рост со временем сессии).
- Учитывает время суток: днём дерево «растёт», ночью — спит.
- Погода запрашивается у Open-Meteo (без API-ключа):
  - при снеге горшочек завален снегом, снежинки вокруг;
  - при дожде листочки опадают, горшок мокрый;
  - ясно — полная крона.

Запуск: python main.py
Выход: Ctrl+C
"""

import sys
import time
import signal
from datetime import datetime

from weather import fetch_weather, get_location_by_ip
from tree_art import build_tree, format_status

# Интервалы обновления (секунды)
WEATHER_REFRESH_INTERVAL = 300  # погода раз в 5 минут
SCREEN_REFRESH_INTERVAL = 0.5   # экран чаще — плавное покачивание

# ANSI
CLEAR = "\033[2J\033[H"  # очистка экрана и курсор в (1,1)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def clear_screen():
    print(CLEAR, end="", flush=True)


def main():
    start_time = time.monotonic()
    last_weather_time = 0.0
    cached_weather = None
    lat, lon = None, None

    def signal_handler(sig, frame):
        clear_screen()
        print("До встречи! 🌳")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTSTP"):
        signal.signal(signal.SIGTSTP, signal_handler)

    try:
        lat, lon = get_location_by_ip()
    except Exception:
        pass

    while True:
        now = time.monotonic()
        session_seconds = now - start_time

        # Обновляем погоду периодически (напрямую с Open-Meteo)
        if cached_weather is None or (now - last_weather_time) >= WEATHER_REFRESH_INTERVAL:
            try:
                cached_weather = fetch_weather(lat, lon)
                last_weather_time = now
            except Exception:
                pass
            if cached_weather is None:
                cached_weather = {
                    "description": "нет данных",
                    "temp": 15.0,
                    "is_rain": False,
                    "is_snow": False,
                }

        # Локальное время (часы для дня/ночи)
        local_now = datetime.now()
        local_hour = local_now.hour
        session_minutes = session_seconds / 60.0

        is_night = not (6 <= local_hour < 22)

        tree_picture = build_tree(
            local_hour=local_hour,
            session_minutes=session_minutes,
            weather_description=cached_weather["description"],
            is_rain=cached_weather.get("is_rain", False),
            is_snow=cached_weather.get("is_snow", False),
            is_night=is_night,
            show_snowflakes=True,
            time_seconds=now,
        )

        status_line = format_status(
            local_now,
            session_seconds,
            cached_weather["description"],
            cached_weather.get("temp", 15.0),
        )

        clear_screen()
        print(tree_picture)
        print()
        print(DIM + status_line + RESET)
        print()
        print("  Ctrl+C — выход")
        sys.stdout.flush()

        time.sleep(SCREEN_REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
