"""
Scheduled jobs:
  - 1 hour before race: reminder "последний час для прогнозов"
  - 5 minutes before race: notification "приём прогнозов закрыт"
  - ~2 hours after race start: auto-fetch results from FastF1, save to DB, calculate scores
    (with up to 3 retries every 30 minutes if data not yet available)
"""
import os
import sys
# Ensure project root is always in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, timezone
import logging

from telegram.ext import Application

from handlers.calendar_handler import RACES_2026

logger = logging.getLogger(__name__)

# Delay before first result fetch attempt (minutes after race START time).
# A race takes ~1.5–2 h; 120 min gives the race time to finish before we fetch.
AUTO_ANALYZE_DELAY_MINUTES = 120

# Retry settings when FastF1 data is not yet available
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_MINUTES = 30

# FastF1 season year
F1_SEASON = 2026

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


def init_fastf1_cache():
    """Enable FastF1 disk cache to avoid re-downloading data on every run."""
    try:
        import fastf1
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".fastf1_cache")
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
        logger.info("FastF1 disk cache enabled at %s", cache_dir)
    except Exception:
        logger.warning("Could not enable FastF1 cache", exc_info=True)


async def _send_reminder(bot, race: dict, minutes_before: int, is_sprint: bool):
    from database import get_leaderboard  # lazy import to avoid circular deps

    users = await get_leaderboard()
    if not users:
        return

    kind = "спринта" if is_sprint else "гонки"
    race_name = f"{race['flag']} {race['name']}"

    if minutes_before == 5:
        text = (
            f"🔒 <b>Приём прогнозов закрыт!</b>\n\n"
            f"До старта {kind} <b>{race_name}</b> осталось 5 минут.\n"
            f"Удачи всем участникам! 🏎"
        )
    else:
        text = (
            f"⏰ <b>Напоминание!</b>\n\n"
            f"До старта {kind} <b>{race_name}</b> остался 1 час.\n"
            f"Не забудь оставить прогноз! 🏁"
        )

    for user in users:
        try:
            await bot.send_message(user["telegram_id"], text, parse_mode="HTML")
        except Exception:
            logger.exception("Failed to notify user %s", user["telegram_id"])


async def _fetch_and_save_results(race: dict, is_sprint: bool) -> bool:
    """
    Fetch race results from FastF1 and save to database.

    Uses Abbreviation column as primary driver lookup (direct 3-letter code),
    with DriverNumber mapping as fallback. Returns True if successful.
    """
    import asyncio
    import fastf1

    from database import save_result
    from data.drivers import DRIVERS
    from handlers.calendar_handler import DRIVER_BY_ID

    race_id = race["id"]
    race_name = race["name"]
    session_type = "Sprint" if is_sprint else "Race"

    try:
        # Both lookup strategies prepared upfront
        number_to_code = {d["number"]: d["id"] for d in DRIVERS}

        gp_name = RACE_ID_TO_FASTF1_NAME.get(race_id)
        if not gp_name:
            logger.warning("Unknown race ID %s — cannot fetch results", race_id)
            return False

        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: fastf1.get_session(F1_SEASON, gp_name, "S" if is_sprint else "R")
        )

        if not session:
            logger.warning("Could not find %s session for %s", session_type, race_name)
            return False

        # Load only the data we need (skip laps, telemetry, weather, messages)
        await loop.run_in_executor(
            None,
            lambda: session.load(laps=False, telemetry=False, weather=False, messages=False)
        )

        results_df = session.results

        if results_df is None or len(results_df) == 0:
            logger.warning("No results found for %s %s", race_name, session_type)
            return False

        positions = []
        for _, row in results_df.iterrows():
            driver_code = None

            # Strategy 1: use Abbreviation directly (e.g. "VER", "HAM")
            abbrev = str(row.get("Abbreviation", "") or "").upper().strip()
            if abbrev and abbrev in DRIVER_BY_ID:
                driver_code = abbrev

            # Strategy 2: fall back to DriverNumber → internal mapping
            if not driver_code:
                raw_number = row.get("DriverNumber") or row.get("Driver")
                if raw_number is not None:
                    try:
                        driver_code = number_to_code.get(int(raw_number))
                    except (ValueError, TypeError):
                        logger.debug("Could not parse driver number %r in %s", raw_number, race_name)

            if not driver_code:
                logger.debug(
                    "Unknown driver (Abbreviation=%r, Number=%r) in %s — skipping",
                    abbrev, row.get("DriverNumber"), race_name,
                )
                continue

            positions.append(driver_code)

        if not positions:
            logger.warning("No valid driver codes extracted for %s %s", race_name, session_type)
            return False

        await save_result(race_id, is_sprint, positions)
        logger.info("Fetched and saved %s results for %s: %s", session_type, race_name, positions)
        return True

    except Exception:
        logger.exception("Failed to fetch %s results for %s from FastF1", session_type, race_name)
        return False


