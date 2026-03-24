"""
Admin commands (restricted to ADMIN_IDS):
  /result <RACE_ID> <TYPE> <P1> <P2> <P3>
    TYPE: race | sprint
    Example: /result MON race VER LEC NOR
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
    if len(args) != 5:
        await update.message.reply_text(
            "Формат: /result <RACE_ID> <race|sprint> <P1> <P2> <P3>\n"
            "Пример: /result MON race VER LEC NOR"
        )
        return

    race_id, race_type, p1, p2, p3 = args
    race_id = race_id.upper()
    p1, p2, p3 = p1.upper(), p2.upper(), p3.upper()

    if race_id not in RACE_BY_ID:
        await update.message.reply_text(f"Гонка {race_id!r} не найдена.")
        return

    for driver_id in (p1, p2, p3):
        if driver_id not in DRIVER_BY_ID:
            await update.message.reply_text(f"Гонщик {driver_id!r} не найден.")
            return

    is_sprint = race_type.lower() == "sprint"
    summary = await process_results_and_score(race_id, is_sprint, p1, p2, p3, context.bot)
    await update.message.reply_text(f"✅ Результаты сохранены:\n{summary}")
