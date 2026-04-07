import gradio as gr
import pandas as pd
from server.environment import env
from models import Action
from baseline import run_baseline
from fastapi import FastAPI
import random
import time
import json
from tasks import grade_task
import uvicorn

app = FastAPI()

@app.get("/tasks")
def get_tasks():
    return {
        "tasks": [
            {
                "id": "easy",
                "name": "S3 Public Access Fix",
                "description": "Detect and restrict public S3 bucket access. Optional: enable encryption.",
                "difficulty": "easy"
            },
            {
                "id": "medium",
                "name": "IAM Security Hardening",
                "description": "Rotate old IAM keys and enforce MFA. Correct order improves score.",
                "difficulty": "medium"
            },
            {
                "id": "hard",
                "name": "Network + Database Security",
                "description": "Close exposed ports and secure RDS. Requires correct sequence of actions.",
                "difficulty": "hard"
            }
        ],
        "action_schema": Action.model_json_schema()
    }

@app.post("/reset")
def reset_env(difficulty: str = "easy"): 
    clean_diff = difficulty.lower() if difficulty else "easy"
    obs = env.reset(clean_diff)
    return obs.model_dump()


@app.post("/step")
def step_env(action: Action):
    obs, reward, done, info = env.step(action)

    return {
        "observation": obs.model_dump(),  
        "reward": float(reward),
        "done": bool(done),
        "info": info
    }


@app.get("/state")
def get_state():
    return env.get_state()


@app.get("/grader")
def get_grader():
    return {
        "score": grade_task(env.current_difficulty, env.reward_history)
    }

@app.get("/baseline")
def get_baseline():
    return {
        "easy": run_baseline("easy"),
        "medium": run_baseline("medium"),
        "hard": run_baseline("hard"),
    }
#------------------------------------------------------------------------------------------------------------------------------------------------
    
def get_task_info(difficulty):
    info = {
        "Easy": "Fix S3 public access (1-step task)",
        "Medium": "Fix IAM issues (key rotation + MFA)",
        "Hard": "SOC investigation → analyze → respond"
    }
    return info[difficulty]


def run_real_simulation(difficulty):
    obs = env.reset(difficulty.lower())

    history = []
    done = False
    step = 0
    final_score = 0

    max_steps = {"Easy": 4, "Medium": 6, "Hard": 8}

    while not done and step < max_steps[difficulty]: 
        r = {x["id"]: x["value"] for x in obs.resources}

        if difficulty == "Easy":
            if r.get("s3_public"):
                action = Action(action_type="restrict_s3", resource_id="s3_public")
            else:
                break

        elif difficulty == "Medium":
            choices = []
            if r.get("iam_key_age", 0) > 0:
                choices.append(Action(action_type="rotate_key", resource_id="iam_key_age"))
            
            if not r.get("iam_mfa_enabled", True):
                choices.append(Action(action_type="enable_mfa", resource_id="iam_mfa_enabled"))
            
            if choices:
                action = random.choice(choices)
            else:
                break

        else:

            if not getattr(env, "investigated", False):
                action = Action(action_type="read_logs", resource_id="logs")

            elif not getattr(env, "checked_ip", False):
                action = Action(action_type="check_ip_reputation", resource_id="ip")

            elif getattr(env, "ip_reputation", None) == "malicious":
                action = Action(action_type="quarantine_host", resource_id="host")

            else:
                action = Action(action_type="escalate_incident", resource_id="incident")
      
        obs, reward, done, _ = env.step(action)

        step += 1
        final_score = round(reward, 2)

        history.append({
            "Step": step,
            "Action": f"{action.action_type} → {action.resource_id}",
            "Score": final_score
        })

    df1 = pd.DataFrame(history)

    baseline_score = round(run_baseline(difficulty.lower()), 2)

    df2 = pd.DataFrame({
        "Type": ["Agent", "Baseline"],
        "Score": [final_score, baseline_score]
    })

    alerts = "\n\n".join([json.dumps(a, indent=2) for a in obs.alerts]) if hasattr(obs, "alerts") else ""
    logs = "\n\n".join([json.dumps(l, indent=2) for l in obs.logs])

    return df1, df2, alerts, logs

with gr.Blocks() as demo:
    gr.Markdown("# CloudSec-Sim")

    alerts_box = gr.Textbox(label="Alerts")
    logs_box = gr.Textbox(label="Logs")

    d = gr.Dropdown(["Easy", "Medium", "Hard"], value="Easy")
    task_text = gr.Markdown()
    d.change(get_task_info, inputs=d, outputs=task_text)

    b = gr.Button("Run Simulation")

    t1 = gr.Dataframe()
    t2 = gr.Dataframe()

    b.click(run_real_simulation, inputs=d, outputs=[t1, t2, alerts_box, logs_box])

app = gr.mount_gradio_app(app, demo, path="/") 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
