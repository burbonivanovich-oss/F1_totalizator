# Scoring configuration — edit freely to adjust the game balance.
#
# The bot awards points for predicting the top-3 (podium) of each race.
# For sprint weekends, the same positions are predicted for the SPRINT race,
# and the sprint score is multiplied by SPRINT_MULTIPLIER.

SCORING_CONFIG = {
    # Points for predicting a driver in the EXACT correct position
    "exact_position": {
        1: 25,   # Bull's-eye on P1
        2: 18,   # Bull's-eye on P2
        3: 15,   # Bull's-eye on P3
    },

    # Points when a driver IS on the podium but in the WRONG predicted position
    # (e.g. you predicted P1 but he finished P2 or P3)
    "podium_but_wrong_position": 5,

    # Penalty when a driver you predicted for the podium MISSED the podium entirely
    "wrong_podium_penalty": -3,

    # Sprint race scores are this fraction of the regular race scores
    "sprint_multiplier": 0.5,

    # --- Optional advanced knobs (set to 0 to disable) ---

    # Bonus for getting the entire podium right (all three in exact order)
    "full_podium_bonus": 10,

    # Bonus for getting all three podium drivers correct (any order)
    "all_drivers_bonus": 5,
}


def calculate_score(
    prediction: dict,      # {"p1": "VER", "p2": "HAM", "p3": "NOR"}
    result: dict,          # {"p1": "VER", "p2": "LEC", "p3": "HAM"}
    is_sprint: bool = False,
) -> dict:
    """
    Returns a dict with:
      - total: int (final points for this race)
      - breakdown: list of str (human-readable description of each earned/lost point)
    """
    cfg = SCORING_CONFIG
    pred_positions = {1: prediction["p1"], 2: prediction["p2"], 3: prediction["p3"]}
    result_positions = {1: result["p1"], 2: result["p2"], 3: result["p3"]}
    result_drivers = set(result_positions.values())

    points = 0
    breakdown = []

    for pos in (1, 2, 3):
        pred_driver = pred_positions[pos]
        actual_driver = result_positions[pos]

        if pred_driver == actual_driver:
            earned = cfg["exact_position"][pos]
            points += earned
            breakdown.append(f"+{earned} за точное P{pos} ({pred_driver})")
        elif pred_driver in result_drivers:
            earned = cfg["podium_but_wrong_position"]
            points += earned
            breakdown.append(f"+{earned} за {pred_driver} на подиуме (не та позиция)")
        else:
            penalty = cfg["wrong_podium_penalty"]
            points += penalty
            breakdown.append(f"{penalty} за {pred_driver} — не попал на подиум")

    # Bonuses
    pred_drivers = set(pred_positions.values())
    if pred_drivers == result_drivers:
        if pred_positions == result_positions:
            bonus = cfg["full_podium_bonus"]
            points += bonus
            breakdown.append(f"+{bonus} бонус за полный подиум в точном порядке!")
        else:
            bonus = cfg["all_drivers_bonus"]
            points += bonus
            breakdown.append(f"+{bonus} бонус за всех трёх гонщиков подиума!")

    if is_sprint:
        multiplier = cfg["sprint_multiplier"]
        original = points
        points = round(points * multiplier)
        breakdown.append(f"× {multiplier} (спринт): {original} → {points}")

    return {"total": points, "breakdown": breakdown}
