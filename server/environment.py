from models import Observation, Action
import random
from datetime import datetime
        

class CloudSecEngine:
    def __init__(self):
        self.max_steps = 10
        self.reset()

    def reset(self, difficulty="easy"):
        self.current_difficulty = difficulty.lower()
        self.scenario = random.choice([
            "brute_force",
            "data_exposure",
            "misconfig",
            "normal"
        ])
        self.step_count = 0
        self.reward_history = []
        self.action_history = []

        if self.current_difficulty == "easy":
            self.state = {
                "s3_public": True,
                "s3_encryption": False,
                "iam_key_age": 0,
                "iam_mfa_enabled": True,
                "sg_port_22": "closed",
                "sg_port_80": "closed",
                "rds_public": False
            }

        elif self.current_difficulty == "medium":
            self.state = {
                "s3_public": random.choice([True, False]),
                "s3_encryption": random.choice([False, True]),
                "iam_key_age": random.randint(0, 150),  
                "iam_mfa_enabled": random.choice([False, True]),
                "sg_port_22": random.choice(["open", "closed"]),
                "sg_port_80": random.choice(["open", "closed"]),
                "rds_public": random.choice([True, False])
            }

        else:
            self.state = {
                "s3_public": random.choice([True, False]),
                "s3_encryption": random.choice([False, True]),
                "iam_key_age": random.randint(0, 200),
                "iam_mfa_enabled": random.choice([False, True]),
                "sg_port_22": random.choice(["open", "closed"]),
                "sg_port_80": random.choice(["open", "closed"]),
                "rds_public": random.choice([True, False])
            }
        self.hidden = {
                "attack_detected": random.choice([True, False]),
                "risk_score": random.randint(1, 10)
            }    
        self.timeline = []
        self.time_step = 0
        self.investigated = False
        self.checked_ip = False
        self.quarantined = False
        self.escalated = False
        self.ip_reputation = None
        
        self.timeline = []
        self.time_step = 0

        return self._get_obs()
                
    def _generate_logs(self):

    
        def ts():
            return datetime.utcnow().isoformat() + "Z"
    
        def ip():
            return ".".join(str(random.randint(1, 255)) for _ in range(4))
    
        logs = []
    
        for event in self.timeline:
            logs.append({
                "timestamp": ts(),
                "event": "attack_progression",
                "ip": ip(),
                "severity": "HIGH",
                "message": event
            })
    
        if self.state["sg_port_22"] == "open":
            logs.append({
                "timestamp": ts(),
                "event": "ssh_failed",
                "ip": ip(),
                "severity": "HIGH",
                "message": "Failed SSH login"
            })
    
        if self.state["rds_public"]:
            logs.append({
                "timestamp": ts(),
                "event": "db_access",
                "ip": ip(),
                "severity": "CRITICAL",
                "message": "External DB access"
            })
            
        noise = ["backup_done", "heartbeat_ok", "lambda_exec"]
        for n in random.sample(noise, 2):
            logs.append({
                "timestamp": ts(),
                "event": n,
                "ip": ip(),
                "severity": "LOW",
                "message": "Normal activity"
            })
    
        return logs
    
    def _get_obs(self):
        return Observation(
            resources=[{"id": k, "value": v} for k, v in self.state.items()],
            instruction=f"[{self.current_difficulty.upper()}] Fix security issues",
            alerts=self._generate_alerts(),  
            logs=self._generate_logs()       
        )
    def step(self, action: Action):
        self.step_count += 1
        self._progress_attack()
        a = action.action_type
        r = action.resource_id

        self.action_history.append(a)

        if a == "restrict_s3":
            self.state["s3_public"] = False
        elif a == "enable_encryption":
            self.state["s3_encryption"] = True
        elif a == "rotate_key":
            self.state["iam_key_age"] = 0
        elif a == "enable_mfa":
            self.state["iam_mfa_enabled"] = True
        elif a == "close_port_22":
            self.state["sg_port_22"] = "closed"
        elif a == "close_port_80":
            self.state["sg_port_80"] = "closed"
        elif a == "secure_rds":
            self.state["rds_public"] = False
        elif a == "read_logs":
            self.investigated = True
        
        elif a == "check_ip_reputation":
            self.ip_reputation = random.choice(["malicious", "suspicious", "clean"])
            self.checked_ip = True
        
        elif a == "quarantine_host":
            self.state["sg_port_22"] = "closed"
            self.state["sg_port_80"] = "closed"
            self.quarantined = True
        
        elif a == "escalate_incident":
            self.escalated = True

        base_score = self._calculate_score()

        if self.current_difficulty == "easy":
            score = base_score
        else:
            penalty = -0.05 * self.step_count
            score = base_score + penalty
        
        score = max(0.0, min(1.0, score))

        self.reward_history.append({"value": score})

        done = score >= 1.0 or self.step_count >= self.max_steps

        return self._get_obs(), score, done, {}

    def _calculate_score(self):
        score = 0

        if self.current_difficulty == "easy":   
            if not self.state["s3_public"]:
                return 1.0  
        
            return 0.0

        elif self.current_difficulty == "medium":
            if self.state["iam_key_age"] == 0:
                score += 0.4
            if self.state["iam_mfa_enabled"]:
                score += 0.4

            return min(score, 1.0)

        elif self.current_difficulty == "hard":
            score = 0
        
            if self.step_count > 0:
                score += 0.2
        
            if self.investigated:
                score += 0.2
        
            if self.checked_ip:
                score += 0.2
        
            if self.quarantined:
                score += 0.2
        
            if self.escalated:
                score += 0.2
        
            if self.state["sg_port_22"] == "closed":
                score += 0.1
        
            return min(score, 1.0)

        return 0.0

    def _progress_attack(self):
        self.time_step += 1
    
        if self.scenario == "brute_force":
            if self.time_step >= 2:
                self.timeline.append("Multiple failed SSH attempts")
            if self.time_step >= 3:
                self.timeline.append("Account compromise suspected")
    
        elif self.scenario == "data_exposure":
            if self.time_step >= 2:
                self.timeline.append("Large data download detected")
            if self.time_step >= 3:
                self.timeline.append("Data exfiltration detected")
        
    def _generate_alerts(self):
        scenario = getattr(self, "scenario", "normal")
        alerts = []

        if self.state.get("s3_public"):
            alerts.append({
                "id": "ALERT-S3",
                "severity": "CRITICAL", 
                "mitre": "T1530",
                "desc": "S3 Bucket is Publicly Accessible",
                "actions": ["restrict_s3"]
            })
    
        if scenario == "brute_force":
            alerts.append({
                "id": "ALERT-SSH",
                "severity": "HIGH",
                "mitre": "T1110",
                "desc": "Brute force detected",
                "actions": ["check_ip_reputation", "quarantine_host"]
            })
        
        return alerts if alerts else [{"id": "INFO", "severity": "LOW", "desc": "No threat"}]
            
    def get_state(self):
        return {
            "state": self.state,
            "step_count": self.step_count,
            "difficulty": self.current_difficulty
        }


env = CloudSecEngine()
