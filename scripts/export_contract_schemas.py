from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Type

from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contracts import (
    AnalyticalBrainInput,
    AnalyticalBrainResult,
    CONTRACT_LAYER_VERSION,
    CONTRACT_SCHEMA_IDS,
    DashboardCritique,
    DashboardPlan,
    DashboardValidationReport,
    PandasMetricPlan,
    SemanticUnderstanding,
)


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "contracts" / "schemas"

SCHEMA_MODELS: dict[str, Type[BaseModel]] = {
    "semantic-understanding": SemanticUnderstanding,
    "pandas-metric-plan": PandasMetricPlan,
    "dashboard-plan": DashboardPlan,
    "dashboard-validation-report": DashboardValidationReport,
    "dashboard-critique": DashboardCritique,
    "analytical-brain-input": AnalyticalBrainInput,
    "analytical-brain-result": AnalyticalBrainResult,
}

SCHEMA_KEYS = {
    "semantic-understanding": "semantic_understanding",
    "pandas-metric-plan": "pandas_metric_plan",
    "dashboard-plan": "dashboard_plan",
    "dashboard-validation-report": "dashboard_validation_report",
    "dashboard-critique": "dashboard_critique",
    "analytical-brain-input": "analytical_brain_input",
    "analytical-brain-result": "analytical_brain_result",
}


def schema_for(name: str, model: Type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
    schema["$id"] = CONTRACT_SCHEMA_IDS[SCHEMA_KEYS[name]]
    schema["x-contract-layer-version"] = CONTRACT_LAYER_VERSION
    return schema


def export_contract_schemas(output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in SCHEMA_MODELS.items():
        path = output_dir / f"{name}.schema.json"
        path.write_text(
            json.dumps(schema_for(name, model), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Dashboard Studio contract JSON Schemas.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where schema JSON files should be written.",
    )
    args = parser.parse_args()

    for path in export_contract_schemas(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
