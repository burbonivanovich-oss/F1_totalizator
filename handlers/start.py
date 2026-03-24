from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db


MAIN_MENU_TEXT = (
    "🏎 <b>F1 Тотализатор 2026</b>\n\n"
    "Выбери действие:"
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Календарь", callback_data="menu:calendar"),
         InlineKeyboardButton("🏁 Прогноз", callback_data="menu:predict")],
        [InlineKeyboardButton("📋 Мои прогнозы", callback_data="menu:my_predictions"),
         InlineKeyboardButton("🏆 Лидерборд", callback_data="menu:leaderboard")],
        [InlineKeyboardButton("🏎 Гонщики", callback_data="menu:drivers")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.upsert_user(user.id, user.username, user.full_name)

    await update.message.reply_text(
        MAIN_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route main menu button presses."""
    query = update.callback_query
    await query.answer()

    action = query.data.split(":")[1]

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

    elif action == "drivers":
        from handlers.calendar_handler import show_drivers
        await show_drivers(update, context)
