from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from config import WEBAPP_URL


MAIN_MENU_TEXT = (
    "🏎 <b>F1 Тотализатор 2026</b>\n\n"
    "Выбери действие:"
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Календарь", callback_data="menu:calendar"),
         InlineKeyboardButton("🏁 Прогноз", callback_data="menu:predict")],
        [InlineKeyboardButton("📋 Мои прогнозы", callback_data="menu:my_predictions"),
         InlineKeyboardButton("📊 Статистика", callback_data="menu:stats")],
        [InlineKeyboardButton("🏆 Лидерборд", callback_data="menu:leaderboard"),
         InlineKeyboardButton("🏎 Гонщики", callback_data="menu:drivers")],
    ])


def webapp_reply_keyboard(
    race_id: str, is_sprint: bool, tg_id: int,
    existing_positions: list[str] | None = None,
) -> ReplyKeyboardMarkup:
    """Reply keyboard with a WebApp button for the given race."""
    sprint_param = "1" if is_sprint else "0"
    url = f"{WEBAPP_URL}?race_id={race_id}&is_sprint={sprint_param}&tg_id={tg_id}"
    if existing_positions:
        url += f"&positions={','.join(existing_positions)}"
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Открыть прогноз", web_app=WebAppInfo(url=url))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.upsert_user(user.id, user.username, user.full_name)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(
            MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route main menu button presses."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) < 2:
        await query.edit_message_text("Ошибка: неверный формат команды")
        return

    action = parts[1]

    if action == "calendar":
        from handlers.calendar_handler import show_calendar
        await show_calendar(update, context)

    elif action == "predict":
        from handlers.predictions import start_predict_flow
        await start_predict_flow(update, context)

    elif action == "my_predictions":
        from handlers.predictions import show_my_predictions
        await show_my_predictions(update, context)

    elif action == "leaderboard":
        from handlers.leaderboard import show_leaderboard
        await show_leaderboard(update, context)

    elif action == "stats":
        from handlers.stats import show_stats
        await show_stats(update, context)

    elif action == "drivers":
        from handlers.calendar_handler import show_drivers
        await show_drivers(update, context)
