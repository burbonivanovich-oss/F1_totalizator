"""
FastAPI routes for the F1 Totalizator Mini App.
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query, HTTPException

import database as db
from config import PREDICTION_LOCK_MINUTES
from handlers.calendar_handler import DRIVERS, RACES_2026, RACE_BY_ID

router = APIRouter(prefix="/api")


def _is_locked(race: dict, is_sprint: bool) -> bool:
    key = "sprint_time" if is_sprint else "race_time"
    race_time = race.get(key)
    if not race_time:
        return True
    deadline = race_time - timedelta(minutes=PREDICTION_LOCK_MINUTES)
    return datetime.now(timezone.utc) >= deadline


@router.get("/drivers")
async def get_drivers():
    """Return full list of F1 2026 drivers."""
    return DRIVERS


@router.get("/races")
async def get_races():
    """Return list of races that are still open for predictions."""
    now = datetime.now(timezone.utc)
    result = []
    for race in RACES_2026:
        race_open = not _is_locked(race, is_sprint=False)
        sprint_open = (
            race["sprint_time"] is not None
            and not _is_locked(race, is_sprint=True)
        )
        if race_open or sprint_open:
            result.append({
                "id": race["id"],
                "name": race["name"],
                "flag": race["flag"],
                "race_open": race_open,
                "sprint_open": sprint_open,
                "race_deadline": (
                    (race["race_time"] - timedelta(minutes=PREDICTION_LOCK_MINUTES)).isoformat()
                    if race_open else None
                ),
                "sprint_deadline": (
                    (race["sprint_time"] - timedelta(minutes=PREDICTION_LOCK_MINUTES)).isoformat()
                    if sprint_open else None
                ),
            })
    return result


@router.get("/prediction")
async def get_prediction(
    race_id: str = Query(...),
    is_sprint: int = Query(0),
    tg_id: int = Query(...),
):
    """Return existing prediction for a user, or null."""
    user = await db.get_user_by_telegram_id(tg_id)
    if not user:
        return None
    pred = await db.get_prediction(user["id"], race_id.upper(), bool(is_sprint))
    if not pred:
        return None
    return {"positions": pred["positions"]}


@router.get("/race/{race_id}")
async def get_race(race_id: str):
    """Return details for a single race."""
    race = RACE_BY_ID.get(race_id.upper())
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return {
        "id": race["id"],
        "name": race["name"],
        "flag": race["flag"],
        "circuit": race["circuit"],
        "race_time": race["race_time"].isoformat(),
        "sprint_time": race["sprint_time"].isoformat() if race["sprint_time"] else None,
        "race_locked": _is_locked(race, is_sprint=False),
        "sprint_locked": _is_locked(race, is_sprint=True),
    }
