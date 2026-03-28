"""
Admin commands (restricted to ADMIN_IDS):
  /result <RACE_ID> <TYPE> <DRIVER1> <DRIVER2> ... <DRIVER_N>
    TYPE: race (16 drivers) | sprint (10 drivers)
    Example: /result MON race VER LEC HAM RUS ALO STR NOR PIA SAI ALB HUL BOR COL GAS LAW LIN
    Example: /result MON sprint VER LEC HAM RUS ALO STR NOR PIA SAI ALB (10 total)

  /test_results <RACE_ID> [race|sprint]
    Fetch and display race results from FastF1
    Example: /test_results AUS race
    Example: /test_results CHN sprint
"""
import os
import sys
# Ensure project root (parent of handlers/) is always in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from handlers.calendar_handler import RACE_BY_ID, DRIVER_BY_ID
from handlers.leaderboard import process_results_and_score

# Mapping from race ID to FastF1 GP name (full names that FastF1 understands)
RACE_ID_TO_FASTF1_NAME = {
    "AUS": "Australia",
    "CHN": "China",
    "JPN": "Japan",
    "MIA": "Miami",
    "CAN": "Canada",
    "MON": "Monaco",
    "ESP": "Spain",
    "AUT": "Austria",
    "GBR": "Britain",
    "BEL": "Belgium",
    "HUN": "Hungary",
    "NED": "Netherlands",
    "ITA": "Italy",
    "MAD": "Madrid",
    "AZE": "Azerbaijan",
    "SGP": "Singapore",
    "USA": "United States",
    "MEX": "Mexico",
    "BRA": "Brazil",
    "LVG": "Las Vegas",
    "QAT": "Qatar",
    "ABU": "Abu Dhabi",
}


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


async def test_results_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to fetch and display race results from FastF1."""
    import logging
    logger = logging.getLogger(__name__)

    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Нет доступа.")
        return

    args = context.args
    logger.info(f"test_results_command called with args: {args}")

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

    race_id = args[0].upper().strip()
    race_type = args[1].lower().strip() if len(args) > 1 else "race"
    is_sprint = race_type == "sprint"

    logger.info(f"Race ID: {race_id}, Type: {race_type}, Is Sprint: {is_sprint}")

    if race_id not in RACE_BY_ID:
        await update.message.reply_text(f"❌ Гонка {race_id!r} не найдена.")
        return

    race = RACE_BY_ID[race_id]
    race_name = race["name"]
    session_type = "Спринта" if is_sprint else "Гонки"

    msg = await update.message.reply_text(f"⏳ Загружаю результаты {session_type} {race_name}...")

    try:
        # Build mapping from driver_id (code) to number
        code_to_number = {d["id"]: d["number"] for d in DRIVER_BY_ID.values()}
        number_to_code = {v: k for k, v in code_to_number.items()}

        # Convert race ID to FastF1 GP name
        gp_name = RACE_ID_TO_FASTF1_NAME.get(race_id)
        if not gp_name:
            await msg.edit_text(f"❌ Неизвестная гонка {race_id}")
            return

        # Fetch from FastF1
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: fastf1.get_session(2026, gp_name, "S" if is_sprint else "R")
        )

        if not session:
            await msg.edit_text(f"❌ Сессия не найдена для {race_name}")
            return

        logger.info(f"Fetching session for {race_id} ({gp_name}) {race_type}")
        await loop.run_in_executor(None, lambda: session.load())

        results_df = session.results
        if results_df is None or len(results_df) == 0:
            await msg.edit_text(f"❌ Результаты не найдены")
            return

        # Extract positions
        positions = []
        lines = [f"🏁 <b>Результаты {session_type} {race_name}</b>\n"]

        for idx, row in results_df.iterrows():
            driver_number = row.get("DriverNumber") or row.get("Driver")

            if driver_number is None:
                continue

            try:
                driver_number = int(driver_number)
            except (ValueError, TypeError):
                logger.debug(f"Could not convert driver number {driver_number}")
                continue

            driver_code = number_to_code.get(driver_number)

            if not driver_code:
                continue

            driver_data = DRIVER_BY_ID.get(driver_code, {})
            driver_name = driver_data.get("full_name", "Unknown")

            lines.append(f"{idx + 1}. {driver_code} - {driver_name}")
            positions.append(driver_code)

        lines.append(f"\n✅ Финишировало: {len(positions)}")

        await msg.edit_text("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.exception(f"Error in test_results: {e}")
        await msg.edit_text(f"❌ Ошибка: {str(e)}")
