#!/usr/bin/env python3
"""
Test script to verify FastF1 integration and fetch past race results.

Usage:
  python test_fastf1.py                 # test first 3 races
  python test_fastf1.py AUS             # test AUS race
  python test_fastf1.py CHN sprint      # test CHN sprint
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fastf1
from data.drivers import DRIVERS
from data.calendar_2026 import RACES_2026
from data.race_mappings import RACE_ID_TO_FASTF1_NAME

RACE_BY_ID = {r["id"]: r for r in RACES_2026}


async def test_fetch_results(race_id: str, is_sprint: bool = False):
    race = RACE_BY_ID.get(race_id.upper())
    if not race:
        print(f"❌ Race {race_id!r} not found in 2026 calendar")
        print(f"   Available: {', '.join(RACE_BY_ID)}")
        return

    race_name    = race["name"]
    session_type = "Sprint" if is_sprint else "Race"
    gp_name      = RACE_ID_TO_FASTF1_NAME.get(race_id.upper())

    if not gp_name:
        print(f"❌ No FastF1 name mapping for {race_id}")
        return

    print(f"\n🏁 Fetching {session_type} results for {race_name} (FastF1 name: {gp_name!r})...")

    try:
        number_to_code = {d["number"]: d["id"] for d in DRIVERS}
        driver_by_id   = {d["id"]: d for d in DRIVERS}

        loop    = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: fastf1.get_session(2026, gp_name, "S" if is_sprint else "R"),
        )

        if not session:
            print(f"❌ Session not found")
            return

        print(f"📡 Loading session data (results only)...")
        await loop.run_in_executor(
            None,
            lambda: session.load(laps=False, telemetry=False, weather=False, messages=False),
        )

        results_df = session.results
        if results_df is None or len(results_df) == 0:
            print("❌ No results found. Data may not be available yet.")
            return

        print(f"\n✅ Found {len(results_df)} entries\n")
        print(f"{'Pos':<4} {'#':<4} {'Code':<6} {'Name':<26} Status")
        print("-" * 65)

        positions = []
        for pos_num, (_, row) in enumerate(results_df.iterrows(), 1):
            driver_code = None

            abbrev = str(row.get("Abbreviation", "") or "").upper().strip()
            if abbrev and abbrev in driver_by_id:
                driver_code = abbrev

            if not driver_code:
                raw_num = row.get("DriverNumber") or row.get("Driver")
                if raw_num is not None:
                    try:
                        driver_code = number_to_code.get(int(raw_num))
                    except (ValueError, TypeError):
                        pass

            if not driver_code:
                print(f"{pos_num:<4} #{row.get('DriverNumber','?'):<3} {'???':<6} {'Unknown driver':<26} {row.get('Status','')}")
                continue

            d      = driver_by_id.get(driver_code, {})
            name   = d.get("full_name", driver_code)
            status = str(row.get("Status", "Finished"))
            print(f"{pos_num:<4} #{d.get('number','?'):<3} {driver_code:<6} {name:<26} {status}")
            positions.append(driver_code)

        print(f"\n📋 Result order ({len(positions)} drivers):")
        print("   " + ", ".join(positions))

        return positions

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    # Parse CLI args: test_fastf1.py [RACE_ID [race|sprint]]
    if len(sys.argv) >= 2:
        race_id   = sys.argv[1].upper()
        is_sprint = len(sys.argv) >= 3 and sys.argv[2].lower() == "sprint"
        await test_fetch_results(race_id, is_sprint)
        return

    # Default: test first few already-finished races
    print("=" * 65)
    print("FastF1 Integration Test — F1 2026")
    print("=" * 65)

    tests = [
        ("AUS", False),
        ("CHN", True),
        ("CHN", False),
        ("JPN", False),
    ]
    for race_id, is_sprint in tests:
        await test_fetch_results(race_id, is_sprint)


if __name__ == "__main__":
    asyncio.run(main())
