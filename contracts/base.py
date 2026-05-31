from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


CONTRACT_LAYER_VERSION = "0.1.0"
SCHEMA_ID_BASE = "https://dashboard-studio.local/contracts"

CONTRACT_SCHEMA_IDS = {
    "contract_artifact_envelope": f"{SCHEMA_ID_BASE}/contract-artifact-envelope.schema.json",
    "semantic_understanding": f"{SCHEMA_ID_BASE}/semantic-understanding.schema.json",
    "pandas_metric_plan": f"{SCHEMA_ID_BASE}/pandas-metric-plan.schema.json",
    "dashboard_plan": f"{SCHEMA_ID_BASE}/dashboard-plan.schema.json",
    "dashboard_critique": f"{SCHEMA_ID_BASE}/dashboard-critique.schema.json",
    "dashboard_validation_report": f"{SCHEMA_ID_BASE}/dashboard-validation-report.schema.json",
    "analytical_brain_input": f"{SCHEMA_ID_BASE}/analytical-brain-input.schema.json",
    "analytical_brain_result": f"{SCHEMA_ID_BASE}/analytical-brain-result.schema.json",
}


def schema_extra(schema_key: str) -> ConfigDict:
    return ConfigDict(
        json_schema_extra={
            "$id": CONTRACT_SCHEMA_IDS[schema_key],
            "x-contract-layer-version": CONTRACT_LAYER_VERSION,
        }
    )


PayloadT = TypeVar("PayloadT")
ModelT = TypeVar("ModelT", bound=BaseModel)


def validate_contract(model_type: type[ModelT], payload: Any) -> ModelT:
    """Validate an agent handoff against its canonical Pydantic contract."""
    return model_type.model_validate(payload)


class ContractArtifactEnvelope(BaseModel, Generic[PayloadT]):
    """Optional wrapper for future artifact metadata without changing v1 payloads."""

    model_config = schema_extra("contract_artifact_envelope")

    contract_name: str = Field(description="Stable contract key for the wrapped payload.")
    contract_version: str = Field(default=CONTRACT_LAYER_VERSION)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp for when the envelope was created.",
    )
    payload: PayloadT = Field(description="Contract payload.")
    metadata: dict[str, Any] = Field(default_factory=dict)
