import aiosqlite
import json
from datetime import datetime, timezone
from typing import Optional

DB_PATH = "f1_totalizator.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username    TEXT,
                full_name   TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                race_id      TEXT NOT NULL,
                is_sprint    INTEGER NOT NULL DEFAULT 0,
                positions    TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                updated_at   TEXT NOT NULL,
                UNIQUE(user_id, race_id, is_sprint),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                race_id     TEXT NOT NULL,
                is_sprint   INTEGER NOT NULL DEFAULT 0,
                positions   TEXT NOT NULL,
                entered_at  TEXT NOT NULL,
                UNIQUE(race_id, is_sprint)
            );

            CREATE TABLE IF NOT EXISTS scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                race_id     TEXT NOT NULL,
                is_sprint   INTEGER NOT NULL DEFAULT 0,
                points      INTEGER NOT NULL,
                breakdown   TEXT NOT NULL,
                calculated_at TEXT NOT NULL,
                UNIQUE(user_id, race_id, is_sprint),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)
        await db.commit()


# ── Users ────────────────────────────────────────────────────────────────────

async def upsert_user(telegram_id: int, username: Optional[str], full_name: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO users (telegram_id, username, full_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
        """, (telegram_id, username, full_name, now))
        await db.commit()
        async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
            row = await cur.fetchone()
            return row[0]


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ── Predictions ───────────────────────────────────────────────────────────────

async def save_prediction(
    user_id: int, race_id: str, is_sprint: bool,
    positions: list[str],
) -> None:
    """Save prediction with ordered list of driver IDs (16 for race, 10 for sprint)."""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat()
        positions_json = json.dumps(positions, ensure_ascii=False)
        await db.execute("""
            INSERT INTO predictions (user_id, race_id, is_sprint, positions, submitted_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, race_id, is_sprint) DO UPDATE SET
                positions = excluded.positions,
                updated_at = excluded.updated_at
        """, (user_id, race_id, int(is_sprint), positions_json, now, now))
        await db.commit()


async def get_prediction(user_id: int, race_id: str, is_sprint: bool) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM predictions
            WHERE user_id = ? AND race_id = ? AND is_sprint = ?
        """, (user_id, race_id, int(is_sprint))) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            result = dict(row)
            try:
                result["positions"] = json.loads(result["positions"])
            except json.JSONDecodeError:
                return None  # Return None instead of crashing on corrupted data
            return result


async def get_user_predictions(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM predictions WHERE user_id = ?
            ORDER BY submitted_at DESC
        """, (user_id,)) as cur:
            rows = await cur.fetchall()
            results = []
            for r in rows:
                row_dict = dict(r)
                try:
                    row_dict["positions"] = json.loads(row_dict["positions"])
                    results.append(row_dict)
                except json.JSONDecodeError:
                    # Skip corrupted records instead of crashing
                    continue
            return results


# ── Results ───────────────────────────────────────────────────────────────────

async def save_result(race_id: str, is_sprint: bool, positions: list[str]) -> None:
    """Save race result with ordered list of driver IDs (16 for race, 10 for sprint)."""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat()
        positions_json = json.dumps(positions, ensure_ascii=False)
        await db.execute("""
            INSERT INTO results (race_id, is_sprint, positions, entered_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(race_id, is_sprint) DO UPDATE SET
                positions = excluded.positions,
                entered_at = excluded.entered_at
        """, (race_id, int(is_sprint), positions_json, now))
        await db.commit()


async def get_result(race_id: str, is_sprint: bool) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM results WHERE race_id = ? AND is_sprint = ?
        """, (race_id, int(is_sprint))) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            result = dict(row)
            try:
                result["positions"] = json.loads(result["positions"])
            except json.JSONDecodeError:
                return None
            return result


async def get_all_predictions_for_race(race_id: str, is_sprint: bool) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, u.telegram_id, u.full_name
            FROM predictions p
            JOIN users u ON u.id = p.user_id
            WHERE p.race_id = ? AND p.is_sprint = ?
        """, (race_id, int(is_sprint))) as cur:
            rows = await cur.fetchall()
            results = []
            for r in rows:
                row_dict = dict(r)
                try:
                    row_dict["positions"] = json.loads(row_dict["positions"])
                    results.append(row_dict)
                except json.JSONDecodeError:
                    # Skip corrupted records
                    continue
            return results


# ── Scores ────────────────────────────────────────────────────────────────────

async def save_score(
    user_id: int, race_id: str, is_sprint: bool,
    points: int, breakdown: list[str],
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO scores (user_id, race_id, is_sprint, points, breakdown, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, race_id, is_sprint) DO UPDATE SET
                points = excluded.points,
                breakdown = excluded.breakdown,
                calculated_at = excluded.calculated_at
        """, (user_id, race_id, int(is_sprint), points, json.dumps(breakdown, ensure_ascii=False), now))
        await db.commit()


async def get_score(user_id: int, race_id: str, is_sprint: bool) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM scores WHERE user_id = ? AND race_id = ? AND is_sprint = ?
        """, (user_id, race_id, int(is_sprint))) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_leaderboard() -> list[dict]:
    """Returns list of {full_name, telegram_id, total_points, races_count}."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT u.full_name, u.telegram_id,
                   COALESCE(SUM(s.points), 0) AS total_points,
                   COUNT(s.id) AS races_count
            FROM users u
            LEFT JOIN scores s ON s.user_id = u.id
            GROUP BY u.id
            ORDER BY total_points DESC, races_count DESC
        """) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_user_scores(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM scores WHERE user_id = ?
            ORDER BY calculated_at DESC
        """, (user_id,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_user_full_stats(user_id: int) -> dict:
    """Comprehensive per-user statistics: points, accuracy, rank."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("""
            SELECT
                COUNT(*)          AS races_scored,
                COALESCE(SUM(points), 0)   AS total_points,
                COALESCE(MAX(points), 0)   AS best_race,
                COALESCE(AVG(points), 0.0) AS avg_points
            FROM scores WHERE user_id = ?
        """, (user_id,)) as cur:
            score_row = dict(await cur.fetchone() or {})

        async with db.execute(
            "SELECT COUNT(*) AS predictions_made FROM predictions WHERE user_id = ?",
            (user_id,),
        ) as cur:
            pred_row = dict(await cur.fetchone() or {})

        # Cross predictions with actual results to compute accuracy
        async with db.execute("""
            SELECT p.positions AS pred_pos, r.positions AS result_pos
            FROM predictions p
            JOIN results r ON r.race_id = p.race_id AND r.is_sprint = p.is_sprint
            WHERE p.user_id = ?
        """, (user_id,)) as cur:
            matched = [dict(r) for r in await cur.fetchall()]

        exact_hits = top_hits = total_slots = p1_correct = 0
        p1_total = len(matched)

        for row in matched:
            try:
                pred = json.loads(row["pred_pos"])
                result = json.loads(row["result_pos"])
                result_set = set(result)

                for i, driver in enumerate(pred):
                    total_slots += 1
                    if i < len(result) and result[i] == driver:
                        exact_hits += 1
                    elif driver in result_set:
                        top_hits += 1

                if pred and result and pred[0] == result[0]:
                    p1_correct += 1
            except (json.JSONDecodeError, IndexError, KeyError):
                pass

        # Global rank: count users with strictly more points
        async with db.execute("""
            SELECT COUNT(*) + 1 AS rank FROM (
                SELECT user_id, SUM(points) AS pts
                FROM scores GROUP BY user_id
            ) WHERE pts > COALESCE(
                (SELECT SUM(points) FROM scores WHERE user_id = ?), 0
            )
        """, (user_id,)) as cur:
            rank_row = await cur.fetchone()

        return {
            "races_scored":      score_row.get("races_scored", 0),
            "total_points":      score_row.get("total_points", 0),
            "best_race":         score_row.get("best_race", 0),
            "avg_points":        float(score_row.get("avg_points", 0)),
            "predictions_made":  pred_row.get("predictions_made", 0),
            "exact_hits":        exact_hits,
            "top_hits":          top_hits,
            "total_slots":       total_slots,
            "p1_correct":        p1_correct,
            "p1_total":          p1_total,
            "rank":              rank_row[0] if rank_row else 1,
        }


async def get_all_users() -> list[dict]:
    """Return all registered users ordered by registration date."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY created_at ASC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
