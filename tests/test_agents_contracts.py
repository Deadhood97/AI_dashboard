import unittest
from unittest.mock import patch

import pandas as pd
from langchain_core.runnables import RunnableLambda

import agents.analytical_brain as analytical_agent
import agents.dashboard_critic as critic_agent
import agents.dashboard_planner as dashboard_agent
import agents.metric_code_planner as metric_agent
import agents.semantic_understanding as semantic_agent
from agents.analytical_brain import (
    AnalyticalBrainResult,
    DashboardInsight,
    build_analytical_brain_input,
)
from agents.dashboard_critic import DashboardCritique
from agents.dashboard_planner import (
    DashboardChartSpec,
    DashboardKpiSpec,
    DashboardPlan,
    DashboardQuestionView,
)
from agents.metric_code_planner import (
    AnalysisOutputSpec,
    DashboardMetricSpec,
    PandasMetricPlan,
    QuestionAnalysisSpec,
)
from agents.semantic_understanding import SemanticUnderstanding
from dashboard_validation import DashboardValidationReport, ValidationIssue


class FakeChain:
    def __init__(self, result):
        self.result = result
        self.payload = None

    def invoke(self, payload):
        self.payload = payload
        return self.result


class FakeLLM:
    instances = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.__class__.instances.append(self)

    def with_structured_output(self, schema):
        return RunnableLambda(lambda payload: schema)


def sample_semantic() -> SemanticUnderstanding:
    return SemanticUnderstanding(
        dataset_domain="Athlete performance",
        primary_entities=["Athlete"],
        important_dimensions=["Training_Intensity", "Gender"],
        important_metrics=["Fatigue_Score", "Performance_Score"],
        analytical_goals=["Compare fatigue and performance by training intensity"],
        suggested_questions=["How does training intensity affect fatigue?"],
    )


def sample_metric_plan() -> PandasMetricPlan:
    return PandasMetricPlan(
        agent_summary="Compute athlete performance summaries.",
        required_columns=["Training_Intensity", "Fatigue_Score", "Performance_Score"],
        dashboard_metrics=[
            DashboardMetricSpec(
                name="Average Fatigue",
                business_purpose="Track fatigue by training intensity.",
                calculation="Mean Fatigue_Score by Training_Intensity.",
                output_key="fatigue_by_intensity",
                required_columns=["Training_Intensity", "Fatigue_Score"],
                missing_data_strategy="Drop rows missing either field.",
            )
        ],
        question_analyses=[
            QuestionAnalysisSpec(
                question="How does training intensity affect fatigue?",
                analysis_strategy="Group by intensity and average fatigue.",
                output_key="fatigue_by_intensity",
                required_columns=["Training_Intensity", "Fatigue_Score"],
                missing_data_strategy="Drop rows missing either field.",
            )
        ],
        analysis_outputs=[
            AnalysisOutputSpec(
                key="fatigue_by_intensity",
                output_type="dataframe",
                semantic_role="categorical_comparison",
                columns=["Training_Intensity", "Fatigue_Score"],
                recommended_views=["bar_chart", "table"],
                description="Average fatigue by training intensity.",
                render_hint="Bar chart with intensity on x and fatigue on y.",
            )
        ],
        pandas_code=(
            "analysis_outputs = {}\n"
            "analysis_outputs['fatigue_by_intensity'] = "
            "df.groupby('Training_Intensity')[['Fatigue_Score']].mean().reset_index()\n"
        ),
        assumptions=["Training intensity labels are consistent."],
        limitations=["No causal inference."],
    )


