import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# How many minutes before race start predictions are locked
PREDICTION_LOCK_MINUTES = 5

# Timezone for race times
RACE_TIMEZONE = "UTC"
