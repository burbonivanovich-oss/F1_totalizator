import os
import sys
# Ensure project root (parent of handlers/) is always in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from data.calendar_2026 import RACES_2026
from data.drivers import DRIVERS


def _race_status(race: dict) -> str:
    now = datetime.now(timezone.utc)
    if race["race_time"] < now:
        return "✅"
    return "🔜"


async def show_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(timezone.utc)
    lines = ["🏁 <b>Календарь Формулы 1 — 2026</b>\n"]

    for race in RACES_2026:
        status = _race_status(race)
        sprint_tag = " 🟣 Sprint" if race["sprint_time"] else ""
        date_str = race["race_time"].strftime("%d %b %H:%M UTC")
        lines.append(
            f"{status} <b>{race['flag']} {race['name']}</b>{sprint_tag}\n"
            f"    📍 {race['circuit']}\n"
            f"    🕒 {date_str}\n"
        )

    text = "\n".join(lines)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=kb
        )
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def show_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Group drivers by team
    teams: dict[str, list] = {}
    for d in DRIVERS:
        teams.setdefault(d["team"], []).append(d)

    lines = ["🏎 <b>Гонщики Ф1 — 2026</b>\n"]
    for team, drivers in teams.items():
        lines.append(f"<b>{team}</b>")
        for d in drivers:
            lines.append(f"  #{d['number']} {d['full_name']}")
        lines.append("")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "\n".join(lines), parse_mode="HTML", reply_markup=kb
        )
    else:
        await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)
