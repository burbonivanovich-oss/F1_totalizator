from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from handlers.calendar_handler import RACE_BY_ID


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
        await update.callback_query.answer()
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
    from data.scoring import calculate_score

    await db.save_result(race_id, is_sprint, positions)
    predictions = await db.get_all_predictions_for_race(race_id, is_sprint)

    if not predictions:
        return "Прогнозов на эту гонку не было."

    race = RACE_BY_ID.get(race_id, {})
    race_label = f"{race.get('flag', '')} {race.get('name', race_id)}".strip()
    kind = "спринта" if is_sprint else "гонки"

    summary_lines = []
    for pred in predictions:
        result = calculate_score(
            {"positions": pred["positions"]},
            {"positions": positions},
            is_sprint=is_sprint,
        )
        existing_score = await db.get_score(pred["user_id"], race_id, is_sprint)
        await db.save_score(
            pred["user_id"], race_id, is_sprint,
            result["total"], result["breakdown"],
        )
        breakdown_text = "\n".join(result["breakdown"])
        action = "пересчитаны" if existing_score else "подсчитаны"
        header = (
            f"📊 <b>Результаты {kind} {race_label}</b> {action}\n\n"
            f"Твои очки: <b>{result['total']:+d}</b>"
        )
        nav_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 Мои прогнозы", callback_data="menu:my_predictions"),
                InlineKeyboardButton("🏆 Лидерборд",    callback_data="menu:leaderboard"),
            ]
        ])
        try:
            await bot.send_message(
                pred["telegram_id"],
                f"{header}\n\n{breakdown_text}",
                parse_mode="HTML",
                reply_markup=nav_kb,
            )
        except Exception as e:
            # Log notification failures instead of silently ignoring
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Failed to send score notification to user {pred['telegram_id']}")

        summary_lines.append(f"{pred['full_name']}: {result['total']} очк.")

    return "\n".join(summary_lines)
