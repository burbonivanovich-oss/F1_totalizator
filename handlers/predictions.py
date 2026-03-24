"""
Prediction flow (ConversationHandler):
  1. Show list of races where predictions are still open → user picks a race
  2. Ask if this is for the sprint or the main race (if sprint weekend)
  3. Pick P1 driver
  4. Pick P2 driver
  5. Pick P3 driver → save, confirm
"""
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
from config import PREDICTION_LOCK_MINUTES
from data.calendar_2026 import RACES_2026, RACE_BY_ID
from data.drivers import DRIVERS, DRIVER_BY_ID, get_driver_short

# Conversation states
(
    STATE_PICK_RACE,
    STATE_PICK_TYPE,   # sprint or main race
    STATE_PICK_P1,
    STATE_PICK_P2,
    STATE_PICK_P3,
) = range(5)

BACK = "predict:back"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_locked(race: dict, is_sprint: bool) -> bool:
    """Returns True if the prediction window has closed."""
    key = "sprint_time" if is_sprint else "race_time"
    race_time = race.get(key)
    if not race_time:
        return True
    deadline = race_time - timedelta(minutes=PREDICTION_LOCK_MINUTES)
    return datetime.now(timezone.utc) >= deadline


def _open_races() -> list[dict]:
    """Races whose main-race prediction is still open."""
    return [r for r in RACES_2026 if not _is_locked(r, is_sprint=False)]


def _driver_buttons(exclude: list[str]) -> list[list[InlineKeyboardButton]]:
    """2-column grid of driver buttons, skipping already-chosen drivers."""
    buttons = []
    row = []
    for d in DRIVERS:
        if d["id"] in exclude:
            continue
        row.append(InlineKeyboardButton(
            f"#{d['number']} {d['name']}",
            callback_data=f"drv:{d['id']}",
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data=BACK)])
    return buttons


# ── Entry points ──────────────────────────────────────────────────────────────

