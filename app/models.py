 
from pydantic import BaseModel
from typing import List, Optional


class UserRequest(BaseModel):
    user_goal: str
    content: str


class SandboxedFacts(BaseModel):
    extracted_facts: List[str]
    suspicious_patterns: List[str]
    raw_summary: str


class ActionPlan(BaseModel):
    proposed_action: str
    target_resource: Optional[str] = None
    justification: str
    required_tool: Optional[str] = None


class SecurityDecision(BaseModel):
    allowed: bool
    reason: str
    risk_score: float
