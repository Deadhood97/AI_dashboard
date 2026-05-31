from __future__ import annotations

import os
from typing import Literal


DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_LLM_TIMEOUT_SECONDS = 90.0
DEFAULT_LLM_MAX_RETRIES = 1

AgentRole = Literal[
    "semantic",
    "metric_code",
    "metric_repair",
    "dashboard",
    "dashboard_critic",
    "insights",
]

ROLE_MODEL_ENV_VARS: dict[AgentRole, str] = {
    "semantic": "OPENAI_SEMANTIC_MODEL",
    "metric_code": "OPENAI_METRIC_CODE_MODEL",
    "metric_repair": "OPENAI_METRIC_REPAIR_MODEL",
    "dashboard": "OPENAI_DASHBOARD_MODEL",
    "dashboard_critic": "OPENAI_DASHBOARD_CRITIC_MODEL",
    "insights": "OPENAI_INSIGHTS_MODEL",
}


def model_for_role(role: AgentRole, explicit_model: str | None = None) -> str:
    if explicit_model:
        return explicit_model
    role_model = os.getenv(ROLE_MODEL_ENV_VARS[role], "").strip()
    if role_model:
        return role_model
    shared_model = os.getenv("OPENAI_MODEL", "").strip()
    if shared_model:
        return shared_model
    return DEFAULT_MODEL


def resolve_llm_timeout() -> float:
    raw_value = os.getenv("OPENAI_TIMEOUT_SECONDS", "").strip()
    if not raw_value:
        return DEFAULT_LLM_TIMEOUT_SECONDS
    try:
        value = float(raw_value)
    except ValueError:
        return DEFAULT_LLM_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_LLM_TIMEOUT_SECONDS


def resolve_llm_max_retries() -> int:
    raw_value = os.getenv("OPENAI_MAX_RETRIES", "").strip()
    if not raw_value:
        return DEFAULT_LLM_MAX_RETRIES
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_LLM_MAX_RETRIES
    return max(value, 0)
