# F1 2026 Driver lineup
DRIVERS = [
    {"id": "VER", "name": "Verstappen",   "full_name": "Max Verstappen",        "team": "Red Bull",      "number": 1},
    {"id": "LAW", "name": "Lawson",       "full_name": "Liam Lawson",            "team": "Red Bull",      "number": 30},
    {"id": "LEC", "name": "Leclerc",      "full_name": "Charles Leclerc",        "team": "Ferrari",       "number": 16},
    {"id": "HAM", "name": "Hamilton",     "full_name": "Lewis Hamilton",         "team": "Ferrari",       "number": 44},
    {"id": "RUS", "name": "Russell",      "full_name": "George Russell",         "team": "Mercedes",      "number": 63},
    {"id": "ANT", "name": "Antonelli",    "full_name": "Andrea Kimi Antonelli",  "team": "Mercedes",      "number": 12},
    {"id": "NOR", "name": "Norris",       "full_name": "Lando Norris",           "team": "McLaren",       "number": 4},
    {"id": "PIA", "name": "Piastri",      "full_name": "Oscar Piastri",          "team": "McLaren",       "number": 81},
    {"id": "ALO", "name": "Alonso",       "full_name": "Fernando Alonso",        "team": "Aston Martin",  "number": 14},
    {"id": "STR", "name": "Stroll",       "full_name": "Lance Stroll",           "team": "Aston Martin",  "number": 18},
    {"id": "GAS", "name": "Gasly",        "full_name": "Pierre Gasly",           "team": "Alpine",        "number": 10},
    {"id": "DOO", "name": "Doohan",       "full_name": "Jack Doohan",            "team": "Alpine",        "number": 7},
    {"id": "SAI", "name": "Sainz",        "full_name": "Carlos Sainz",           "team": "Williams",      "number": 55},
    {"id": "ALB", "name": "Albon",        "full_name": "Alex Albon",             "team": "Williams",      "number": 23},
    {"id": "TSU", "name": "Tsunoda",      "full_name": "Yuki Tsunoda",           "team": "Racing Bulls",  "number": 22},
    {"id": "HAD", "name": "Hadjar",       "full_name": "Isack Hadjar",           "team": "Racing Bulls",  "number": 6},
    {"id": "BEA", "name": "Bearman",      "full_name": "Oliver Bearman",         "team": "Haas",          "number": 87},
    {"id": "OCO", "name": "Ocon",         "full_name": "Esteban Ocon",           "team": "Haas",          "number": 31},
    {"id": "HUL", "name": "Hulkenberg",   "full_name": "Nico Hulkenberg",        "team": "Audi",          "number": 27},
    {"id": "BOR", "name": "Bortoleto",    "full_name": "Gabriel Bortoleto",      "team": "Audi",          "number": 5},
]

DRIVER_BY_ID = {d["id"]: d for d in DRIVERS}


def get_driver_display(driver_id: str) -> str:
    d = DRIVER_BY_ID.get(driver_id)
    if not d:
        return driver_id
    return f"#{d['number']} {d['full_name']} ({d['team']})"


def get_driver_short(driver_id: str) -> str:
    d = DRIVER_BY_ID.get(driver_id)
    if not d:
        return driver_id
    return f"{d['name']} ({d['team']})"