async def _auto_analyze_race(context, race: dict, is_sprint: bool, attempt: int = 0):
    """
    Auto-analyze race results: fetch from FastF1, save, and calculate scores.
    If data is not yet available, reschedules itself up to MAX_RETRY_ATTEMPTS times.
    """
    from database import get_result
    from handlers.leaderboard import process_results_and_score

    bot = context.bot
    job_queue = context.application.job_queue
    race_id = race["id"]
    kind = "спринта" if is_sprint else "гонки"
    race_name = f"{race['flag']} {race['name']}"

    fetched = await _fetch_and_save_results(race, is_sprint)

    if not fetched:
        if attempt < MAX_RETRY_ATTEMPTS:
            next_attempt = attempt + 1
            logger.info(
                "Results not available yet for %s (%s), scheduling retry %d/%d in %d min",
                race_name, kind, next_attempt, MAX_RETRY_ATTEMPTS, RETRY_DELAY_MINUTES,
            )
            job_queue.run_once(
                lambda ctx, r=race, s=is_sprint, a=next_attempt: _auto_analyze_race(ctx, r, s, a),
                when=timedelta(minutes=RETRY_DELAY_MINUTES),
                name=f"retry_analyze_{race_id}_{'sprint' if is_sprint else 'race'}_{next_attempt}",
            )
        else:
            logger.error(
                "Failed to fetch results for %s (%s) after %d attempts",
                race_name, kind, MAX_RETRY_ATTEMPTS,
            )
        return

    result = await get_result(race_id, is_sprint)
    if not result:
        logger.info("No results in DB for %s (%s) after fetch — skipping score calc", race_name, kind)
        return

    try:
        await process_results_and_score(race_id, is_sprint, result["positions"], bot)
        logger.info("Auto-analyzed %s (%s)", race_name, kind)
    except Exception:
        logger.exception("Failed to auto-analyze %s (%s)", race_name, kind)


def register_race_jobs(app: Application):
    """Register reminder and auto-analysis jobs for all upcoming races."""
    init_fastf1_cache()

    jq = app.job_queue
    now = datetime.now(timezone.utc)

    for race in RACES_2026:
        for is_sprint in (False, True):
            key = "sprint_time" if is_sprint else "race_time"
            race_time = race.get(key)
            if not race_time or race_time <= now:
                continue

            race_id = race["id"]
            sprint_flag = is_sprint

            # 1-hour reminder
            remind_1h = race_time - timedelta(hours=1)
            if remind_1h > now:
                jq.run_once(
                    lambda ctx, r=race, s=sprint_flag: _send_reminder(ctx.bot, r, 60, s),
                    when=remind_1h,
                    name=f"remind_1h_{race_id}_{'sprint' if is_sprint else 'race'}",
                )

            # 5-minute lock notification
            remind_5m = race_time - timedelta(minutes=5)
            if remind_5m > now:
                jq.run_once(
                    lambda ctx, r=race, s=sprint_flag: _send_reminder(ctx.bot, r, 5, s),
                    when=remind_5m,
                    name=f"remind_5m_{race_id}_{'sprint' if is_sprint else 'race'}",
                )

            # Auto-analyze: starts AUTO_ANALYZE_DELAY_MINUTES after race start
            auto_analyze_time = race_time + timedelta(minutes=AUTO_ANALYZE_DELAY_MINUTES)
            if auto_analyze_time > now:
                jq.run_once(
                    lambda ctx, r=race, s=sprint_flag: _auto_analyze_race(ctx, r, s, 0),
                    when=auto_analyze_time,
                    name=f"auto_analyze_{race_id}_{'sprint' if is_sprint else 'race'}",
                )

    logger.info("Race reminder and auto-analysis jobs registered.")
