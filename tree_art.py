#-------------------------------------------------------------------
#
# This code is copyright 2025 by the author.
# Procedural bonsai algorithm inspired by bonsai.sh (jallbrit).
#
#-------------------------------------------------------------------

"""
Процедурная генерация бонсай в терминале (в духе bonsai.sh).
Ветвление, ствол, листья на сетке; рост по времени сессии и времени суток;
погода влияет на символы листьев и базу; плавное покачивание.
"""

import math
import random
import re

COLS = 48
ROWS = 14
TREE_WIDTH = 52
SWAY_AMPLITUDE = 2
SWAY_PERIOD_SEC = 6.0

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
DARK_GREEN = "\033[38;5;22m"
BROWN = "\033[38;5;172m"
DARK_BROWN = "\033[38;5;130m"
WHITE = "\033[37m"
GRAY = "\033[38;5;243m"


def _is_daytime(hour):
    return 6 <= hour < 22


def _growth_factor(local_hour, session_minutes):
    day_factor = 0.4 if _is_daytime(local_hour) else 0.1
    session_factor = min(1.0, session_minutes / 240.0) * 0.6
    return min(1.0, day_factor + session_factor)


def _base_art(is_rain, is_snow, is_night):
    if is_snow:
        return [
            GRAY + ":" + GREEN + "___________" + WHITE + "./~~\\." + GREEN + "___________" + GRAY + ":" + RESET,
            " \\                          /" + RESET,
            "  \\________________________/" + RESET,
            "  (_)                    (_)" + RESET,
        ]
    if is_rain:
        return [
            GRAY + "(" + GREEN + "---" + DARK_BROWN + "./~~\\." + GREEN + "---" + GRAY + ")" + RESET,
            " (          )" + RESET,
            "  (________)" + RESET,
        ]
    return [
        GRAY + ":" + GREEN + "___________" + DARK_BROWN + "./~~\\." + GREEN + "___________" + GRAY + ":" + RESET,
        " \\                          /" + RESET,
        "  \\________________________/" + RESET,
        "  (_)                    (_)" + RESET,
    ]


def _grow_bonsai(growth, leaf_chars, is_night):
    life_start = 8 + int(growth * 20)
    multiplier = min(20, 2 + int(growth * 5))
    branches_max = multiplier * 110
    shoots_max = multiplier

    grid = [[" " for _ in range(COLS)] for _ in range(ROWS)]
    list_changed = [-1] * ROWS
    state = {"branches": 0, "shoots": 0, "shoot_type": None}

    def set_cell(y, x, s):
        if 0 <= y < ROWS and 0 <= x < COLS:
            grid[y][x] = s
            if x > list_changed[y]:
                list_changed[y] = x

    def branch(x, y, btype, life):
        state["branches"] += 1
        dx, dy = 0, 0

        while life > 0:
            life -= 1

            if btype in ("shootLeft", "shootRight"):
                r = random.randint(0, 9)
                dy = -1 if r <= 1 else (1 if r >= 8 else 0)
            elif btype == "dying":
                r = random.randint(0, 9)
                dy = -1 if r <= 1 else (1 if r >= 9 else 0)
            else:
                dy = 0
                if life != life_start and random.randint(0, 9) > 2:
                    dy = -1

            if dy > 0 and y >= ROWS - 1:
                dy = 0
            if btype == "trunk" and life < 4:
                dy = 0

            if btype == "shootLeft":
                r = random.randint(0, 9)
                dx = -2 if r <= 1 else (-1 if r <= 5 else (0 if r <= 8 else 1))
            elif btype == "shootRight":
                r = random.randint(0, 9)
                dx = 2 if r <= 1 else (1 if r <= 5 else (0 if r <= 8 else -1))
            elif btype == "dying":
                dx = random.randint(-3, 3)
            else:
                dx = random.randint(-1, 1)

            if state["branches"] < branches_max:
                if life < 3:
                    branch(x, y, "dead", life)
                elif btype == "trunk" and life < multiplier + 2:
                    branch(x, y, "dying", life)
                elif btype in ("shootLeft", "shootRight") and life < multiplier + 2:
                    branch(x, y, "dying", life)
                elif (btype == "trunk" and life < life_start - 8 and
                      (random.randint(0, max(1, 16 - multiplier)) == 0 or
                      (life % 5 == 0 and life > 5))):
                    if random.randint(0, 2) == 0 and life > 7:
                        branch(x, y, "trunk", life)
                    elif state["shoots"] < shoots_max:
                        tmp_life = max(0, life + multiplier - 2)
                        tmp_type = "shootRight" if (state["shoots"] == 0 and random.randint(0, 1) == 0) else "shootLeft"
                        if state["shoots"] > 0:
                            tmp_type = "shootLeft" if state["shoot_type"] == "shootRight" else "shootRight"
                        state["shoot_type"] = tmp_type
                        state["shoots"] += 1
                        branch(x, y, tmp_type, tmp_life)

            x += dx
            y += dy

            if x < 0 or x >= COLS or y < 0 or y >= ROWS:
                return

            if life < 3:
                ch = leaf_chars[random.randint(0, len(leaf_chars) - 1)]
                color = DARK_GREEN if is_night else GREEN
                set_cell(y, x, color + ch + RESET)
            else:
                color = DARK_BROWN if random.randint(0, 3) == 0 else BROWN
                if btype == "dying":
                    color = DARK_GREEN
                if btype == "trunk":
                    ch = "\\" if dx < 0 else ("/" if dx > 0 else ("/" if random.randint(0, 1) == 0 else "|"))
                    if dy == 0:
                        ch = "/" if random.randint(0, 1) == 0 else "~"
                elif btype == "shootLeft":
                    ch = "\\" if dx <= -1 else ("/" if dx >= 1 else ("/" if random.randint(0, 1) == 0 else "|"))
                    if dy > 0:
                        ch = "/"
                    elif dy == 0:
                        ch = "\\" if random.randint(0, 1) == 0 else "_"
                elif btype == "shootRight":
                    ch = "/" if dx >= 1 else ("\\" if dx <= -1 else ("\\" if random.randint(0, 1) == 0 else "|"))
                    if dy > 0:
                        ch = "\\"
                    elif dy == 0:
                        ch = "_" if random.randint(0, 1) == 0 else "/"
                else:
                    ch = ["/", "\\", "|", "-"][random.randint(0, 3)]
                set_cell(y, x, color + ch + RESET)

    start_x = COLS // 2
    start_y = ROWS - 1
    branch(start_x, start_y, "trunk", life_start)

    out = []
    for row in range(ROWS):
        end = list_changed[row] + 1 if list_changed[row] >= 0 else 0
        out.append("".join(grid[row][c] for c in range(end)))
    return out


