"""
Prediction flow via Telegram Mini App (WebApp).

Flow:
  1. User presses "🏁 Прогноз" → show list of open races
  2. User picks a race (and optionally sprint/race type)
  3. Bot sends a WebApp button → user opens drag-and-drop interface
  4. User submits → bot receives web_app_data → saves to DB
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
)

import database as db
from config import PREDICTION_LOCK_MINUTES, WEBAPP_URL
from data.calendar_2026 import RACES_2026, RACE_BY_ID
from data.drivers import DRIVER_BY_ID, get_driver_short

# Conversation states
(
    STATE_PICK_RACE,
    STATE_PICK_TYPE,
) = range(2)

BACK = "predict:back"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_locked(race: dict, is_sprint: bool) -> bool:
    key = "sprint_time" if is_sprint else "race_time"
    race_time = race.get(key)
    if not race_time:
        return True
    deadline = race_time - timedelta(minutes=PREDICTION_LOCK_MINUTES)
    return datetime.now(timezone.utc) >= deadline


def _open_races() -> list[dict]:
    return [r for r in RACES_2026 if not _is_locked(r, is_sprint=False)]


# ── Entry points ──────────────────────────────────────────────────────────────

async def start_predict_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    open_races = _open_races()

    if not open_races:
        text = "❌ Приём прогнозов на все оставшиеся гонки закрыт."
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")
        ]])
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=kb)
        else:
            await update.message.reply_text(text, reply_markup=kb)
        return ConversationHandler.END

    buttons = []
    for race in open_races:
        label = f"{race['flag']} {race['name']}"
        if race["sprint_time"] and not _is_locked(race, is_sprint=True):
            label += " 🟣"
        buttons.append([InlineKeyboardButton(label, callback_data=f"race:{race['id']}")])
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data=BACK)])

    text = "🏁 <b>Выбери гонку для прогноза:</b>"
    kb = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)

    return STATE_PICK_RACE


async def pick_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == BACK:
        await _back_to_menu(query)
        return ConversationHandler.END

    parts = query.data.split(":")
    if len(parts) < 2:
        await query.edit_message_text("Ошибка: неверный формат гонки")
        return ConversationHandler.END

    race_id = parts[1]
    race = RACE_BY_ID.get(race_id)
    if not race:
        await query.edit_message_text("Гонка не найдена.")
        return ConversationHandler.END

    context.user_data["pred_race_id"] = race_id

    sprint_open = race["sprint_time"] is not None and not _is_locked(race, is_sprint=True)
    main_open   = not _is_locked(race, is_sprint=False)

    if sprint_open and main_open:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟣 Спринт", callback_data="type:sprint"),
             InlineKeyboardButton("🏁 Гонка",  callback_data="type:race")],
            [InlineKeyboardButton("❌ Отмена", callback_data=BACK)],
        ])
        await query.edit_message_text(
            f"<b>{race['flag']} {race['name']}</b>\n\nЧто прогнозируем?",
            parse_mode="HTML", reply_markup=kb,
        )
        return STATE_PICK_TYPE

    is_sprint = sprint_open and not main_open
    return await _send_webapp_button(query, context, race_id, is_sprint)


async def pick_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == BACK:
        await _back_to_menu(query)
        return ConversationHandler.END

    is_sprint = query.data == "type:sprint"
    race_id   = context.user_data.get("pred_race_id")
    if not race_id:
        await query.edit_message_text("Ошибка: сессия истекла. Начни заново /start")
        return ConversationHandler.END
    return await _send_webapp_button(query, context, race_id, is_sprint)


async def _send_webapp_button(query, context: ContextTypes.DEFAULT_TYPE, race_id: str, is_sprint: bool):
    """Send a message with the WebApp launch button."""
    from handlers.start import webapp_reply_keyboard

    race = RACE_BY_ID.get(race_id)
    if not race:
        await query.message.reply_text(f"❌ Гонка не найдена: {race_id}")
        return ConversationHandler.END

    kind  = "спринт" if is_sprint else "гонку"
    top_n = 10 if is_sprint else 16
    tg_id = query.from_user.id

    if not WEBAPP_URL:
        await query.message.reply_text(
            f"<b>{race['flag']} {race['name']}</b> — {kind}\n\n"
            "⚠️ WebApp URL не настроен. Укажи <code>WEBAPP_URL</code> в .env файле.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    # Load existing prediction to pre-fill the WebApp
    existing_positions = []
    user = await db.get_user_by_telegram_id(tg_id)
    if user:
        pred = await db.get_prediction(user["id"], race_id, is_sprint)
        if pred:
            existing_positions = pred["positions"]

    await query.message.reply_text(
        f"<b>{race['flag']} {race['name']}</b> — {kind}\n\n"
        f"Расставь топ-{top_n} гонщиков и подтверди прогноз.",
        parse_mode="HTML",
        reply_markup=webapp_reply_keyboard(race_id, is_sprint, tg_id, existing_positions),
    )
    return ConversationHandler.END


# ── web_app_data handler ──────────────────────────────────────────────────────

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data submitted from the Telegram Mini App."""
    raw = update.message.web_app_data.data
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, AttributeError):
        await update.message.reply_text("❌ Неверный формат данных от Mini App.")
        return

    race_id   = str(data.get("race_id", "")).upper()
    is_sprint = bool(data.get("is_sprint", False))
    positions = data.get("positions", [])
    top_n     = 10 if is_sprint else 16

    # Validate
    race = RACE_BY_ID.get(race_id)
    if not race:
        await update.message.reply_text(f"❌ Неизвестная гонка: {race_id}")
        return

    if _is_locked(race, is_sprint):
        await update.message.reply_text("❌ Приём прогнозов на эту гонку уже закрыт.")
        return

    if not isinstance(positions, list) or len(positions) != top_n:
        await update.message.reply_text(
            f"❌ Нужно ровно {top_n} гонщиков, получено {len(positions)}."
        )
        return

    positions = [str(p).upper() for p in positions]
    if len(set(positions)) != top_n:
        await update.message.reply_text("❌ Дублирующиеся гонщики в прогнозе.")
        return

    for driver_id in positions:
        if driver_id not in DRIVER_BY_ID:
            await update.message.reply_text(f"❌ Неизвестный гонщик: {driver_id}")
            return

    # Save
    tg_user    = update.effective_user
    user_db_id = await db.upsert_user(tg_user.id, tg_user.username, tg_user.full_name)
    await db.save_prediction(user_db_id, race_id, is_sprint, positions)

    kind = "спринт" if is_sprint else "гонку"
    podium = "\n".join(
        f"P{i+1}: {get_driver_short(d)}" for i, d in enumerate(positions[:3])
    )
    rest_count = len(positions) - 3

    await update.message.reply_text(
        f"✅ <b>Прогноз сохранён!</b>\n\n"
        f"{race['flag']} <b>{race['name']}</b> — {kind}\n\n"
        f"{podium}\n"
        f"<i>... и ещё {rest_count} позиций</i>\n\n"
        f"<i>Изменить прогноз можно до 5 минут до старта.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")
        ]]),
    )


