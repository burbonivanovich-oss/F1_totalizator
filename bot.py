import logging
import os
import sys
import asyncio

# Ensure project root is in Python path regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
import database as db
from handlers.start import start, menu_callback
from handlers.calendar_handler import show_calendar, show_drivers
from handlers.leaderboard import show_leaderboard
from handlers.predictions import build_predict_conversation, show_my_predictions, handle_webapp_data
from handlers.admin import result_command, test_results_command
from scheduler import register_race_jobs

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(app: Application):
    await db.init_db()
    register_race_jobs(app)
    logger.info("Bot started. DB initialised.")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")

    # Fix for Python 3.10+ (especially Python 3.14 on Render)
    # Ensure event loop exists before running the bot
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Prediction conversation (WebApp flow — must be registered first)
    app.add_handler(build_predict_conversation())

    # WebApp data handler — receives data submitted from the Mini App
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    # Simple commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("calendar", show_calendar))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("result", result_command))
    app.add_handler(CommandHandler("test_results", test_results_command))

    # Inline button router (main menu)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: start(u, c),
        pattern="^main_menu$",
    ))

    # Catch stale callbacks (race/type buttons from a previous bot session).
    # Without this, pressing them after a restart causes silent nothing.
    async def _stale_callback(update, context):
        await update.callback_query.answer(
            "⏱ Сессия устарела — нажми /start", show_alert=True
        )

    app.add_handler(CallbackQueryHandler(_stale_callback))

    logger.info("Starting polling...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,  # explicitly request ALL update types
    )


if __name__ == "__main__":
    main()
