from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_user = update.effective_user

    user = await db.get_user_by_telegram_id(tg_user.id)
    if not user:
        await query.edit_message_text(
            "Сначала запусти /start",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")
            ]]),
        )
        return

    stats = await db.get_user_full_stats(user["id"])

    races   = stats["races_scored"]
    total   = stats["total_points"]
    best    = stats["best_race"]
    avg     = stats["avg_points"]
    rank    = stats["rank"]
    made    = stats["predictions_made"]
    exact   = stats["exact_hits"]
    top     = stats["top_hits"]
    slots   = stats["total_slots"]
    p1_ok   = stats["p1_correct"]
    p1_tot  = stats["p1_total"]

    exact_pct = f"{exact / slots * 100:.0f}%" if slots > 0 else "—"
    p1_str    = f"{p1_ok}/{p1_tot}" if p1_tot > 0 else "—"

    if races == 0:
        text = (
            "📊 <b>Моя статистика</b>\n\n"
            "Пока нет оценённых гонок.\n"
            "Сделай прогноз и дождись итогов! 🏁"
        )
    else:
        text = (
            "📊 <b>Моя статистика</b>\n\n"
            f"🏆 Место в рейтинге: <b>#{rank}</b>\n"
            f"⭐ Всего очков: <b>{total}</b>\n"
            f"🏁 Гонок оценено: <b>{races}</b>\n"
            f"📋 Прогнозов сделано: <b>{made}</b>\n"
            f"📈 Среднее за гонку: <b>{avg:.1f}</b>\n"
            f"🔝 Лучший результат: <b>{best}</b>\n\n"
            f"🎯 Точных попаданий: <b>{exact}</b> ({exact_pct})\n"
            f"📍 В топе (не та позиция): <b>{top}</b>\n"
            f"🥇 Победитель угадан: <b>{p1_str}</b>"
        )

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")
    ]])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