# ── Cancel ────────────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        await _back_to_menu(update.callback_query)
    else:
        await update.message.reply_text("Отменено.")
    return ConversationHandler.END


async def _back_to_menu(query):
    from handlers.start import MAIN_MENU_TEXT, main_menu_keyboard
    await query.edit_message_text(
        MAIN_MENU_TEXT, parse_mode="HTML", reply_markup=main_menu_keyboard()
    )


# ── My predictions ────────────────────────────────────────────────────────────

async def show_my_predictions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tg_user = update.effective_user

    user = await db.get_user_by_telegram_id(tg_user.id)
    if not user:
        await query.edit_message_text("Сначала запусти /start")
        return

    predictions = await db.get_user_predictions(user["id"])
    # Convert is_sprint to int for consistent dict keys (database stores as 0/1, not bool)
    scores = {(s["race_id"], int(s["is_sprint"])): s for s in await db.get_user_scores(user["id"])}

    if not predictions:
        text = "📋 У тебя пока нет прогнозов."
    else:
        lines = ["📋 <b>Мои прогнозы</b>\n"]
        for pred in predictions:
            race = RACE_BY_ID.get(pred["race_id"], {})
            flag = race.get("flag", "")
            name = race.get("name", pred["race_id"])
            kind = "🟣 Спринт" if pred["is_sprint"] else "🏁 Гонка"
            # Use same type (int) for lookup as used in dict creation
            score_rec = scores.get((pred["race_id"], int(pred["is_sprint"])))
            pts = f"+{score_rec['points']} очк." if score_rec else "ожидание результата"

            positions = pred.get("positions", [])
            podium_str = ", ".join(get_driver_short(d) for d in positions[:3])

            lines.append(
                f"{flag} <b>{name}</b> {kind}\n"
                f"  {podium_str} …\n"
                f"  📊 {pts}\n"
            )
        text = "\n".join(lines)

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")
    ]])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


# ── ConversationHandler factory ───────────────────────────────────────────────

def build_predict_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_predict_flow, pattern="^menu:predict$"),
            CommandHandler("predict", start_predict_flow),
        ],
        states={
            STATE_PICK_RACE: [
                CallbackQueryHandler(pick_race, pattern=r"^race:"),
                CallbackQueryHandler(cancel, pattern=f"^{BACK}$"),
            ],
            STATE_PICK_TYPE: [
                CallbackQueryHandler(pick_type, pattern=r"^type:"),
                CallbackQueryHandler(cancel, pattern=f"^{BACK}$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern=f"^{BACK}$"),
        ],
        per_message=False,
    )
