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

The current app supports CSV upload, optional dataset description capture, explicit dataset submission, dataframe preview, basic column type analysis, and generated metadata storage in `artifacts/metadata/`.

The saved metadata includes a `schema` object with the user-provided dataset description and inferred column schema. This will be used later by the semantic understanding agent.

Each upload gets a CSV-specific metadata file named with the source CSV name and file hash. Uploading the same file with the same name overwrites that file's metadata; uploading a different CSV or changed file creates a separate metadata file. The app also maintains `artifacts/metadata/metadata_index.json` and updates `artifacts/metadata/latest_metadata.json` as a convenience pointer to the most recent upload.

Application logs are written to `artifacts/logs/app.log`. If a CSV upload fails, the UI shows the error and the log file records the exception details.

If `py -3.12` is not available on a different machine, install Python 3.12 from python.org and then create the virtual environment with the available Python launcher or executable.

## Standalone Semantic Agent

The first standalone agent lives in `agents/semantic_understanding.py`. It uses LangChain with OpenAI structured output to produce:

```python
class SemanticUnderstanding(BaseModel):
    dataset_domain: str
    primary_entities: list[str]
    important_dimensions: list[str]
    important_metrics: list[str]
    analytical_goals: list[str]
    suggested_questions: list[str]
```

It can be called from Python code, or run as a CLI against a metadata JSON file and CSV:

```powershell
python -m agents.semantic_understanding --metadata artifacts\metadata\latest_metadata.json --csv path\to\dataset.csv
```

The agent reads `OPENAI_API_KEY` from `.env` and falls back to `VITE_OPENAI_API_KEY` for local compatibility. Set `OPENAI_MODEL` to override the default model.

The Streamlit UI also includes a `Semantic Understanding` tab after CSV upload. Click `Generate semantic understanding` to run the agent against the uploaded dataset metadata and `df.head(5)`. The result is displayed in the app and saved to `artifacts/semantic/`.

## Standalone Metric Code Planner

The second standalone agent lives in `agents/metric_code_planner.py`. It takes a saved semantic understanding JSON file plus `df.head()` from a CSV and returns a structured pandas metric plan.

The output includes an agent summary, dashboard KPI specs, per-question analysis specs, output specs for future rendering, assumptions, limitations, and pandas code. The generated code assumes a dataframe named `df` already exists and stores outputs in a dictionary named `analysis_outputs`. It is not executed by the app yet.

```powershell
python -m agents.metric_code_planner --semantic artifacts\semantic\your_dataset_semantic.json --csv path\to\dataset.csv
```

## Source Briefs

- `project-brief.md`
- `overview.md.txt`
