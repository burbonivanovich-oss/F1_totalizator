from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db


MEDALS = ["🥇", "🥈", "🥉"]


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    board = await db.get_leaderboard()

    if not board:
        text = "🏆 Лидерборд пуст — сделай первый прогноз!"
    else:
        lines = ["🏆 <b>Лидерборд</b>\n"]
        for i, row in enumerate(board):
            pos = MEDALS[i] if i < 3 else f"{i + 1}."
            lines.append(
                f"{pos} <b>{row['full_name']}</b> — "
                f"<b>{row['total_points']}</b> очк. "
                f"({row['races_count']} гон.)"
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


async def process_results_and_score(
    race_id: str,
    is_sprint: bool,
    positions: list[str],
    bot,
) -> str:
    """
    Admin helper: save race result, compute scores for all participants,
    and notify them. Returns a summary string.
    """
    import logging
    from data.scoring import calculate_score

    logger = logging.getLogger(__name__)

    # ── Validate results ─────────────────────────────────────────────────────
    expected_count = 10 if is_sprint else 16
    min_count = 1  # At least 1 driver must finish

    if not positions or not isinstance(positions, list):
        error_msg = f"Invalid race results for {race_id}: empty or non-list positions"
        logger.error(error_msg)
        return f"❌ {error_msg}"

    if len(positions) < min_count:
        error_msg = (
            f"Invalid race results for {race_id}: got {len(positions)} results, "
            f"need at least {min_count}"
        )
        logger.error(error_msg)
        return f"❌ {error_msg}"

    if len(positions) < expected_count:
        logger.info(
            f"Partial results for {race_id}: {len(positions)} finished "
            f"(expected {expected_count}). DNF drivers will get -1 penalty."
        )

    if len(set(positions)) != len(positions):
        duplicates = [d for d in positions if positions.count(d) > 1]
        error_msg = (
            f"Duplicate drivers in race results for {race_id}: {', '.join(set(duplicates))}"
        )
        logger.error(error_msg)
        return f"❌ {error_msg}"

    if None in positions or "" in positions:
        error_msg = f"Empty values in race results for {race_id}"
        logger.error(error_msg)
        return f"❌ {error_msg}"

    # ── Save and process ────────────────────────────────────────────────────
    await db.save_result(race_id, is_sprint, positions)
    predictions = await db.get_all_predictions_for_race(race_id, is_sprint)

    if not predictions:
        logger.info(f"No predictions for race {race_id}")
        return "Прогнозов на эту гонку не было."

    summary_lines = []
    for pred in predictions:
        # Validate prediction before scoring
        if not pred.get("positions") or not isinstance(pred["positions"], list):
            logger.warning(
                f"Skipping invalid prediction for user {pred['telegram_id']} "
                f"in race {race_id}"
            )
            continue

        result = calculate_score(
            {"positions": pred["positions"]},
            {"positions": positions},
            is_sprint=is_sprint,
        )

        # Check if scoring returned error
        if result["total"] == 0 and result["breakdown"] and result["breakdown"][0].startswith("❌"):
            logger.error(
                f"Scoring error for user {pred['telegram_id']} in race {race_id}: "
                f"{result['breakdown'][0]}"
            )
            continue
        existing_score = await db.get_score(pred["user_id"], race_id, is_sprint)
        await db.save_score(
            pred["user_id"], race_id, is_sprint,
            result["total"], result["breakdown"],
        )
        breakdown_text = "\n".join(result["breakdown"])
        header = "🔄 <b>Результаты пересчитаны</b>" if existing_score else f"📊 <b>Результаты {'спринта' if is_sprint else 'гонки'}</b>"
        try:
            await bot.send_message(
                pred["telegram_id"],
                f"{header}\n\n"
                f"Твои очки: <b>{result['total']}</b>\n\n{breakdown_text}",
                parse_mode="HTML",
            )
        except Exception as e:
            # Log notification failures instead of silently ignoring
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Failed to send score notification to user {pred['telegram_id']}")

        summary_lines.append(f"{pred['full_name']}: {result['total']} очк.")

    return "\n".join(summary_lines)
