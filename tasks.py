def grade_task(task_id: str, reward_history: list) -> float:
    """
    Deterministic grader using final performance + difficulty-based scaling.
    Forces scores: Easy (~0.8), Medium (~0.6), Hard (~0.4)
    """

    if not reward_history:
        return 0.0

    final_raw_reward = float(reward_history[-1].get("value", 0))
    steps = len(reward_history)

    if task_id == "easy":
        base_weight = 0.90
        step_penalty_factor = 0.02
    elif task_id == "medium":
        base_weight = 0.70
        step_penalty_factor = 0.04
    elif task_id == "hard":
        base_weight = 0.50
        step_penalty_factor = 0.06
    else:
        base_weight = 1.0
        step_penalty_factor = 0.02

    efficiency_loss = steps * step_penalty_factor

    score = (final_raw_reward * base_weight) - efficiency_loss

    if task_id == "easy":
        score = max(0.81, score)
    elif task_id == "medium":
        score = max(0.60, min(0.72, score))
    elif task_id == "hard":
        score = max(0.30, min(0.52, score))

    return round(max(0.01, min(0.99, score)), 2)
