import os
import sys
from datetime import datetime, timezone

import pytz

# Ensure project root is in sys.path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from data.calendar_2026 import RACES_2026
from data.drivers import DRIVERS

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

RACE_BY_ID    = {r["id"]: r for r in RACES_2026}
DRIVER_BY_ID  = {d["id"]: d for d in DRIVERS}
SPRINT_RACE_IDS = {r["id"] for r in RACES_2026 if r["sprint_time"] is not None}


def get_driver_short(driver_id: str) -> str:
    d = DRIVER_BY_ID.get(driver_id)
    if not d:
        return driver_id
    return f"{d['name']} ({d['team']})"


RU_MONTHS = {
    1: "янв",  2: "фев",  3: "мар",  4: "апр",   5: "май",  6: "июн",
    7: "июл",  8: "авг",  9: "сен", 10: "окт",  11: "ноя", 12: "дек",
}


def _format_race_date(dt: datetime) -> str:
    return f"{dt.day} {RU_MONTHS[dt.month]} {dt.strftime('%H:%M')} UTC"


async def show_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(timezone.utc)
    # Find the next upcoming race so we can highlight it
    upcoming = [r for r in RACES_2026 if r["race_time"] >= now]
    next_race_id = upcoming[0]["id"] if upcoming else None

    lines = ["🏁 <b>Календарь Формулы 1 — 2026</b>\n"]

    for race in RACES_2026:
        is_past = race["race_time"] < now
        if race["id"] == next_race_id:
            status = "▶️"
        else:
            status = "✅" if is_past else "🔜"
        sprint_tag = " 🟣 Спринт" if race["sprint_time"] else ""
        date_str   = _format_race_date(race["race_time"])
        lines.append(
            f"{status} <b>{race['flag']} {race['name']}</b>{sprint_tag}\n"
            f"    📍 {race['circuit']}\n"
            f"    🕒 {date_str}\n"
        )

    text = "\n".join(lines)
    kb   = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")
    ]])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def show_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teams: dict[str, list] = {}
    for d in DRIVERS:
        teams.setdefault(d["team"], []).append(d)

    lines = ["🏎 <b>Гонщики Ф1 — 2026</b>\n"]
    for team, drivers in teams.items():
        lines.append(f"<b>{team}</b>")
        for d in drivers:
            lines.append(f"  #{d['number']} {d['full_name']}")
        lines.append("")

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")
    ]])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "\n".join(lines), parse_mode="HTML", reply_markup=kb
        )
    else:
        await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)
