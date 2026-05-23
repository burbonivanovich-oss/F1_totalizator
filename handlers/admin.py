"""
Admin commands (restricted to ADMIN_IDS):

  /result <RACE_ID> <race|sprint> <DRIVER1> ... <DRIVER_N>
      Manually enter race results (16 drivers for race, 10 for sprint).
      Example: /result MON race VER LEC HAM RUS ALO STR NOR PIA SAI ALB HUL BOR COL GAS LAW LIN

  /reanalyze <RACE_ID> [race|sprint]
      Force re-fetch results from FastF1 and recalculate scores.
      Example: /reanalyze AUS race
      Example: /reanalyze CHN sprint

  /test_results <RACE_ID> [race|sprint]
      Fetch and display race results from FastF1 without saving.
      Example: /test_results AUS race

  /admin_stats
      Show all registered users with their point totals.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from handlers.calendar_handler import RACE_BY_ID, DRIVER_BY_ID
from handlers.leaderboard import process_results_and_score
from data.race_mappings import RACE_ID_TO_FASTF1_NAME

logger = logging.getLogger(__name__)

def _check_admin(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_admin(update):
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

    race_id   = args[0].upper()
    race_type = args[1].lower()
    drivers   = [d.upper() for d in args[2:]]

    if race_id not in RACE_BY_ID:
        await update.message.reply_text(f"Гонка {race_id!r} не найдена.")
        return

    if race_type not in ("race", "sprint"):
        await update.message.reply_text(f"Неверный тип {race_type!r}. Используй: race или sprint")
        return

    expected = 16 if race_type == "race" else 10
    if len(drivers) != expected:
        await update.message.reply_text(
            f"Для {race_type} нужно {expected} гонщиков, получено {len(drivers)}."
        )
        return

    if len(set(drivers)) != len(drivers):
        dupes = [d for d in drivers if drivers.count(d) > 1]
        await update.message.reply_text(f"Дублирующиеся гонщики: {', '.join(set(dupes))}")
        return

    for driver_id in drivers:
        if driver_id not in DRIVER_BY_ID:
            await update.message.reply_text(f"Гонщик {driver_id!r} не найден.")
            return

    is_sprint = race_type == "sprint"
    summary = await process_results_and_score(race_id, is_sprint, drivers, context.bot)
    await update.message.reply_text(f"✅ Результаты сохранены:\n{summary}")


async def reanalyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force re-fetch from FastF1 and recalculate scores for a given race."""
    if not _check_admin(update):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Формат: /reanalyze <RACE_ID> [race|sprint]\n"
            "Пример: /reanalyze AUS race\n"
            "Пример: /reanalyze CHN sprint\n\n"
            "По умолчанию ищет гонку (race)."
        )
        return

    import asyncio
    import fastf1
    import database as db
    from data.drivers import DRIVERS

    race_id   = args[0].upper().strip()
    race_type = args[1].lower().strip() if len(args) > 1 else "race"
    is_sprint = race_type == "sprint"

    if race_id not in RACE_BY_ID:
        await update.message.reply_text(f"❌ Гонка {race_id!r} не найдена.")
        return

    race = RACE_BY_ID[race_id]
    kind = "спринта" if is_sprint else "гонки"
    msg  = await update.message.reply_text(
        f"⏳ Загружаю результаты {kind} {race['flag']} {race['name']} из FastF1..."
    )

    # Import the shared fetch function from scheduler
    from scheduler import _fetch_and_save_results

    try:
        fetched = await _fetch_and_save_results(race, is_sprint)
        if not fetched:
            await msg.edit_text(
                f"❌ Не удалось получить результаты {kind} {race['name']} из FastF1.\n"
                "Возможно, данные ещё не доступны или гонка не проводилась."
            )
            return

        result = await db.get_result(race_id, is_sprint)
        if not result:
            await msg.edit_text("❌ Результаты не найдены в БД после загрузки.")
            return

        summary = await process_results_and_score(
            race_id, is_sprint, result["positions"], context.bot
        )
        positions_preview = "\n".join(
            f"{i+1}. {code}" for i, code in enumerate(result["positions"][:10])
        )
        suffix = f"\n... ещё {len(result['positions']) - 10}" if len(result["positions"]) > 10 else ""
        await msg.edit_text(
            f"✅ <b>Пересчёт завершён!</b>\n\n"
            f"{race['flag']} <b>{race['name']}</b> — {kind}\n\n"
            f"<b>Топ-10:</b>\n{positions_preview}{suffix}\n\n"
            f"<b>Очки участников:</b>\n{summary}",
            parse_mode="HTML",
        )

    except Exception as e:
        logger.exception("Error in reanalyze_command for %s", race_id)
        await msg.edit_text(f"❌ Ошибка: {e}")


