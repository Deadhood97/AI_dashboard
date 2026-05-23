# Smart AI Dashboarding System

An AI-powered analytics application that turns uploaded CSV datasets into explainable dashboards. The system is designed to behave like a junior data analyst: profile the dataset, infer structure and business context, generate analytical questions, create visualizations, derive grounded insights, and arrange the results into a coherent dashboard.

## MVP Goals

- Accept arbitrary CSV uploads.
- Profile datasets and infer schema/datatype information.
- Generate useful analytical questions automatically.
- Create basic Plotly visualizations from deterministic computations.
- Summarize insights from computed metrics.
- Show explainability logs for each major workflow step.
- Produce a simple dashboard layout with KPI cards, charts, insight summaries, filters, and reasoning traces.

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

## Architecture Principles

- Keep LLM reasoning separate from deterministic execution.
- Use Python code for profiling, cleaning, aggregations, metric computation, and chart rendering.
- Use LLMs for semantic interpretation, planning, explanation, and business-readable narratives.
- Store traceable artifacts such as generated questions, chart rationale, aggregation logic, rejected hypotheses, insight derivations, and dashboard layout decisions.
- Clearly label computed facts, inferred insights, and speculative observations.

## Planned Agent Workflow

1. Dataset Understanding Agent: infer domain, semantic column meanings, KPIs, feature types, and entity relationships.
2. Analytical Question Generation Agent: create prioritized questions that can be answered from the dataset.
3. Visualization and Code Generation Agent: generate executable analysis code, aggregations, Plotly charts, and chart rationale.
4. Insight Generation Agent: convert computed results into business-readable insights with limitations and confidence notes.
5. Dashboard Planning Agent: organize components into a coherent dashboard layout and explain the information hierarchy.

## Local Configuration

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Then add your OpenAI API key:

```text
OPENAI_API_KEY=your_api_key_here
```

If your local environment already uses `VITE_OPENAI_API_KEY`, the backend can be configured to fall back to that value during development.

Do not commit `.env` or real credentials.

## Run The MVP App

Create and activate a project virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies inside the virtual environment:

```powershell
pip install -r requirements.txt
```

Start Streamlit:

```powershell
streamlit run app.py
```

The current app supports CSV upload, optional dataset description capture, dataframe preview, basic column type analysis, and generated metadata storage at `artifacts/metadata/latest_metadata.json`.

The saved metadata includes a `schema` object with the user-provided dataset description and inferred column schema. This will be used later by the semantic understanding agent.

Application logs are written to `artifacts/logs/app.log`. If a CSV upload fails, the UI shows the error and the log file records the exception details.

If `py -3.12` is not available on a different machine, install Python 3.12 from python.org and then create the virtual environment with the available Python launcher or executable.

## Source Briefs

- `project-brief.md`
- `overview.md.txt`