async def start_predict_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of open races."""
    open_races = _open_races()

    if not open_races:
        text = "❌ Приём прогнозов на все оставшиеся гонки закрыт."
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ])
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

    race_id = query.data.split(":")[1]
    race = RACE_BY_ID.get(race_id)
    if not race:
        await query.edit_message_text("Гонка не найдена.")
        return ConversationHandler.END

    context.user_data["pred_race_id"] = race_id

    # If sprint weekend and sprint not yet locked → ask which to predict
    sprint_open = (
        race["sprint_time"] is not None
        and not _is_locked(race, is_sprint=True)
    )
    main_open = not _is_locked(race, is_sprint=False)

    if sprint_open and main_open:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟣 Спринт", callback_data="type:sprint"),
             InlineKeyboardButton("🏁 Гонка", callback_data="type:race")],
            [InlineKeyboardButton("❌ Отмена", callback_data=BACK)],
        ])
        await query.edit_message_text(
            f"<b>{race['flag']} {race['name']}</b>\n\nЧто прогнозируем?",
            parse_mode="HTML", reply_markup=kb,
        )
        return STATE_PICK_TYPE

    # Only one option open — set automatically
    context.user_data["pred_is_sprint"] = sprint_open and not main_open
    return await _ask_p1(query, context)


async def pick_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == BACK:
        await _back_to_menu(query)
        return ConversationHandler.END

    context.user_data["pred_is_sprint"] = query.data == "type:sprint"
    return await _ask_p1(query, context)


async def _ask_p1(query, context: ContextTypes.DEFAULT_TYPE):
    race_id = context.user_data["pred_race_id"]
    is_sprint = context.user_data["pred_is_sprint"]
    race = RACE_BY_ID[race_id]

    # Check for existing prediction
    user = await db.get_user_by_telegram_id(query.from_user.id)
    existing = await db.get_prediction(user["id"], race_id, is_sprint) if user else None

    kind = "спринт" if is_sprint else "гонку"
    header = (
        f"<b>{race['flag']} {race['name']}</b> — {kind}\n\n"
        f"Выбери гонщика на <b>P1</b> 🥇"
    )
    if existing:
        header = (
            f"✏️ Редактируешь прогноз\n{header}\n\n"
            f"Текущий: {existing['p1']} / {existing['p2']} / {existing['p3']}"
        )

    context.user_data["pred_chosen"] = []
    await query.edit_message_text(
        header, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(_driver_buttons([])),
    )
    return STATE_PICK_P1


async def pick_p1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == BACK:
        await _back_to_menu(query)
        return ConversationHandler.END

    driver_id = query.data.split(":")[1]
    context.user_data["pred_chosen"] = [driver_id]

    race = RACE_BY_ID[context.user_data["pred_race_id"]]
    is_sprint = context.user_data["pred_is_sprint"]
    kind = "спринт" if is_sprint else "гонку"

    await query.edit_message_text(
        f"<b>{race['flag']} {race['name']}</b> — {kind}\n\n"
        f"P1 🥇: <b>{get_driver_short(driver_id)}</b>\n\n"
        f"Выбери гонщика на <b>P2</b> 🥈",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(_driver_buttons([driver_id])),
    )
    return STATE_PICK_P2


async def pick_p2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == BACK:
        await _back_to_menu(query)
        return ConversationHandler.END

    driver_id = query.data.split(":")[1]
    chosen = context.user_data["pred_chosen"]
    chosen.append(driver_id)
    context.user_data["pred_chosen"] = chosen

    race = RACE_BY_ID[context.user_data["pred_race_id"]]
    is_sprint = context.user_data["pred_is_sprint"]
    kind = "спринт" if is_sprint else "гонку"

    await query.edit_message_text(
        f"<b>{race['flag']} {race['name']}</b> — {kind}\n\n"
        f"P1 🥇: <b>{get_driver_short(chosen[0])}</b>\n"
        f"P2 🥈: <b>{get_driver_short(driver_id)}</b>\n\n"
        f"Выбери гонщика на <b>P3</b> 🥉",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(_driver_buttons(chosen)),
    )
    return STATE_PICK_P3


async def pick_p3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == BACK:
        await _back_to_menu(query)
        return ConversationHandler.END

    driver_id = query.data.split(":")[1]
    chosen = context.user_data["pred_chosen"]
    chosen.append(driver_id)

    race_id = context.user_data["pred_race_id"]
    is_sprint = context.user_data["pred_is_sprint"]
    race = RACE_BY_ID[race_id]

    # Save to DB
    tg_user = query.from_user
    user_db_id = await db.upsert_user(tg_user.id, tg_user.username, tg_user.full_name)
    await db.save_prediction(user_db_id, race_id, is_sprint, chosen[0], chosen[1], chosen[2])

    kind = "спринт" if is_sprint else "гонку"
    text = (
        f"✅ <b>Прогноз сохранён!</b>\n\n"
        f"{race['flag']} <b>{race['name']}</b> — {kind}\n\n"
        f"🥇 P1: {get_driver_short(chosen[0])}\n"
        f"🥈 P2: {get_driver_short(chosen[1])}\n"
        f"🥉 P3: {get_driver_short(chosen[2])}\n\n"
        f"<i>Изменить прогноз можно до 5 минут до старта.</i>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏁 Ещё прогноз", callback_data="menu:predict"),
         InlineKeyboardButton("◀️ Меню", callback_data="main_menu")],
    ])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    context.user_data.clear()
    return ConversationHandler.END


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
    scores = {(s["race_id"], s["is_sprint"]): s for s in await db.get_user_scores(user["id"])}

    if not predictions:
        text = "📋 У тебя пока нет прогнозов."
    else:
        lines = ["📋 <b>Мои прогнозы</b>\n"]
        for pred in predictions:
            race = RACE_BY_ID.get(pred["race_id"], {})
            flag = race.get("flag", "")
            name = race.get("name", pred["race_id"])
            kind = "🟣 Спринт" if pred["is_sprint"] else "🏁 Гонка"
            score_rec = scores.get((pred["race_id"], pred["is_sprint"]))
            pts = f"+{score_rec['points']} очк." if score_rec else "ожидание результата"

            lines.append(
                f"{flag} <b>{name}</b> {kind}\n"
                f"  🥇 {get_driver_short(pred['p1'])}\n"
                f"  🥈 {get_driver_short(pred['p2'])}\n"
                f"  🥉 {get_driver_short(pred['p3'])}\n"
                f"  📊 {pts}\n"
            )
        text = "\n".join(lines)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
    ])
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
            STATE_PICK_P1: [
                CallbackQueryHandler(pick_p1, pattern=r"^drv:"),
                CallbackQueryHandler(cancel, pattern=f"^{BACK}$"),
            ],
            STATE_PICK_P2: [
                CallbackQueryHandler(pick_p2, pattern=r"^drv:"),
                CallbackQueryHandler(cancel, pattern=f"^{BACK}$"),
            ],
            STATE_PICK_P3: [
                CallbackQueryHandler(pick_p3, pattern=r"^drv:"),
                CallbackQueryHandler(cancel, pattern=f"^{BACK}$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern=f"^{BACK}$"),
        ],
        per_message=False,
    )
