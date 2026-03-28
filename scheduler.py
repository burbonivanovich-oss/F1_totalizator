"""
Scheduled jobs:
  - 1 hour before race: reminder "последний час для прогнозов"
  - 5 minutes before race: notification "приём прогнозов закрыт"
  - ~10 minutes after race: auto-fetch results from FastF1, save to DB, calculate scores
"""
import os
import sys
# Ensure project root is always in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, timezone
import logging
import pandas as pd

from telegram.ext import Application

from handlers.calendar_handler import RACES_2026

logger = logging.getLogger(__name__)

# Delay before fetching and analyzing results (in minutes)
AUTO_ANALYZE_DELAY_MINUTES = 10

# FastF1 season year
F1_SEASON = 2026


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
        except Exception as e:
            # Log full exception details instead of just warning
            logger.exception("Failed to notify user %s", user["telegram_id"])


async def _fetch_and_save_results(race: dict, is_sprint: bool) -> bool:
    """Fetch race results from FastF1 and save to database. Returns True if successful."""
    import asyncio
    import fastf1

    from database import save_result
    from handlers.calendar_handler import DRIVER_BY_ID

    race_id = race["id"]
    race_name = race["name"]
    session_type = "Sprint" if is_sprint else "Race"

    try:
        # Build mapping: driver_number -> driver_code
        number_to_code = {d["number"]: d["id"] for d in DRIVER_BY_ID.values()}

        # Load session data from FastF1
        # Run in thread pool since FastF1 is blocking
        loop = asyncio.get_event_loop()

        # Try to fetch session - use latest available year with data
        # FastF1 may not have 2026 data yet, fall back to 2024
        session = None
        for year in [F1_SEASON, 2024, 2023]:
            try:
                session = await loop.run_in_executor(
                    None,
                    lambda y=year: fastf1.get_session(y, race_id, "S" if is_sprint else "R")
                )
                if session:
                    logger.info(f"Found session for {race_id} in year {year}")
                    break
            except Exception as e:
                logger.debug(f"Could not find session for {race_id} in year {year}: {e}")
                continue

        if not session:
            logger.warning(f"Could not find session for {race_name} {session_type} in any year")
            return False

        # Load results (this downloads data from F1 API)
        await loop.run_in_executor(None, lambda: session.load())

        # Get results DataFrame
        results_df = session.results
        if results_df is None or len(results_df) == 0:
            logger.warning(f"No results found for {race_name} {session_type}")
            return False

        # Extract driver abbreviations/numbers in finishing order (by ClassifiedPosition)
        positions = []

        # Sort by ClassifiedPosition to get finishing order
        sorted_results = results_df.sort_values('ClassifiedPosition', na_position='last')

        for _, row in sorted_results.iterrows():
            # Try to get driver abbreviation or number
            abbrev = row.get('Abbreviation')
            driver_number = row.get('DriverNumber')

            if pd.isna(abbrev) and pd.isna(driver_number):
                continue

            # Try abbreviation first (3-letter code like VER, HAM, etc.)
            driver_code = None
            if not pd.isna(abbrev):
                abbrev_str = str(abbrev).upper().strip()
                # Search for matching driver
                for code, driver in DRIVER_BY_ID.items():
                    if driver.get("name", "").upper() == abbrev_str or code == abbrev_str:
                        driver_code = code
                        break

            # Fall back to driver number
            if not driver_code and not pd.isna(driver_number):
                driver_number = int(driver_number) if isinstance(driver_number, (int, float)) else driver_number
                driver_code = number_to_code.get(driver_number)

            if driver_code:
                positions.append(driver_code)
            else:
                logger.debug(f"Could not map driver {abbrev}/{driver_number} to code in {race_name}")

        if not positions:
            logger.warning(f"No valid driver codes extracted for {race_name} {session_type}")
            return False

        # Save to database
        await save_result(race_id, is_sprint, positions)
        logger.info(f"Fetched and saved {session_type} results for {race_name}: {positions}")
        return True

    except Exception as e:
        logger.exception(f"Failed to fetch {session_type} results for {race_name} from FastF1")
        return False


async def _auto_analyze_race(bot, race: dict, is_sprint: bool):
    """Auto-analyze race results: fetch from FastF1, save, and calculate scores."""
    from database import get_result  # lazy import
    from handlers.leaderboard import process_results_and_score

    race_id = race["id"]
    kind = "спринта" if is_sprint else "гонки"
    race_name = f"{race['flag']} {race['name']}"

    # Try to fetch results from FastF1
    fetched = await _fetch_and_save_results(race, is_sprint)

    # Check if results exist in database (either fetched or manually entered)
    result = await get_result(race_id, is_sprint)
    if not result:
        logger.info(f"No results for {race_name} ({kind}), skipping auto-analysis")
        return

    try:
        summary = await process_results_and_score(
            race_id, is_sprint, result["positions"], bot
        )
        logger.info(f"Auto-analyzed {race_name} ({kind})")
    except Exception as e:
        logger.exception(f"Failed to auto-analyze {race_name} ({kind})")


def register_race_jobs(app: Application):
    """Register reminder and auto-analysis jobs for all upcoming races."""
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

            # Auto-analyze results after race ends
            auto_analyze_time = race_time + timedelta(minutes=AUTO_ANALYZE_DELAY_MINUTES)
            if auto_analyze_time > now:
                jq.run_once(
                    lambda ctx, r=race, s=sprint_flag: _auto_analyze_race(ctx.bot, r, s),
                    when=auto_analyze_time,
                    name=f"auto_analyze_{race_id}_{'sprint' if is_sprint else 'race'}",
                )

    logger.info("Race reminder and auto-analysis jobs registered.")
