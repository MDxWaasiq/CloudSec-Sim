import random
from server.environment import env
from models import Action

def get_resources(obs):
    if hasattr(obs, "resources"):
        return obs.resources
    elif isinstance(obs, dict):
        return obs.get("observation", obs).get("resources", [])
    return []


def get_action(obs):
    res_list = get_resources(obs)
    res = {r["id"]: r["value"] for r in res_list}

    if res.get("s3_public", False):
        return {"action_type": "restrict_s3", "resource_id": "s3_public"}

    if not res.get("s3_encryption", True):
        return {"action_type": "enable_encryption", "resource_id": "s3_encryption"}

    if res.get("iam_key_age", 0) > 0:
        return {"action_type": "rotate_key", "resource_id": "iam_key_age"}

    if not res.get("iam_mfa_enabled", True):
        return {"action_type": "enable_mfa", "resource_id": "iam_mfa_enabled"}

    if not getattr(env, "investigated", False):
        return {"action_type": "read_logs", "resource_id": "logs"}
    
    if not getattr(env, "checked_ip", False):
        return {"action_type": "escalate_incident", "resource_id": "incident"}
    
    if getattr(env, "ip_reputation", None) == "malicious":
        return {"action_type": "quarantine_host", "resource_id": "host"}
    
    return {"action_type": "escalate_incident", "resource_id": "incident"}

    return None


def run_baseline(difficulty="easy"):
    random.seed(42)

    obs = env.reset(difficulty)
    done = False
    steps = 0
    final_score = 0.0

    visited = set()

    max_steps = {"easy": 4, "medium": 6, "hard": 8}

    while not done and steps < max_steps[difficulty]:

        action = get_action(obs)

        if action is None:
            break

        key = (action["action_type"], action["resource_id"])
        if key in visited:
            break

        visited.add(key)

        obs, reward, done, _ = env.step(Action(**action))

        final_score = reward
        steps += 1

    return round(final_score, 2)