async def test_results_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display race results from FastF1 (preview, no DB save)."""
    if not _check_admin(update):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Формат: /test_results <RACE_ID> [race|sprint]\n"
            "Пример: /test_results AUS race\n"
            "Пример: /test_results CHN sprint\n\n"
            "По умолчанию ищет гонку (race)."
        )
        return

    import asyncio
    import fastf1

    race_id   = args[0].upper().strip()
    race_type = args[1].lower().strip() if len(args) > 1 else "race"
    is_sprint = race_type == "sprint"

    logger.info("test_results_command: race_id=%s, type=%s", race_id, race_type)

    if race_id not in RACE_BY_ID:
        await update.message.reply_text(f"❌ Гонка {race_id!r} не найдена.")
        return

    race = RACE_BY_ID[race_id]
    kind = "Спринта" if is_sprint else "Гонки"
    msg  = await update.message.reply_text(
        f"⏳ Загружаю результаты {kind} {race['name']}..."
    )

    try:
        code_to_number = {d["id"]: d["number"] for d in DRIVER_BY_ID.values()}
        number_to_code = {v: k for k, v in code_to_number.items()}

        gp_name = RACE_ID_TO_FASTF1_NAME.get(race_id)
        if not gp_name:
            await msg.edit_text(f"❌ Неизвестная гонка {race_id}")
            return

        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: fastf1.get_session(2026, gp_name, "S" if is_sprint else "R")
        )

        if not session:
            await msg.edit_text(f"❌ Сессия не найдена для {race['name']}")
            return

        await loop.run_in_executor(
            None,
            lambda: session.load(laps=False, telemetry=False, weather=False, messages=False)
        )

        results_df = session.results
        if results_df is None or len(results_df) == 0:
            await msg.edit_text("❌ Результаты не найдены. Данные ещё не доступны?")
            return

        lines    = [f"🏁 <b>Результаты {kind} {race['name']}</b>\n"]
        positions = []
        pos_num  = 1

        for _, row in results_df.iterrows():
            driver_code = None

            # Try Abbreviation first
            abbrev = str(row.get("Abbreviation", "") or "").upper().strip()
            if abbrev and abbrev in DRIVER_BY_ID:
                driver_code = abbrev

            # Fallback to DriverNumber
            if not driver_code:
                raw_num = row.get("DriverNumber") or row.get("Driver")
                if raw_num is not None:
                    try:
                        driver_code = number_to_code.get(int(raw_num))
                    except (ValueError, TypeError):
                        pass

            if not driver_code:
                lines.append(f"{pos_num}. ??? — #{row.get('DriverNumber', '?')}")
                pos_num += 1
                continue

            driver_data = DRIVER_BY_ID.get(driver_code, {})
            driver_name = driver_data.get("full_name", driver_code)
            lines.append(f"{pos_num}. {driver_code} — {driver_name}")
            positions.append(driver_code)
            pos_num += 1

        lines.append(f"\n✅ Классифицировано: {len(positions)}")
        await msg.edit_text("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.exception("Error in test_results_command for %s", race_id)
        await msg.edit_text(f"❌ Ошибка: {e}")


async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all registered users with their total points."""
    if not _check_admin(update):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    import database as db

    leaderboard = await db.get_leaderboard()
    all_users   = await db.get_all_users()

    scored_ids = {row["telegram_id"] for row in leaderboard}
    lines = [f"👥 <b>Пользователи ({len(all_users)})</b>\n"]

    for i, row in enumerate(leaderboard, 1):
        lines.append(
            f"{i}. <b>{row['full_name']}</b> — "
            f"{row['total_points']} очк. ({row['races_count']} гон.)"
        )

    # Users registered but without any score yet
    no_scores = [u for u in all_users if u["telegram_id"] not in scored_ids]
    if no_scores:
        lines.append("\n<i>Без оценённых гонок:</i>")
        for u in no_scores:
            uname = f"@{u['username']}" if u.get("username") else "без username"
            lines.append(f"  • {u['full_name']} ({uname})")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
