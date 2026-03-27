"""
Scheduled jobs:
  - 1 hour before race: reminder "последний час для прогнозов"
  - 5 minutes before race: notification "приём прогнозов закрыт"
  - ~10 minutes after race: auto-analyze results if they exist
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

# Delay before auto-analyzing results (in minutes)
AUTO_ANALYZE_DELAY_MINUTES = 10


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


async def _auto_analyze_race(bot, race: dict, is_sprint: bool):
    """Auto-analyze race results if they exist in database."""
    from database import get_result  # lazy import
    from handlers.leaderboard import process_results_and_score

    race_id = race["id"]
    kind = "спринта" if is_sprint else "гонки"
    race_name = f"{race['flag']} {race['name']}"

    # Check if results exist in database
    result = await get_result(race_id, is_sprint)
    if not result:
        logger.info(f"No results for {race_name} ({kind}) in database yet, skipping auto-analysis")
        return

    try:
        summary = await process_results_and_score(
            race_id, is_sprint, result["positions"], bot
        )
        logger.info(f"Auto-analyzed {race_name} ({kind}): {summary}")
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
