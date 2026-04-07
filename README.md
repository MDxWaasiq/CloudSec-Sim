---
title: CloudSec-Sim
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
tags:
  - openenv
  - cybersecurity
  - cloud
  - reinforcement-learning
---

# CloudSec-Sim: Realistic Cloud Security (SOC) Environment

* CloudSec-Sim is a real-world cloud security simulation built on OpenEnv, modeling how SOC analysts detect and respond to threats.

* Cloud security failures are a major real-world problem:

  * IBM (2023): Average breach cost = **$4.45 million**
  * Verizon DBIR: **Credential misuse + misconfigurations** are leading causes of breaches

* Existing AI environments are:

  * Too simple
  * Deterministic
  * Not reflective of real SOC workflows

* Real SOC work requires:

  * Handling noisy logs
  * Interpreting alerts
  * Multi-step decision making under uncertainty

* CloudSec-Sim solves this by providing:

  * Realistic cloud infrastructure scenarios
  * Structured alerts and logs
  * Multi-step remediation tasks
  * Constraints similar to real-world operations

- Result: A practical, high-fidelity environment for evaluating autonomous cybersecurity agents.

---

# Key Features

### Real-World Cloud Security Simulation

Simulates realistic cloud misconfigurations and incidents:

* Public S3 exposure
* IAM credential risks
* Network misconfigurations
* Active attack scenarios (brute force, data exfiltration)

---
# Project Structure

```
CloudSec-Sim/
│
├── server/
│   ├── app.py             
│   └── environment.py      
│
├── models.py           
├── tasks.py                
│
├── baseline.py            
├── inference.py            
│
├── openenv.yaml           
├── Dockerfile             
│
├── requirements.txt        
├── pyproject.toml         
├── uv.lock                 
│
└── README.md               
```
--- 
### Multi-Step SOC Workflow (Hard Task)

```
Investigate → Analyze → Respond → Escalate
```

---

### Rich Observations

Agents receive structured observations:

* Infrastructure state (resources)
* Security alerts (MITRE-style)
* System logs (noisy + adversarial)

### Grading & Reward Logic 

Scoring in CloudSec-Sim is deterministic and based on the agent’s actions and final system state.

---

## Step-Level Reward

### Easy

* `s3_public = True` → **0.0**
* `s3_public = False` → **1.0**
* No penalties
  → Fully binary, single-step task

Why Easy Task is Binary?
The Easy task is binary because fixing a public S3 bucket is a **critical all-or-nothing issue**—it is either secure or not. This ensures clear evaluation, full reproducibility, and serves as a simple baseline before more complex tasks.

---

### Medium

* +0.4 → Key rotated (`iam_key_age = 0`)
* +0.4 → MFA enabled
* Penalty: `-0.05 × steps`

**Final:**

```
score = base_score - (0.05 × steps)
```

Clipped to `[0,1]`

---

### Hard

Progress-based scoring:

* +0.2 → Action started
* +0.2 → Logs read
* +0.2 → IP checked
* +0.2 → Threat contained
* +0.2 → Incident escalated
* +0.1 → Ports secured

Penalty:

* `-0.05 × steps`

→ Encourages correct sequence + efficiency

---

## Final Score (Grader)

Combines outcome + efficiency:

* Bonus:

  * ≤3 steps → +0.2
  * ≤6 steps → +0.1

* Penalty:

  * `min(0.2, steps × 0.02)`

**Final:**

```
final_score = last_reward + bonus - penalty
```

Clipped to `[0,1]`

---

## Key Points

* Deterministic scoring
* Partial rewards (not binary)
* Penalizes extra steps
* Rewards optimal strategies

→ Ensures fair, reproducible evaluation


---

# Environment Design

## Observation Space

```json
{
  "resources": [{"id": "...", "value": "..."}],
  "alerts": [...],
  "logs": [...]
}
```

Includes:

* Cloud configuration state
* Security alerts (threat signals)
* System logs (signal + noise)

---

## Action Space

```python
Action(
    action_type: str,
    resource_id: str
)
```

### Supported Actions

**Cloud Fixes**

* `restrict_s3`
* `enable_encryption`
* `rotate_key`
* `enable_mfa`
* `close_port_22`
* `close_port_80`
* `secure_rds`

**SOC Actions**

* `read_logs`
* `check_ip_reputation`
* `quarantine_host`
* `escalate_incident`

---

# Baseline Agent

* Minimum benchmark
* Validates environment
* Measures agent improvement
* Reproducibility

---

# Running the Environment

## Docker (Recommended)

```bash
docker build -t cloudsec-sim .
docker run -p 7860:7860 cloudsec-sim
```

Then access:

```
http://localhost:7860
```

---

## API Endpoints

| Endpoint    | Description       |
| ----------- | ----------------- |
| `/reset`    | Start new episode |
| `/step`     | Execute action    |
| `/state`    | Get current state |
| `/tasks`    | List tasks        |
| `/grader`   | Get score         |
| `/baseline` | Run baseline      |

---

# Inference 

Run:

```bash
python inference.py
```
Requirements:

* `HF_TOKEN`
* `API_BASE_URL`
* `MODEL_NAME`

Logs follow required format:

```
[START]
[STEP]
[END]
```

---

# OpenEnv Compliance

✔ Typed models (Pydantic)
✔ step / reset / state implemented
✔ openenv.yaml included
✔ Deterministic graders
✔ Reproducible baseline

---

# Summary

CloudSec-Sim is:

* Realistic
* Multi-step
* Reward-shaped
* Reproducible

Built to evaluate the next generation of **autonomous cybersecurity agents**.
