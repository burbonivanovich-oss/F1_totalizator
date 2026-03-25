"""
Admin commands (restricted to ADMIN_IDS):
  /result <RACE_ID> <TYPE> <DRIVER1> <DRIVER2> ... <DRIVER_N>
    TYPE: race (16 drivers) | sprint (10 drivers)
    Example: /result MON race VER LEC HAM RUS ALO STR NOR PIA SAI ALB HUL BOR COL GAS LAW LIN
    Example: /result MON sprint VER LEC HAM RUS ALO STR NOR PIA SAI ALB (10 total)
"""
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from data.calendar_2026 import RACE_BY_ID
from data.drivers import DRIVER_BY_ID
from handlers.leaderboard import process_results_and_score


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Нет доступа.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Формат: /result <RACE_ID> <race|sprint> <DRIVER1> <DRIVER2> ...\n"
            "Для гонки нужно 16 гонщиков, для спринта — 10.\n"
            "Пример: /result MON race VER LEC HAM RUS ALO STR NOR PIA SAI ALB HUL BOR COL GAS LAW LIN"
        )
        return

    race_id = args[0].upper()
    race_type = args[1].lower()
    drivers = [d.upper() for d in args[2:]]

    if race_id not in RACE_BY_ID:
        await update.message.reply_text(f"Гонка {race_id!r} не найдена.")
        return

    if race_type not in ("race", "sprint"):
        await update.message.reply_text(
            f"Неверный тип {race_type!r}. Используй: race или sprint"
        )
        return

    expected_count = 16 if race_type == "race" else 10
    if len(drivers) != expected_count:
        await update.message.reply_text(
            f"Для {race_type} нужно {expected_count} гонщиков, получено {len(drivers)}."
        )
        return

    for driver_id in drivers:
        if driver_id not in DRIVER_BY_ID:
            await update.message.reply_text(f"Гонщик {driver_id!r} не найден.")
            return

    is_sprint = race_type == "sprint"
    summary = await process_results_and_score(race_id, is_sprint, drivers, context.bot)
    await update.message.reply_text(f"✅ Результаты сохранены:\n{summary}")
