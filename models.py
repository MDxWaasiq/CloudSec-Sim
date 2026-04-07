from pydantic import BaseModel
from typing import List, Dict, Any, Literal

class Observation(BaseModel):
    resources: List[Dict[str, Any]]
    instruction: str

    alerts: List[Dict[str, Any]] = []

    logs: List[Dict[str, Any]] = []

class Action(BaseModel):
    action_type: Literal[
        "restrict_s3",
        "enable_encryption",
        "rotate_key",
        "enable_mfa",
        "close_port_22",
        "close_port_80",
        "secure_rds",
        "read_logs",
        "check_ip_reputation",
        "quarantine_host",
        "escalate_incident"
    ]
    resource_id: str

class State(BaseModel):
    internal_status: Dict[str, str]
    step_count: int