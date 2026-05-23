"""
Single source of truth for FastF1 GP name mappings.

FastF1 accepts event names as used in the official F1 schedule.
Import this dict in scheduler.py, handlers/admin.py, and test_fastf1.py.
"""

RACE_ID_TO_FASTF1_NAME: dict[str, str] = {
    "AUS": "Australia",
    "CHN": "China",
    "JPN": "Japan",
    "MIA": "Miami",
    "CAN": "Canada",
    "MON": "Monaco",
    "ESP": "Barcelona",       # Barcelona Grand Prix at Circuit de Barcelona-Catalunya
    "AUT": "Austria",
    "GBR": "Great Britain",
    "BEL": "Belgium",
    "HUN": "Hungary",
    "NED": "Netherlands",
    "ITA": "Italy",
    "MAD": "Madrid",          # Spanish Grand Prix at IFEMA Madrid Circuit
    "AZE": "Azerbaijan",
    "SGP": "Singapore",
    "USA": "United States",
    "MEX": "Mexico",
    "BRA": "Brazil",
    "LVG": "Las Vegas",
    "QAT": "Qatar",
    "ABU": "Abu Dhabi",
}
