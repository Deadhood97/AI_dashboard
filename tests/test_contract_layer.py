import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from contracts import (
    CONTRACT_LAYER_VERSION,
    CONTRACT_SCHEMA_IDS,
    AnalyticalBrainResult,
    DashboardCritique,
    DashboardPlan,
    DashboardValidationReport,
    PandasMetricPlan,
    SemanticUnderstanding,
)
from contracts.insights import AnalyticalBrainInput
from contracts.base import validate_contract
from scripts.export_contract_schemas import export_contract_schemas
from tests.test_agents_contracts import (
    sample_dashboard_plan,
    sample_insights,
    sample_metric_plan,
    sample_semantic,
    sample_validation_report,
)


class ContractLayerTests(unittest.TestCase):
    def test_contract_package_import_does_not_import_langchain_clients(self):
        code = (
            "import sys; import contracts; "
            "blocked = [name for name in sys.modules "
            "if name.startswith('langchain_openai') or name.startswith('langchain_core')]; "
            "assert not blocked, blocked"
        )
        subprocess.run([sys.executable, "-c", code], check=True)

    def test_existing_agent_import_paths_reexport_contract_models(self):
        from agents.analytical_brain import AnalyticalBrainResult as AgentInsights
        from agents.dashboard_critic import DashboardCritique as AgentCritique
        from agents.dashboard_planner import DashboardPlan as AgentDashboardPlan
        from agents.metric_code_planner import PandasMetricPlan as AgentMetricPlan
        from agents.semantic_understanding import SemanticUnderstanding as AgentSemantic
        from dashboard_validation import DashboardValidationReport as ValidatorReport

        self.assertIs(AgentSemantic, SemanticUnderstanding)
        self.assertIs(AgentMetricPlan, PandasMetricPlan)
        self.assertIs(AgentDashboardPlan, DashboardPlan)
        self.assertIs(ValidatorReport, DashboardValidationReport)
        self.assertIs(AgentCritique, DashboardCritique)
        self.assertIs(AgentInsights, AnalyticalBrainResult)

    def test_sample_payloads_validate_through_contract_models(self):
        semantic = SemanticUnderstanding.model_validate(sample_semantic().model_dump())
        metric_plan = PandasMetricPlan.model_validate(sample_metric_plan().model_dump())
        dashboard_plan = DashboardPlan.model_validate(sample_dashboard_plan().model_dump())
        validation_report = DashboardValidationReport.model_validate(
            sample_validation_report().model_dump()
        )
        critique = DashboardCritique.model_validate(
            {
                "critique_summary": "Repair summary.",
                "repaired_dashboard_plan": dashboard_plan.model_dump(),
                "repair_notes": ["Changed chart scale."],
                "remaining_risks": ["Small differences need context."],
            }
        )
        insights = AnalyticalBrainResult.model_validate(sample_insights().model_dump())

        analytical_input = AnalyticalBrainInput.model_validate(
            {
                "metadata": {"source_file": "athletes.csv"},
                "semantic_understanding": semantic.model_dump(),
                "metric_plan": metric_plan.model_dump(),
                "analysis_outputs": {"fatigue_by_intensity": [{"Fatigue_Score": 62.1}]},
                "dashboard_plan": dashboard_plan.model_dump(),
                "validation_report": validation_report.model_dump(),
                "df_context": "dataframe context",
            }
        )

        self.assertEqual(critique.repaired_dashboard_plan.dashboard_title, dashboard_plan.dashboard_title)
        self.assertEqual(insights.narrative_title, "Training Load Signals")
        self.assertEqual(analytical_input.semantic_understanding.dataset_domain, semantic.dataset_domain)

    def test_validate_contract_normalizes_raw_payloads_to_model_instances(self):
        semantic = validate_contract(SemanticUnderstanding, sample_semantic().model_dump())

        self.assertIsInstance(semantic, SemanticUnderstanding)
        self.assertEqual(semantic.dataset_domain, "Athlete performance")

    def test_export_contract_schemas_writes_versioned_schema_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            written = export_contract_schemas(Path(temp_dir))

            self.assertEqual(len(written), 7)
            semantic_schema = json.loads(
                (Path(temp_dir) / "semantic-understanding.schema.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(semantic_schema["$id"], CONTRACT_SCHEMA_IDS["semantic_understanding"])
        self.assertEqual(semantic_schema["x-contract-layer-version"], CONTRACT_LAYER_VERSION)
        self.assertEqual(semantic_schema["title"], "SemanticUnderstanding")


if __name__ == "__main__":
    unittest.main()