def sample_dashboard_plan() -> DashboardPlan:
    chart = DashboardChartSpec(
        title="Fatigue by Intensity",
        chart_type="bar",
        source_output_key="fatigue_by_intensity",
        x="Training_Intensity",
        y="Fatigue_Score",
        rationale="Compares fatigue across intensity groups.",
    )
    return DashboardPlan(
        dashboard_title="Athlete Training Dashboard",
        dashboard_summary="Summarizes fatigue and performance patterns.",
        data_integrity_notes=["Uses available non-null rows per metric."],
        kpis=[
            DashboardKpiSpec(
                title="Average Fatigue",
                source_output_key="fatigue_by_intensity",
                value_column="Fatigue_Score",
                aggregation="mean",
                rationale="Headline fatigue indicator.",
            )
        ],
        overview_charts=[chart],
        question_views=[
            DashboardQuestionView(
                question="How does training intensity affect fatigue?",
                answer_strategy="Compare grouped means.",
                chart=chart,
            )
        ],
        assumptions=["Grouped averages are comparable."],
        limitations=["Small groups may need sample-size review."],
    )


def sample_validation_report() -> DashboardValidationReport:
    return DashboardValidationReport(
        status="failed",
        issues=[
            ValidationIssue(
                severity="error",
                component="chart",
                item_title="Fatigue by Intensity",
                source_output_key="fatigue_by_intensity",
                message="Bar values are tightly clustered.",
                suggested_fix="Declare scale fields and a scale note.",
            )
        ],
        rejected_chart_titles=["Fatigue by Intensity"],
        rejected_kpi_titles=[],
    )


def sample_insights() -> AnalyticalBrainResult:
    return AnalyticalBrainResult(
        narrative_title="Training Load Signals",
        executive_summary="Fatigue differs modestly across intensity groups.",
        key_insights=[
            DashboardInsight(
                headline="Fatigue is slightly higher at intense loads",
                explanation="The grouped output shows a higher average fatigue score.",
                evidence=["fatigue_by_intensity"],
                business_implication="Coaches may need closer recovery monitoring.",
                recommended_action="Review recovery days for high-intensity athletes.",
                confidence="medium",
                impact="medium",
                related_dashboard_items=["Fatigue by Intensity"],
            )
        ],
        watchouts=["Correlation does not imply causation."],
        follow_up_questions=["Do recovery days offset fatigue?"],
    )


