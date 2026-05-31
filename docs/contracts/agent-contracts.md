# Agent Contracts

Dashboard Studio agents use shared Pydantic contracts from the `contracts/` package.
These contracts are the common language between LLM agents, deterministic validators,
artifact writers, notebooks, and the FastAPI artifact layer.

Contract layer version: `0.1.0`

## Handoffs

| Contract | Producer | Consumers | Artifact | JSON Schema |
| --- | --- | --- | --- | --- |
| `SemanticUnderstanding` | Semantic understanding agent | Metric planner, dashboard planner, critic, analytical brain | `artifacts/semantic/*_semantic.json` | `docs/contracts/schemas/semantic-understanding.schema.json` |
| `PandasMetricPlan` | Metric code planner | Sandbox executor, dashboard planner, validator, critic, notebook, analytical brain | `artifacts/metric_plans/*_metric_plan.json` | `docs/contracts/schemas/pandas-metric-plan.schema.json` |
| Serialized analysis outputs | Sandbox executor | Frontend renderer, notebook, analytical brain compaction | `artifacts/analysis_outputs/*_analysis_outputs.json` | Not formalized yet |
| `DashboardPlan` | Dashboard planner or critic | Streamlit renderer, frontend artifact API, validator, notebook, analytical brain | `artifacts/dashboard/*_dashboard.json` | `docs/contracts/schemas/dashboard-plan.schema.json` |
| `DashboardValidationReport` | Deterministic validator | Dashboard critic, Streamlit renderer, frontend artifact API, notebook, analytical brain | `artifacts/dashboard/*_dashboard_validation.json` | `docs/contracts/schemas/dashboard-validation-report.schema.json` |
| `DashboardCritique` | Dashboard critic | Streamlit renderer, artifact API, notebook | `artifacts/critiques/*_dashboard_critique.json` | `docs/contracts/schemas/dashboard-critique.schema.json` |
| `AnalyticalBrainInput` | Pipeline orchestration | Analytical brain agent | In-memory handoff | `docs/contracts/schemas/analytical-brain-input.schema.json` |
| `AnalyticalBrainResult` | Analytical brain agent | Streamlit renderer, frontend artifact API, notebook | `artifacts/insights/*_analytical_insights.json` | `docs/contracts/schemas/analytical-brain-result.schema.json` |

## Rules

- The `contracts/` package owns shared model definitions.
- Agent modules may re-export contract models for backward compatibility.
- Prompt builders, LLM calls, rendering, execution, and validation logic stay outside the contract layer.
- Existing artifact payload shapes are preserved in this version.
- Version metadata is exposed through schema ids and `x-contract-layer-version`; existing artifacts are not wrapped or migrated.

## Exporting Schemas

Run:

```powershell
.\.venv\Scripts\python.exe scripts\export_contract_schemas.py
```

The command writes JSON Schemas to:

```text
docs/contracts/schemas/
```
