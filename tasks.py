def grade_task(task_id: str, reward_history: list) -> float:
    """
    Deterministic grader using final performance + efficiency.
    """

    if not reward_history:
        return 0.0
    final_score = reward_history[-1]["value"]
    steps = len(reward_history)

    if steps <= 3:
        efficiency_bonus = 0.2
    elif steps <= 6:
        efficiency_bonus = 0.1
    else:
        efficiency_bonus = 0.0

    step_penalty = min(0.2, steps * 0.02)

    score = final_score + efficiency_bonus - step_penalty

    score = max(0.0, min(1.0, score))

    return round(score, 2)