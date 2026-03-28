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

from telegram.ext import Application

from handlers.calendar_handler import RACES_2026

logger = logging.getLogger(__name__)

# Delay before fetching and analyzing results (in minutes)
AUTO_ANALYZE_DELAY_MINUTES = 10

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
    from data.drivers import DRIVERS

    race_id = race["id"]
    race_name = race["name"]
    session_type = "Sprint" if is_sprint else "Race"

    try:
        # Build driver number to code mapping
        number_to_code = {d["number"]: d["id"] for d in DRIVERS}

        # Convert race ID to FastF1 GP name
        gp_name = RACE_ID_TO_FASTF1_NAME.get(race_id)
        if not gp_name:
            logger.warning(f"Unknown race ID {race_id}, cannot fetch results")
            return False

        # Load session data from FastF1
        # Run in thread pool since FastF1 is blocking
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: fastf1.get_session(F1_SEASON, gp_name, "S" if is_sprint else "R")
        )

        if not session:
            logger.warning(f"Could not find session for {race_name} {session_type}")
            return False

        # Load results (this downloads data from F1 API)
        await loop.run_in_executor(None, lambda: session.load())

        # Get results DataFrame
        results_df = session.results

        if results_df is None or len(results_df) == 0:
            logger.warning(f"No results found for {race_name} {session_type}")
            return False

        # Filter only drivers who finished (Status = "Finished") and sort by Position/ClassifiedPosition
        # DNF drivers won't be scored
        finished_df = results_df[results_df['Status'] == '+0:00:00.000'].copy() if 'Status' in results_df.columns else results_df.copy()

        # Sort by Position if available, otherwise by ClassifiedPosition
        if 'Position' in finished_df.columns:
            sorted_results = finished_df.sort_values('Position', na_position='last')
        elif 'ClassifiedPosition' in finished_df.columns:
            sorted_results = finished_df.sort_values('ClassifiedPosition', na_position='last')
        else:
            sorted_results = finished_df

        # Extract driver numbers in finishing order
        positions = []
        for idx, row in sorted_results.iterrows():
            driver_number = row.get("DriverNumber") or row.get("Driver")

            # Skip drivers who didn't finish or have no valid number
            if driver_number is None or driver_number == "":
                continue

            # Convert to int - handles numpy/pandas types too
            try:
                driver_number = int(driver_number)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert driver number {driver_number} in {race_name}")
                continue

            # Convert driver number to code
            driver_code = number_to_code.get(driver_number)
            if not driver_code:
                logger.warning(f"Unknown driver number {driver_number} in {race_name}")
                continue

            positions.append(driver_code)

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
