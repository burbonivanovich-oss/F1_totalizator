# F1 2026 Scoring rules
#
# Points awarded for predictions on sprint (top 10) and race (top 16).
# Users predict 16 drivers for race, 10 drivers for sprint in exact order.

SCORING_CONFIG = {
    # 1. Exact hit — driver in the same predicted position
    "exact_position": {
        "sprint": 5,   # Sprint exact match
        "race": 10,    # Race exact match
    },

    # 2. Top hit — driver finished in top, but not predicted position
    "top_hit_wrong_position": {
        "sprint": 2,   # Sprint top hit, wrong position
        "race": 3,     # Race top hit, wrong position
    },

    # 3. Bonus for correct winner (P1 prediction matches actual winner)
    "p1_winner_bonus": {
        "sprint": 3,   # Additional points if P1 is correct (sprint)
        "race": 5,     # Additional points if P1 is correct (race)
    },

    # 4. Penalty for driver not in results (DNF, disqualified, etc.)
    "not_in_results_penalty": -1,
}


def calculate_score(
    prediction: dict,      # {"positions": ["VER", "HAM", "LEC", ...]}
    result: dict,          # {"positions": ["VER", "LEC", "HAM", ...]}
    is_sprint: bool = False,
) -> dict:
    """
    Calculates points for top 16 (race) or top 10 (sprint) predictions.

    Returns a dict with:
      - total: int (final points for this race)
      - breakdown: list of str (human-readable scoring breakdown)
    """
    cfg = SCORING_CONFIG
    race_type = "sprint" if is_sprint else "race"
    expected_len = 10 if is_sprint else 16

    pred_list = prediction.get("positions", [])
    result_list = result.get("positions", [])

    # Guard against corrupted data: scoring requires both lists in expected shape.
    if not isinstance(pred_list, list) or not isinstance(result_list, list):
        return {"total": 0, "breakdown": ["Ошибка: некорректные данные прогноза/результата."]}
    if len(pred_list) != expected_len:
        return {"total": 0, "breakdown": [f"Ошибка: ожидалось {expected_len} позиций в прогнозе, получено {len(pred_list)}."]}
    if len(result_list) == 0:
        return {"total": 0, "breakdown": ["Ошибка: пустой список результатов гонки."]}
    if len(set(pred_list)) != len(pred_list):
        return {"total": 0, "breakdown": ["Ошибка: в прогнозе есть дублирующиеся гонщики."]}

    # Build position maps (1-indexed)
    pred_positions = {i + 1: driver for i, driver in enumerate(pred_list)}
    result_positions = {i + 1: driver for i, driver in enumerate(result_list)}
    result_drivers = set(result_list)

    points = 0
    breakdown = []

    for pos in sorted(pred_positions.keys()):
        pred_driver = pred_positions[pos]
        actual_driver = result_positions.get(pos)

        if pred_driver == actual_driver:
            earned = cfg["exact_position"][race_type]
            points += earned
            breakdown.append(f"+{earned} точное P{pos}: {pred_driver}")

            if pos == 1:
                bonus = cfg["p1_winner_bonus"][race_type]
                points += bonus
                breakdown.append(f"+{bonus} бонус за победителя!")

        elif pred_driver in result_drivers:
            earned = cfg["top_hit_wrong_position"][race_type]
            points += earned
            try:
                actual_pos = result_list.index(pred_driver) + 1
                breakdown.append(f"+{earned} {pred_driver} в топе (P{actual_pos}, предсказано P{pos})")
            except ValueError:
                # Should not happen if logic is correct, but handle gracefully
                breakdown.append(f"+{earned} {pred_driver} в топе (предсказано P{pos})")
        else:
            penalty = cfg["not_in_results_penalty"]
            points += penalty
            breakdown.append(f"{penalty} {pred_driver} — не финишировал")

    return {"total": points, "breakdown": breakdown}
