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
    raw_score = grade_task(env.current_difficulty, env.reward_history)
    final_safe_score = max(0.01, min(0.99, float(raw_score)))
    
    return {
        "score": round(final_safe_score, 3)
    }

@app.get("/baseline")
def get_baseline():
    return {
        "easy": run_baseline("easy"),
        "medium": run_baseline("medium"),
        "hard": run_baseline("hard"),
    }

def get_task_info(difficulty):
    info = {
        "Easy": "Fix S3 public access (1-step task)",
        "Medium": "Fix IAM issues (key rotation + MFA)",
        "Hard": "SOC investigation → analyze → respond"
    }
    return info[difficulty]

def ui_reset(difficulty):
    """Manually resets the environment and clears history."""
    obs = env.reset(difficulty.lower())
    state = env.get_state()
  
    alerts = "\n\n".join([json.dumps(a, indent=2) for a in getattr(obs, "alerts", [])])
    logs = "\n\n".join([json.dumps(l, indent=2) for l in getattr(obs, "logs", [])])
    
    empty_history = pd.DataFrame(columns=["Step", "Action", "Target", "Score"])
    
    return json.dumps(state, indent=2), empty_history, alerts, logs, 0

def ui_get_state():
    """Fetches the current raw JSON state."""
    state = env.get_state()
    return json.dumps(state, indent=2)

def ui_step(action_type, resource_id, step_count, history_df):
    """Executes a single manual step in the environment."""
    if not action_type or not resource_id:
        return gr.update(), history_df, gr.update(), gr.update(), step_count

    action = Action(action_type=action_type, resource_id=resource_id)
    obs, reward, done, _ = env.step(action)
    
    step_count += 1
    
    # Update History Table
    new_row = {"Step": step_count, "Action": action_type, "Target": resource_id, "Score": round(reward, 2)}
    updated_history = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
    
    state = env.get_state()
    alerts = "\n\n".join([json.dumps(a, indent=2) for a in getattr(obs, "alerts", [])])
    logs = "\n\n".join([json.dumps(l, indent=2) for l in getattr(obs, "logs", [])])

    return json.dumps(state, indent=2), updated_history, alerts, logs, step_count

with gr.Blocks() as demo:
    gr.Markdown("# CloudSec-Sim Manual Playground")
    gr.Markdown("Step-by-step diagnostic interface for agent and environment evaluation.")

    step_counter = gr.State(0)
    history_state = gr.State(pd.DataFrame(columns=["Step", "Action", "Target", "Score"]))

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 1. Environment Controls")
            difficulty_dd = gr.Dropdown(["Easy", "Medium", "Hard"], value="Easy", label="Difficulty")
            task_text = gr.Markdown(get_task_info("Easy"))
            difficulty_dd.change(get_task_info, inputs=difficulty_dd, outputs=task_text)
            
            with gr.Row():
                btn_reset = gr.Button("🔄 Reset Env", variant="secondary")
                btn_state = gr.Button("🔍 Get State", variant="secondary")

            gr.Markdown("### 2. Manual Action Override")
            action_dd = gr.Dropdown(
                choices=["restrict_s3", "rotate_key", "enable_mfa", "read_logs", "check_ip_reputation", "quarantine_host", "escalate_incident"], 
                label="Action Type"
            )
            resource_txt = gr.Textbox(label="Resource ID Target", placeholder="e.g., s3_public or iam_key_age")
            btn_step = gr.Button("▶ Execute Step", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("### Live State & Outputs")
            with gr.Accordion("Raw JSON State", open=True):
                state_box = gr.Code(language="json", label="env.get_state()")
            
            history_table = gr.Dataframe(headers=["Step", "Action", "Target", "Score"], interactive=False)
            
            with gr.Row():
                alerts_box = gr.Textbox(label="Alerts", lines=4)
                logs_box = gr.Textbox(label="Logs", lines=4)

    btn_reset.click(
        fn=ui_reset,
        inputs=[difficulty_dd],
        outputs=[state_box, history_table, alerts_box, logs_box, step_counter]
    )

    btn_state.click(
        fn=ui_get_state,
        inputs=[],
        outputs=[state_box]
    )

    btn_step.click(
        fn=ui_step,
        inputs=[action_dd, resource_txt, step_counter, history_table],
        outputs=[state_box, history_table, alerts_box, logs_box, step_counter]
    )

app = gr.mount_gradio_app(app, demo, path="/") 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