def build_tree(
    local_hour,
    session_minutes,
    weather_description,
    is_rain,
    is_snow,
    is_night,
    show_snowflakes=True,
    time_seconds=0.0,
):
    growth = _growth_factor(local_hour, session_minutes)
    seed = int(session_minutes) * 60 + int(growth * 20)
    random.seed(seed)

    leaf_chars = ["*"] if is_snow else ([".", "·"] if is_rain else ["&", "*", "+", "%"])

    tree_lines = _grow_bonsai(growth, leaf_chars, is_night)
    base_lines = _base_art(is_rain, is_snow, is_night)

    # Часть «дерево» — качается; часть «база» — неподвижна
    tree_part = []
    if show_snowflakes and (is_snow or is_rain):
        c = "*" if is_snow else "."
        for _ in range(2):
            tree_part.append(DIM + "".join(c if random.random() > 0.88 else " " for _ in range(TREE_WIDTH)) + RESET)
    tree_part.extend(tree_lines)
    if is_rain and growth >= 0.3:
        tree_part.append(DIM + "  " + "".join("." if random.random() > 0.6 else " " for _ in range(24)) + RESET)

    base_part = list(base_lines)
    if show_snowflakes and (is_snow or is_rain):
        c = "*" if is_snow else "."
        base_part.append(DIM + "".join(c if random.random() > 0.9 else " " for _ in range(TREE_WIDTH)) + RESET)

    sway = int(round(SWAY_AMPLITUDE * math.sin(2 * math.pi * time_seconds / SWAY_PERIOD_SEC)))

    def strip_ansi(s):
        return re.sub(r"\033\[[0-9;]*m", "", s)

    num_tree = len(tree_part)
    # Изгиб: верх качается, низ (у горшка) неподвижен — ветви гнутся от основания
    def pad_tree_line(line, row_index):
        plain_len = len(strip_ansi(line))
        center = (TREE_WIDTH - plain_len) // 2
        if num_tree <= 1:
            sway_row = sway
        else:
            # row_index 0 = верх = полное качание; row_index num_tree-1 = низ = 0
            factor = 1.0 - row_index / (num_tree - 1)
            sway_row = int(round(sway * factor))
        left = max(0, center + sway_row)
        return " " * left + line

    def pad_base_line(line):
        plain_len = len(strip_ansi(line))
        left = max(0, (TREE_WIDTH - plain_len) // 2)
        return " " * left + line

    padded_tree = [pad_tree_line(line, i) for i, line in enumerate(tree_part)]
    padded_base = [pad_base_line(line) for line in base_part]

    return "\n".join(padded_tree + padded_base)


def format_status(local_time, session_seconds, weather, temp):
    minutes = int(session_seconds // 60)
    hours = minutes // 60
    mins = minutes % 60
    uptime_str = f"{hours} ч {mins} мин" if hours else f"{mins} мин"
    time_str = local_time.strftime("%H:%M")
    return f"  Время: {time_str}  |  Открыто: {uptime_str}  |  {weather}  {temp:+.0f}°C"