class AgentContractTests(unittest.TestCase):
    def test_all_agent_chain_builders_construct_without_network(self):
        modules_and_builders = [
            (semantic_agent, semantic_agent.build_semantic_understanding_chain),
            (metric_agent, metric_agent.build_metric_code_planner_chain),
            (dashboard_agent, dashboard_agent.build_dashboard_planner_chain),
            (critic_agent, critic_agent.build_dashboard_critic_chain),
            (analytical_agent, analytical_agent.build_analytical_brain_chain),
        ]

        for module, builder in modules_and_builders:
            with self.subTest(module=module.__name__):
                with patch.object(module, "resolve_openai_api_key", return_value="test-key"):
                    with patch.object(module, "ChatOpenAI", FakeLLM):
                        self.assertIsNotNone(builder(model="test-model"))

    def test_agent_llm_clients_use_timeout_and_retry_bounds(self):
        modules_and_builders = [
            (semantic_agent, semantic_agent.build_semantic_understanding_chain),
            (metric_agent, metric_agent.build_metric_code_planner_chain),
            (dashboard_agent, dashboard_agent.build_dashboard_planner_chain),
            (critic_agent, critic_agent.build_dashboard_critic_chain),
            (analytical_agent, analytical_agent.build_analytical_brain_chain),
        ]

        for module, builder in modules_and_builders:
            with self.subTest(module=module.__name__):
                FakeLLM.instances = []
                with patch.object(module, "resolve_openai_api_key", return_value="test-key"):
                    with patch.object(module, "ChatOpenAI", FakeLLM):
                        builder(model="test-model")

                self.assertEqual(len(FakeLLM.instances), 1)
                llm = FakeLLM.instances[0]
                self.assertEqual(llm.kwargs["timeout"], semantic_agent.DEFAULT_LLM_TIMEOUT_SECONDS)
                self.assertEqual(llm.kwargs["max_retries"], semantic_agent.DEFAULT_LLM_MAX_RETRIES)

    def test_agent_chain_builders_use_role_specific_models(self):
        cases = [
            (semantic_agent, semantic_agent.build_semantic_understanding_chain, "OPENAI_SEMANTIC_MODEL", "semantic-model"),
            (metric_agent, metric_agent.build_metric_code_planner_chain, "OPENAI_METRIC_CODE_MODEL", "metric-code-model"),
            (dashboard_agent, dashboard_agent.build_dashboard_planner_chain, "OPENAI_DASHBOARD_MODEL", "dashboard-model"),
            (critic_agent, critic_agent.build_dashboard_critic_chain, "OPENAI_DASHBOARD_CRITIC_MODEL", "critic-model"),
            (analytical_agent, analytical_agent.build_analytical_brain_chain, "OPENAI_INSIGHTS_MODEL", "insights-model"),
        ]

        for module, builder, env_var, expected_model in cases:
            with self.subTest(module=module.__name__):
                FakeLLM.instances = []
                with patch.dict("os.environ", {env_var: expected_model}, clear=False):
                    with patch.object(module, "resolve_openai_api_key", return_value="test-key"):
                        with patch.object(module, "ChatOpenAI", FakeLLM):
                            builder()

                self.assertEqual(FakeLLM.instances[0].kwargs["model"], expected_model)

    def test_metric_repair_agent_uses_repair_model(self):
        class RepairFakeLLM(FakeLLM):
            def with_structured_output(self, schema):
                return RunnableLambda(lambda payload: sample_metric_plan())

        RepairFakeLLM.instances = []
        failed_plan = sample_metric_plan()
        with patch.dict("os.environ", {"OPENAI_METRIC_REPAIR_MODEL": "metric-repair-model"}, clear=False):
            with patch.object(metric_agent, "resolve_openai_api_key", return_value="test-key"):
                with patch.object(metric_agent, "ChatOpenAI", RepairFakeLLM):
                    chain = metric_agent.repair_metric_code_plan(
                        failed_plan=failed_plan,
                        semantic_understanding=sample_semantic(),
                        df_head="context",
                        error_message="broken",
                    )

        self.assertIsInstance(chain, PandasMetricPlan)
        self.assertEqual(RepairFakeLLM.instances[0].kwargs["model"], "metric-repair-model")

    def test_semantic_agent_invokes_chain_with_metadata_json_and_dataframe_context(self):
        result = sample_semantic()
        fake_chain = FakeChain(result)

        with patch.object(
            semantic_agent,
            "build_semantic_understanding_chain",
            return_value=fake_chain,
        ):
            actual = semantic_agent.generate_semantic_understanding(
                metadata={"source_file": "athletes.csv", "row_count": 10},
                df_head="| Training_Intensity | Fatigue_Score |",
            )

        self.assertEqual(actual, result)
        self.assertIn('"source_file"', fake_chain.payload["metadata_json"])
        self.assertEqual(
            fake_chain.payload["df_head"],
            "| Training_Intensity | Fatigue_Score |",
        )

    def test_agent_outputs_are_validated_from_raw_payloads(self):
        cases = [
            (
                semantic_agent,
                "build_semantic_understanding_chain",
                semantic_agent.generate_semantic_understanding,
                sample_semantic().model_dump(),
                {"metadata": {"source_file": "athletes.csv"}, "df_head": "context"},
                SemanticUnderstanding,
            ),
            (
                metric_agent,
                "build_metric_code_planner_chain",
                metric_agent.generate_metric_code_plan,
                sample_metric_plan().model_dump(),
                {"semantic_understanding": sample_semantic().model_dump(), "df_head": "context"},
                PandasMetricPlan,
            ),
            (
                dashboard_agent,
                "build_dashboard_planner_chain",
                dashboard_agent.generate_dashboard_plan,
                sample_dashboard_plan().model_dump(),
                {
                    "metadata": {"source_file": "athletes.csv"},
                    "semantic_understanding": sample_semantic().model_dump(),
                    "metric_plan": sample_metric_plan().model_dump(),
                    "df_head": "context",
                },
                DashboardPlan,
            ),
        ]

        for module, builder_name, generate, payload, kwargs, expected_type in cases:
            with self.subTest(module=module.__name__):
                with patch.object(module, builder_name, return_value=FakeChain(payload)):
                    if module is dashboard_agent:
                        with patch.object(module, "load_dashboard_design_guide", return_value="guide"):
                            actual = generate(**kwargs)
                    else:
                        actual = generate(**kwargs)
                self.assertIsInstance(actual, expected_type)

    def test_metric_agent_invokes_chain_with_structured_semantic_json(self):
        result = sample_metric_plan()
        fake_chain = FakeChain(result)

        with patch.object(
            metric_agent,
            "build_metric_code_planner_chain",
            return_value=fake_chain,
        ):
            actual = metric_agent.generate_metric_code_plan(
                semantic_understanding=sample_semantic(),
                df_head="dataframe context",
            )

        self.assertEqual(actual, result)
        self.assertIn('"dataset_domain"', fake_chain.payload["semantic_json"])
        self.assertEqual(fake_chain.payload["df_head"], "dataframe context")

    def test_dashboard_agent_invokes_chain_with_metric_plan_and_design_guide(self):
        result = sample_dashboard_plan()
        fake_chain = FakeChain(result)

        with patch.object(dashboard_agent, "build_dashboard_planner_chain", return_value=fake_chain):
            with patch.object(dashboard_agent, "load_dashboard_design_guide", return_value="guide"):
                actual = dashboard_agent.generate_dashboard_plan(
                    metadata={"source_file": "athletes.csv"},
                    semantic_understanding=sample_semantic(),
                    metric_plan=sample_metric_plan(),
                    df_head="dataframe context",
                )

        self.assertEqual(actual, result)
        self.assertIn('"source_file"', fake_chain.payload["metadata_json"])
        self.assertIn('"analysis_outputs"', fake_chain.payload["metric_plan_json"])
        self.assertEqual(fake_chain.payload["dashboard_design_guide"], "guide")

    def test_critic_agent_invokes_chain_with_compacted_analysis_outputs(self):
        repaired = sample_dashboard_plan()
        result = DashboardCritique(
            critique_summary="Added scale disclosure.",
            repaired_dashboard_plan=repaired,
            repair_notes=["Set value axis fields."],
            remaining_risks=["Small differences need careful interpretation."],
        )
        fake_chain = FakeChain(result)

        with patch.object(critic_agent, "build_dashboard_critic_chain", return_value=fake_chain):
            with patch.object(critic_agent, "load_dashboard_design_guide", return_value="guide"):
                actual = critic_agent.repair_dashboard_plan(
                    metadata={"source_file": "athletes.csv"},
                    semantic_understanding=sample_semantic(),
                    metric_plan=sample_metric_plan(),
                    analysis_outputs={
                        "fatigue_by_intensity": pd.DataFrame(
                            {
                                "Training_Intensity": ["High", "Low"],
                                "Fatigue_Score": [62.1, 61.8],
                            }
                        ),
                        "missing_counts": pd.Series([0, 1], index=["Age", "Gender"]),
                    },
                    dashboard_plan=sample_dashboard_plan(),
                    validation_report=sample_validation_report(),
                    df_context="dataframe context",
                )

        self.assertEqual(actual, result)
        self.assertIn('"type": "Series"', fake_chain.payload["analysis_outputs_json"])
        self.assertIn("validation_report_json", fake_chain.payload)

    def test_critic_output_is_validated_from_raw_payload(self):
        payload = {
            "critique_summary": "Added scale disclosure.",
            "repaired_dashboard_plan": sample_dashboard_plan().model_dump(),
            "repair_notes": ["Set value axis fields."],
            "remaining_risks": ["Small differences need careful interpretation."],
        }

        with patch.object(critic_agent, "build_dashboard_critic_chain", return_value=FakeChain(payload)):
            with patch.object(critic_agent, "load_dashboard_design_guide", return_value="guide"):
                actual = critic_agent.repair_dashboard_plan(
                    metadata={"source_file": "athletes.csv"},
                    semantic_understanding=sample_semantic().model_dump(),
                    metric_plan=sample_metric_plan().model_dump(),
                    analysis_outputs={"fatigue_by_intensity": pd.DataFrame({"Fatigue_Score": [1]})},
                    dashboard_plan=sample_dashboard_plan().model_dump(),
                    validation_report=sample_validation_report().model_dump(),
                    df_context="dataframe context",
                )

        self.assertIsInstance(actual, DashboardCritique)
        self.assertIsInstance(actual.repaired_dashboard_plan, DashboardPlan)

    def test_critic_repaired_chart_null_defaults_are_normalized(self):
        repaired_plan = sample_dashboard_plan().model_dump()
        repaired_plan["question_views"][0]["chart"]["orientation"] = None
        repaired_plan["question_views"][0]["chart"]["sort_order"] = None
        repaired_plan["question_views"][0]["chart"]["metrics"] = None
        payload = {
            "critique_summary": "Normalized defaults.",
            "repaired_dashboard_plan": repaired_plan,
            "repair_notes": ["Left optional chart defaults unset."],
            "remaining_risks": [],
        }

        with patch.object(critic_agent, "build_dashboard_critic_chain", return_value=FakeChain(payload)):
            with patch.object(critic_agent, "load_dashboard_design_guide", return_value="guide"):
                actual = critic_agent.repair_dashboard_plan(
                    metadata={"source_file": "athletes.csv"},
                    semantic_understanding=sample_semantic(),
                    metric_plan=sample_metric_plan(),
                    analysis_outputs={"fatigue_by_intensity": pd.DataFrame({"Fatigue_Score": [1]})},
                    dashboard_plan=sample_dashboard_plan(),
                    validation_report=sample_validation_report(),
                    df_context="dataframe context",
                )

        chart = actual.repaired_dashboard_plan.question_views[0].chart
        self.assertEqual(chart.orientation, "vertical")
        self.assertEqual(chart.sort_order, "descending")
        self.assertEqual(chart.metrics, [])

    def test_analytical_brain_builds_structured_input_and_invokes_chain(self):
        fake_chain = FakeChain(sample_insights())
        analytical_input = build_analytical_brain_input(
            metadata={"source_file": "athletes.csv"},
            semantic_understanding=sample_semantic(),
            metric_plan=sample_metric_plan(),
            analysis_outputs={
                "fatigue_by_intensity": pd.DataFrame(
                    {
                        "Training_Intensity": ["High", "Low"],
                        "Fatigue_Score": [62.1, 61.8],
                    }
                )
            },
            dashboard_plan=sample_dashboard_plan(),
            validation_report=sample_validation_report(),
            df_context="dataframe context",
        )

        with patch.object(
            analytical_agent,
            "build_analytical_brain_chain",
            return_value=fake_chain,
        ):
            result = analytical_agent.generate_analytical_insights(analytical_input)

        self.assertEqual(result.narrative_title, "Training Load Signals")
        self.assertIn('"source_file"', fake_chain.payload["metadata_json"])
        self.assertIn('"fatigue_by_intensity"', fake_chain.payload["analysis_outputs_json"])
        self.assertIn('"dashboard_title"', fake_chain.payload["dashboard_plan_json"])

    def test_analytical_input_and_output_are_validated_from_raw_payloads(self):
        analytical_input = build_analytical_brain_input(
            metadata={"source_file": "athletes.csv"},
            semantic_understanding=sample_semantic().model_dump(),
            metric_plan=sample_metric_plan().model_dump(),
            analysis_outputs={"fatigue_by_intensity": pd.DataFrame({"Fatigue_Score": [62.1]})},
            dashboard_plan=sample_dashboard_plan().model_dump(),
            validation_report=sample_validation_report().model_dump(),
            df_context="dataframe context",
        )

        with patch.object(
            analytical_agent,
            "build_analytical_brain_chain",
            return_value=FakeChain(sample_insights().model_dump()),
        ):
            result = analytical_agent.generate_analytical_insights(analytical_input.model_dump())

        self.assertIsInstance(analytical_input, analytical_agent.AnalyticalBrainInput)
        self.assertIsInstance(result, AnalyticalBrainResult)


if __name__ == "__main__":
    unittest.main()
