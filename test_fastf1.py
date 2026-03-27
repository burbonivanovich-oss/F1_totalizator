#!/usr/bin/env python3
"""Test script to verify FastF1 integration and fetch past race results."""

import asyncio
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fastf1
from data.drivers import DRIVERS
from handlers.calendar_handler import RACES_2026


async def test_fetch_results(race_id: str, is_sprint: bool = False):
    """Test fetching results from FastF1."""

    # Find race in calendar
    race = next((r for r in RACES_2026 if r["id"] == race_id), None)
    if not race:
        print(f"❌ Race {race_id} not found in calendar")
        return

    race_name = race["name"]
    session_type = "Sprint" if is_sprint else "Race"

    print(f"\n🏁 Fetching {session_type} results for {race_name}...")

    try:
        # Build driver number to code mapping
        number_to_code = {d["number"]: d["id"] for d in DRIVERS}

        # Fetch session
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: fastf1.get_session(2026, race_id, "S" if is_sprint else "R")
        )

        print(f"📡 Loading data from F1 API...")
        await loop.run_in_executor(None, lambda: session.load())

        # Get results
        results_df = session.results

        if results_df is None or len(results_df) == 0:
            print(f"❌ No results found")
            return

        print(f"\n✅ Found {len(results_df)} drivers\n")
        print(f"{'Pos':<4} {'#':<3} {'Driver Code':<12} {'Name':<25} {'Status'}")
        print("-" * 75)

        positions = []
        for idx, row in results_df.iterrows():
            driver_number = row.get("DriverNumber") or row.get("Driver")

            if driver_number is None:
                continue

            driver_number = int(driver_number) if isinstance(driver_number, (int, float)) else driver_number
            driver_code = number_to_code.get(driver_number)

            if not driver_code:
                print(f"{idx+1:<4} {driver_number:<3} {'UNKNOWN':<12} Status: {row.get('Status', 'Unknown')}")
                continue

            # Get driver name
            driver_data = next((d for d in DRIVERS if d["id"] == driver_code), {})
            driver_name = driver_data.get("full_name", "Unknown")
            status = row.get("Status", "Finished")

            print(f"{idx+1:<4} {driver_number:<3} {driver_code:<12} {driver_name:<25} {status}")
            positions.append(driver_code)

        print(f"\n📋 Final order ({len(positions)} finished):")
        print(f"   {', '.join(positions)}")

        return positions

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run tests for recent races."""
    print("=" * 75)
    print("FastF1 Integration Test")
    print("=" * 75)

    # Test past races
    races_to_test = [
        ("AUS", False),  # Australian GP (past)
        ("CHN", True),   # Chinese GP Sprint (if available)
        ("CHN", False),  # Chinese GP Race
    ]

    for race_id, is_sprint in races_to_test:
        await test_fetch_results(race_id, is_sprint)


if __name__ == "__main__":
    asyncio.run(main())
