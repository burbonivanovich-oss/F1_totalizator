import asyncio
import logging

import uvicorn
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, WEBAPP_URL, WEBAPP_PORT, WEBAPP_HOST
import database as db
from handlers.start import start, menu_callback
from handlers.calendar_handler import show_calendar, show_drivers
from handlers.leaderboard import show_leaderboard
from handlers.predictions import build_predict_conversation, show_my_predictions, handle_webapp_data
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

    # Prediction conversation (WebApp flow — must be registered first)
    app.add_handler(build_predict_conversation())

    # WebApp data handler — receives data submitted from the Mini App
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    # Simple commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("calendar", show_calendar))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("result", result_command))

    # Inline button router (main menu)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: start(u, c),
        pattern="^main_menu$",
    ))

    # Individual feature callbacks (outside conversation)
    app.add_handler(CallbackQueryHandler(show_leaderboard,    pattern="^menu:leaderboard$"))
    app.add_handler(CallbackQueryHandler(show_my_predictions, pattern="^menu:my_predictions$"))
    app.add_handler(CallbackQueryHandler(show_calendar,       pattern="^menu:calendar$"))
    app.add_handler(CallbackQueryHandler(show_drivers,        pattern="^menu:drivers$"))

    if WEBAPP_URL:
        logger.info("Starting webapp server on %s:%s", WEBAPP_HOST, WEBAPP_PORT)
        _run_with_webapp(app)
    else:
        logger.info("WEBAPP_URL not set — starting bot only (no web server).")
        app.run_polling(drop_pending_updates=True)


def _run_with_webapp(app: Application):
    """Run bot polling and FastAPI web server concurrently in the same event loop."""
    from webapp.server import app as web_app

    async def _main():
        # Start web server
        config = uvicorn.Config(web_app, host=WEBAPP_HOST, port=WEBAPP_PORT, log_level="info")
        server = uvicorn.Server(config)
        web_task = asyncio.create_task(server.serve())

        # Start bot (run_polling manages its own lifecycle)
        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot polling started.")
            try:
                await web_task
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            finally:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()

    asyncio.run(_main())


if __name__ == "__main__":
    main()
