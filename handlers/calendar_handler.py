import os
import sys
import importlib.util
from datetime import datetime
import pytz

# Ensure project root is in sys.path (handles all container/deployment scenarios)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


def _load(module_name: str):
    """Load a data module by absolute file path — immune to sys.path issues."""
    path = os.path.join(_root, 'data', module_name + '.py')
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    from data.calendar_2026 import RACES_2026
    from data.drivers import DRIVERS
except (ImportError, FileNotFoundError):
    # Embed data directly if files missing
    RACES_2026 = [
        {
            "id": "AUS",
            "name": "Australian Grand Prix",
            "circuit": "Albert Park Circuit",
            "city": "Melbourne",
            "country": "Australia",
            "flag": "🇦🇺",
            "race_time": datetime(2026, 3, 15, 5, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "CHN",
            "name": "Chinese Grand Prix",
            "circuit": "Shanghai International Circuit",
            "city": "Shanghai",
            "country": "China",
            "flag": "🇨🇳",
            "race_time": datetime(2026, 3, 22, 7, 0, tzinfo=pytz.utc),
            "sprint_time": datetime(2026, 3, 21, 7, 30, tzinfo=pytz.utc),
        },
        {
            "id": "JPN",
            "name": "Japanese Grand Prix",
            "circuit": "Suzuka International Racing Course",
            "city": "Suzuka",
            "country": "Japan",
            "flag": "🇯🇵",
            "race_time": datetime(2026, 4, 5, 5, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "BHR",
            "name": "Bahrain Grand Prix",
            "circuit": "Bahrain International Circuit",
            "city": "Sakhir",
            "country": "Bahrain",
            "flag": "🇧🇭",
            "race_time": datetime(2026, 4, 19, 15, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "SAU",
            "name": "Saudi Arabian Grand Prix",
            "circuit": "Jeddah Corniche Circuit",
            "city": "Jeddah",
            "country": "Saudi Arabia",
            "flag": "🇸🇦",
            "race_time": datetime(2026, 4, 26, 17, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "MIA",
            "name": "Miami Grand Prix",
            "circuit": "Miami International Autodrome",
            "city": "Miami",
            "country": "United States",
            "flag": "🇺🇸",
            "race_time": datetime(2026, 5, 10, 19, 0, tzinfo=pytz.utc),
            "sprint_time": datetime(2026, 5, 9, 19, 0, tzinfo=pytz.utc),
        },
        {
            "id": "EMI",
            "name": "Emilia Romagna Grand Prix",
            "circuit": "Autodromo Enzo e Dino Ferrari",
            "city": "Imola",
            "country": "Italy",
            "flag": "🇮🇹",
            "race_time": datetime(2026, 5, 24, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "MON",
            "name": "Monaco Grand Prix",
            "circuit": "Circuit de Monaco",
            "city": "Monaco",
            "country": "Monaco",
            "flag": "🇲🇨",
            "race_time": datetime(2026, 6, 7, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "ESP",
            "name": "Spanish Grand Prix",
            "circuit": "Circuit de Barcelona-Catalunya",
            "city": "Barcelona",
            "country": "Spain",
            "flag": "🇪🇸",
            "race_time": datetime(2026, 6, 21, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "CAN",
            "name": "Canadian Grand Prix",
            "circuit": "Circuit Gilles Villeneuve",
            "city": "Montréal",
            "country": "Canada",
            "flag": "🇨🇦",
            "race_time": datetime(2026, 7, 5, 18, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "AUT",
            "name": "Austrian Grand Prix",
            "circuit": "Red Bull Ring",
            "city": "Spielberg",
            "country": "Austria",
            "flag": "🇦🇹",
            "race_time": datetime(2026, 7, 12, 13, 0, tzinfo=pytz.utc),
            "sprint_time": datetime(2026, 7, 11, 11, 0, tzinfo=pytz.utc),
        },
        {
            "id": "GBR",
            "name": "British Grand Prix",
            "circuit": "Silverstone Circuit",
            "city": "Silverstone",
            "country": "United Kingdom",
            "flag": "🇬🇧",
            "race_time": datetime(2026, 7, 26, 14, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "HUN",
            "name": "Hungarian Grand Prix",
            "circuit": "Hungaroring",
            "city": "Budapest",
            "country": "Hungary",
            "flag": "🇭🇺",
            "race_time": datetime(2026, 8, 2, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "BEL",
            "name": "Belgian Grand Prix",
            "circuit": "Circuit de Spa-Francorchamps",
            "city": "Spa",
            "country": "Belgium",
            "flag": "🇧🇪",
            "race_time": datetime(2026, 8, 30, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "NED",
            "name": "Dutch Grand Prix",
            "circuit": "Circuit Zandvoort",
            "city": "Zandvoort",
            "country": "Netherlands",
            "flag": "🇳🇱",
            "race_time": datetime(2026, 9, 6, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "ITA",
            "name": "Italian Grand Prix",
            "circuit": "Autodromo Nazionale Monza",
            "city": "Monza",
            "country": "Italy",
            "flag": "🇮🇹",
            "race_time": datetime(2026, 9, 13, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "AZE",
            "name": "Azerbaijan Grand Prix",
            "circuit": "Baku City Circuit",
            "city": "Baku",
            "country": "Azerbaijan",
            "flag": "🇦🇿",
            "race_time": datetime(2026, 9, 27, 11, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "SGP",
            "name": "Singapore Grand Prix",
            "circuit": "Marina Bay Street Circuit",
            "city": "Singapore",
            "country": "Singapore",
            "flag": "🇸🇬",
            "race_time": datetime(2026, 10, 4, 12, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "USA",
            "name": "United States Grand Prix",
            "circuit": "Circuit of the Americas",
            "city": "Austin",
            "country": "United States",
            "flag": "🇺🇸",
            "race_time": datetime(2026, 10, 18, 19, 0, tzinfo=pytz.utc),
            "sprint_time": datetime(2026, 10, 17, 19, 0, tzinfo=pytz.utc),
        },
        {
            "id": "MEX",
            "name": "Mexico City Grand Prix",
            "circuit": "Autodromo Hermanos Rodriguez",
            "city": "Mexico City",
            "country": "Mexico",
            "flag": "🇲🇽",
            "race_time": datetime(2026, 11, 1, 20, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "BRA",
            "name": "São Paulo Grand Prix",
            "circuit": "Autodromo Jose Carlos Pace",
            "city": "São Paulo",
            "country": "Brazil",
            "flag": "🇧🇷",
            "race_time": datetime(2026, 11, 8, 17, 0, tzinfo=pytz.utc),
            "sprint_time": datetime(2026, 11, 7, 17, 0, tzinfo=pytz.utc),
        },
        {
            "id": "LVG",
            "name": "Las Vegas Grand Prix",
            "circuit": "Las Vegas Strip Circuit",
            "city": "Las Vegas",
            "country": "United States",
            "flag": "🇺🇸",
            "race_time": datetime(2026, 11, 22, 6, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
        {
            "id": "QAT",
            "name": "Qatar Grand Prix",
            "circuit": "Lusail International Circuit",
            "city": "Lusail",
            "country": "Qatar",
            "flag": "🇶🇦",
            "race_time": datetime(2026, 11, 29, 15, 0, tzinfo=pytz.utc),
            "sprint_time": datetime(2026, 11, 28, 14, 0, tzinfo=pytz.utc),
        },
        {
            "id": "ABU",
            "name": "Abu Dhabi Grand Prix",
            "circuit": "Yas Marina Circuit",
            "city": "Abu Dhabi",
            "country": "UAE",
            "flag": "🇦🇪",
            "race_time": datetime(2026, 12, 6, 13, 0, tzinfo=pytz.utc),
            "sprint_time": None,
        },
    ]

    DRIVERS = [
        {"id": "VER", "name": "Verstappen",   "full_name": "Max Verstappen",          "team": "Red Bull Racing",  "number": 1},
        {"id": "HAD", "name": "Hadjar",       "full_name": "Isack Hadjar",             "team": "Red Bull Racing",  "number": 6},
        {"id": "LEC", "name": "Leclerc",      "full_name": "Charles Leclerc",          "team": "Ferrari",          "number": 16},
        {"id": "HAM", "name": "Hamilton",     "full_name": "Lewis Hamilton",           "team": "Ferrari",          "number": 44},
        {"id": "RUS", "name": "Russell",      "full_name": "George Russell",           "team": "Mercedes",         "number": 63},
        {"id": "ANT", "name": "Antonelli",    "full_name": "Andrea Kimi Antonelli",    "team": "Mercedes",         "number": 12},
        {"id": "NOR", "name": "Norris",       "full_name": "Lando Norris",             "team": "McLaren",          "number": 4},
        {"id": "PIA", "name": "Piastri",      "full_name": "Oscar Piastri",            "team": "McLaren",          "number": 81},
        {"id": "ALO", "name": "Alonso",       "full_name": "Fernando Alonso",          "team": "Aston Martin",     "number": 14},
        {"id": "STR", "name": "Stroll",       "full_name": "Lance Stroll",             "team": "Aston Martin",     "number": 18},
        {"id": "GAS", "name": "Gasly",        "full_name": "Pierre Gasly",             "team": "Alpine",           "number": 10},
        {"id": "COL", "name": "Colapinto",    "full_name": "Franco Colapinto",         "team": "Alpine",           "number": 43},
        {"id": "HUL", "name": "Hulkenberg",   "full_name": "Nico Hulkenberg",          "team": "Audi",             "number": 27},
        {"id": "BOR", "name": "Bortoleto",    "full_name": "Gabriel Bortoleto",        "team": "Audi",             "number": 5},
        {"id": "SAI", "name": "Sainz",        "full_name": "Carlos Sainz",             "team": "Williams",         "number": 55},
        {"id": "ALB", "name": "Albon",        "full_name": "Alexander Albon",          "team": "Williams",         "number": 23},
        {"id": "PER", "name": "Perez",        "full_name": "Sergio Perez",             "team": "Cadillac",         "number": 11},
        {"id": "BOT", "name": "Bottas",       "full_name": "Valtteri Bottas",          "team": "Cadillac",         "number": 77},
        {"id": "LAW", "name": "Lawson",       "full_name": "Liam Lawson",              "team": "Racing Bulls",     "number": 30},
        {"id": "LIN", "name": "Lindblad",     "full_name": "Arvid Lindblad",           "team": "Racing Bulls",     "number": 45},
        {"id": "OCO", "name": "Ocon",         "full_name": "Esteban Ocon",             "team": "Haas",             "number": 31},
        {"id": "BEA", "name": "Bearman",      "full_name": "Oliver Bearman",           "team": "Haas",             "number": 87},
    ]

RACE_BY_ID = {r["id"]: r for r in RACES_2026}
DRIVER_BY_ID = {d["id"]: d for d in DRIVERS}
SPRINT_RACE_IDS = {r["id"] for r in RACES_2026 if r["sprint_time"] is not None}


def get_driver_short(driver_id: str) -> str:
    d = DRIVER_BY_ID.get(driver_id)
    if not d:
        return driver_id
    return f"{d['name']} ({d['team']})"


from datetime import timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


def _race_status(race: dict) -> str:
    now = datetime.now(timezone.utc)
    if race["race_time"] < now:
        return "✅"
    return "🔜"


async def show_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(timezone.utc)
    lines = ["🏁 <b>Календарь Формулы 1 — 2026</b>\n"]

    for race in RACES_2026:
        status = _race_status(race)
        sprint_tag = " 🟣 Sprint" if race["sprint_time"] else ""
        date_str = race["race_time"].strftime("%d %b %H:%M UTC")
        lines.append(
            f"{status} <b>{race['flag']} {race['name']}</b>{sprint_tag}\n"
            f"    📍 {race['circuit']}\n"
            f"    🕒 {date_str}\n"
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


async def show_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Group drivers by team
    teams: dict[str, list] = {}
    for d in DRIVERS:
        teams.setdefault(d["team"], []).append(d)

    lines = ["🏎 <b>Гонщики Ф1 — 2026</b>\n"]
    for team, drivers in teams.items():
        lines.append(f"<b>{team}</b>")
        for d in drivers:
            lines.append(f"  #{d['number']} {d['full_name']}")
        lines.append("")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "\n".join(lines), parse_mode="HTML", reply_markup=kb
        )
    else:
        await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)
