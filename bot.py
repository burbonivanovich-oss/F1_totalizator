import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
)

from config import BOT_TOKEN
import database as db
from handlers.start import start, menu_callback
from handlers.calendar_handler import show_calendar, show_drivers
from handlers.leaderboard import show_leaderboard
from handlers.predictions import build_predict_conversation, show_my_predictions
from handlers.admin import result_command
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

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Prediction multi-step conversation (must be registered first)
    app.add_handler(build_predict_conversation())

    # Simple commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("calendar", show_calendar))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("result", result_command))

    # Inline button router (main menu)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: start(u, c),   # re-show main menu
        pattern="^main_menu$",
    ))

    # Individual feature callbacks (outside conversation)
    app.add_handler(CallbackQueryHandler(show_leaderboard, pattern="^menu:leaderboard$"))
    app.add_handler(CallbackQueryHandler(show_my_predictions, pattern="^menu:my_predictions$"))
    app.add_handler(CallbackQueryHandler(show_calendar, pattern="^menu:calendar$"))
    app.add_handler(CallbackQueryHandler(show_drivers, pattern="^menu:drivers$"))

    logger.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
