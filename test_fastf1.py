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

# Mapping from race ID to FastF1 GP name
RACE_ID_TO_FASTF1_NAME = {
    "AUS": "Australia",
    "CHN": "China",
    "JPN": "Japan",
    "MIA": "Miami",
    "CAN": "Canada",
    "MON": "Monaco",
    "ESP": "Spain",
    "AUT": "Austria",
    "GBR": "Britain",
    "BEL": "Belgium",
    "HUN": "Hungary",
    "NED": "Netherlands",
    "ITA": "Italy",
    "MAD": "Madrid",
    "AZE": "Azerbaijan",
    "SGP": "Singapore",
    "USA": "United States",
    "MEX": "Mexico",
    "BRA": "Brazil",
    "LVG": "Las Vegas",
    "QAT": "Qatar",
    "ABU": "Abu Dhabi",
}


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

        # Convert race ID to FastF1 GP name
        gp_name = RACE_ID_TO_FASTF1_NAME.get(race_id)
        if not gp_name:
            print(f"❌ Unknown race ID {race_id}")
            return

        # Fetch session
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: fastf1.get_session(2026, gp_name, "S" if is_sprint else "R")
        )

        if not session:
            print(f"❌ Could not find session for {race_name}")
            return

        print(f"📡 Loading data from F1 API...")
        await loop.run_in_executor(None, lambda: session.load())

        # Get results
        results_df = session.results

        if results_df is None or len(results_df) == 0:
            print(f"❌ No results found")
            return

        # Filter only drivers who finished and sort by Position/ClassifiedPosition
        finished_df = results_df[results_df['Status'] == '+0:00:00.000'].copy() if 'Status' in results_df.columns else results_df.copy()

        # Sort by Position if available, otherwise by ClassifiedPosition
        if 'Position' in finished_df.columns:
            sorted_results = finished_df.sort_values('Position', na_position='last')
        elif 'ClassifiedPosition' in finished_df.columns:
            sorted_results = finished_df.sort_values('ClassifiedPosition', na_position='last')
        else:
            sorted_results = finished_df

        print(f"\n✅ Found {len(results_df)} drivers ({len(sorted_results)} finished)\n")
        print(f"{'Pos':<4} {'#':<3} {'Code':<8} {'Driver Name':<28} {'Time / Gap':<15}")
        print("-" * 90)

        positions = []
        for idx, row in sorted_results.iterrows():
            driver_number = row.get("DriverNumber") or row.get("Driver")

            if driver_number is None:
                continue

            try:
                driver_number = int(driver_number)
            except (ValueError, TypeError):
                continue

            driver_code = number_to_code.get(driver_number)

            if not driver_code:
                continue

            # Get driver name
            driver_data = next((d for d in DRIVERS if d["id"] == driver_code), {})
            driver_name = driver_data.get("full_name", "Unknown")

            # Get time/gap info
            time_info = ""
            if 'Time' in row and row['Time']:
                time_info = str(row['Time'])[:10]

            delta = row.get('Delta') or row.get('Timedelta')
            if delta:
                time_info = f"+{str(delta)[:8]}"
            elif time_info == "":
                status = row.get("Status", "Finished")
                if status:
                    time_info = str(status)[:15]

            print(f"{idx+1:<4} {driver_number:<3} {driver_code:<8} {driver_name:<28} {time_info:<15}")
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
