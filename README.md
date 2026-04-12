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

The grader applies a base weight to the environmental reward and penalizes the agent based on step count and task complexity.

General Formula:

final_score = (env_reward × base_weight) - (steps × penalty_factor)
---
1. Easy (S3 Fix)
Base Weight: 0.90

Step Penalty: 0.02 per step

Target Range: 0.80 – 0.99

Focus: Verifies the agent can perform a single-step remediation (Restricting S3 access).
---
2. Medium (IAM Hardening)
Base Weight: 0.70

Step Penalty: 0.04 per step

Target Range: 0.60 – 0.72

Focus: Rewards the correct sequencing of IAM key rotation and MFA enforcement.
---
3. Hard (SOC Sequence)
Base Weight: 0.50

Step Penalty: 0.06 per step

Target Range: 0.30 – 0.52

Focus: Protocol compliance. The agent is heavily penalized for skipping "Investigation" and "Analysis" phases (Log reading/IP checks) before responding to the threat.
---
Step-Level Rewards (Environment)
These are the raw values emitted by the environment before the Grader applies difficulty scaling:

Easy: +1.0 for securing the S3 bucket.

Medium: +0.5 for Key Rotation | +0.5 for MFA Enablement.

Hard: Cumulative rewards (+0.2 each) for: Logs Read → IP Checked → Host Quarantined → Incident Escalated.
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
