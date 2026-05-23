# Smart AI Dashboarding System

## Project Brief

The Smart AI Dashboarding System is an AI-powered analytics application that turns uploaded structured datasets into meaningful, explainable dashboards. The goal is to simulate the workflow of a junior data analyst: understanding the dataset, asking useful analytical questions, generating visualizations, deriving insights, and arranging everything into a coherent dashboard.

The system should be useful not only as an autonomous dashboard generator, but also as an educational assistant that shows users how analytical decisions are made.

## Core Objective

Build a system that can:

- Accept arbitrary CSV datasets.
- Understand dataset structure, meaning, and business context.
- Identify useful metrics, dimensions, entities, and relationships.
- Generate relevant analytical questions automatically.
- Produce appropriate charts and visualizations.
- Generate grounded business insights from computed results.
- Assemble a clear dashboard layout.
- Explain reasoning, assumptions, and limitations throughout the workflow.

## MVP Scope

The first version should prioritize reliability, transparency, and modularity over full autonomy.

### Initial Features

- CSV upload.
- Dataset profiling.
- Schema and datatype inference.
- Automatic analytical question generation.
- Basic chart generation with Plotly.
- Insight summaries based on computed metrics.
- Explainability logs for each major step.
- Simple dashboard layout generation.

## Recommended Stack

| Layer | Technology |
| --- | --- |
| Frontend | Streamlit |
| Backend | Python |
| Data Processing | pandas / polars |
| Agent Orchestration | LangGraph |
| LLM Provider | OpenAI API |
| Visualization | Plotly |
| Storage | SQLite |
| Vector Search | ChromaDB |
| Execution Layer | Sandboxed Python Runtime |

## System Architecture

The system should separate reasoning from execution.

LLMs should primarily:

- Interpret metadata.
- Generate analytical plans.
- Explain decisions.
- Produce business-readable narratives.

Deterministic Python code should:

- Clean and profile data.
- Compute metrics.
- Run aggregations.
- Generate charts.
- Validate outputs.

This separation improves reliability, debuggability, explainability, and maintainability.

## Multi-Agent Workflow

### 1. Dataset Understanding Agent

Interprets the uploaded dataset semantically.

Inputs:

- Dataset schema.
- Column statistics.
- Sample rows.
- Optional dataset description.

Outputs:

- Inferred business domain.
- Semantic column meanings.
- Identified KPIs.
- Temporal, categorical, and numerical feature mapping.
- Possible entity relationships.

Example:

```text
order_date -> temporal dimension
sales -> revenue metric
customer_id -> customer entity
product_category -> segmentation feature
```

Explainability:

- Why columns were categorized a certain way.
- Why specific fields are treated as KPIs.
- What relationships were detected.
- What assumptions were made about the business domain.

### 2. Analytical Question Generation Agent

Generates meaningful questions that can be answered using the dataset.

Example questions:

- Which categories contribute most to revenue?
- Are there seasonal patterns?
- Which customer segments are underperforming?
- What trends or anomalies exist?
- Which variables show strong relationships?

Outputs:

- Prioritized analytical questions.
- Suggested analysis paths.
- Rationale for why each question matters.

### 3. Visualization and Code Generation Agent

Generates executable analysis code and visualization specifications.

Responsibilities:

- Create pandas or polars analysis code.
- Compute aggregations and metrics.
- Select appropriate chart types.
- Generate Plotly charts.
- Explain how each chart answers a question.

Example:

```text
Question:
Which categories generate the highest revenue?

Output:
Grouped revenue aggregation + bar chart visualization
```

Explainability:

- Why a chart type was selected.
- Why specific dimensions and measures were paired.
- What the visualization is intended to reveal.
- How the generated code answers the analytical question.

### 4. Insight Generation Agent

Turns computed results into business-readable insights.

Responsibilities:

- Summarize trends.
- Identify anomalies.
- Compare segments.
- Explain correlations and metric changes.
- State confidence and limitations.

Example:

```text
Revenue increased 18% month over month, primarily driven by repeat purchases in the skincare category.
```

Explainability:

- Which metrics support the conclusion.
- What aggregations were used.
- What limitations might affect interpretation.
- Whether the insight is computed, inferred, or speculative.

### 5. Dashboard Planning Agent

Arranges the generated analysis into a coherent dashboard.

Responsibilities:

- Prioritize important insights.
- Decide chart hierarchy.
- Group related analytics.
- Structure dashboard sections.
- Optimize the user’s information flow.

Outputs:

- Dashboard layout plan.
- Component ordering.
- Section metadata.
- Explanation for layout decisions.

## Explainability Principles

The system should avoid behaving like a black box. At each stage, it should explain:

- What it is doing.
- Why it is doing it.
- What assumptions it is making.
- How conclusions are derived.
- What uncertainty or limitations exist.

The application should clearly distinguish:

- Computed facts.
- Inferred insights.
- Speculative observations.

## Final Application Experience

The frontend should dynamically render:

- KPI cards.
- Charts.
- Insight summaries.
- Grouped dashboard sections.
- Filters and interactions.
- Reasoning traces.
- Analytical explanations.

The user experience should feel like watching an AI analyst work through the data step by step.

## Engineering Challenges

### Generic Dataset Understanding

The system must work across unseen datasets with inconsistent column names, formats, and business domains.

### Reliable Code Generation

Generated analysis code must execute safely, handle malformed data gracefully, and produce deterministic outputs.

### Visualization Selection

Chart selection should depend on analytical intent, datatype compatibility, and business meaning.

### Insight Quality

Insights must be grounded in computed metrics and avoid unsupported claims.

### Dashboard Coherence

The dashboard should feel intentionally designed, not randomly assembled.

### Traceability

The system should store artifacts such as:

- Generated questions.
- Rejected hypotheses.
- Chart selection rationale.
- Aggregation logic.
- Insight derivation steps.
- Dashboard prioritization logic.

## Success Criteria

The project is successful if the system can:

1. Accept arbitrary structured datasets.
2. Generate relevant analytical questions automatically.
3. Produce meaningful visualizations dynamically.
4. Generate coherent business insights.
5. Assemble a usable dashboard with minimal human intervention.
6. Explain its analytical reasoning transparently.
7. Help users understand both the data and the system’s thought process.

## Future Extensions

- Conversational analytics.
- Live database connections.
- Autonomous exploratory analysis loops.
- Dashboard editing through natural language.
- Anomaly alerting.
- Report generation.
- Collaborative analytics.
- Multi-dataset reasoning.
- Agent memory and learning.
- Replayable reasoning sessions.

