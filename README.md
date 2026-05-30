# Dashboard Studio

Dashboard Studio is an AI-assisted analytics app that turns a CSV dataset into:

- a profiled dataset summary
- semantic understanding of the data
- generated pandas analysis code
- validated dashboard charts and KPIs
- analytical insights
- a Jupyter notebook-style audit trail
- saved artifacts that can be restored later

The easiest way to think about it:

> You give the app a dataset. The app behaves like a cautious junior data analyst: it studies the columns, writes analysis code, executes that code locally, validates the results, builds a dashboard, and explains what happened.

This project is currently in an active prototype-to-product transition. The existing app runs in Streamlit. A new product frontend is being planned on the `ui-overhaul` branch, backed by a FastAPI artifact API.

---

## Who This README Is For

This guide is written for beginners. You do not need to know the whole codebase to run the app.

You should be comfortable with:

- opening a terminal
- copying commands
- editing a `.env` file

If you are new to Python virtual environments, that is okay. Follow the setup steps exactly.

---

## What The App Does

Dashboard Studio can:

1. Load a CSV file from upload or Kaggle.
2. Profile the dataset.
3. Infer column roles, metrics, dimensions, and analytical goals.
4. Generate pandas code for useful analyses.
5. Execute generated code in a constrained local sandbox.
6. Validate the dashboard plan before rendering.
7. Ask a critic agent to repair weak dashboard plans.
8. Generate an analytical narrative.
9. Save outputs as JSON artifacts.
10. Generate a notebook artifact that shows the analysis process step by step.

---

## Current Tech Stack

| Layer | Current Tooling |
| --- | --- |
| App UI | Streamlit |
| API for future frontend | FastAPI |
| Data processing | pandas, numpy |
| Visualization | Plotly |
| LLM orchestration | LangChain structured output |
| LLM provider | OpenAI |
| Dataset import | CSV upload, Kaggle API |
| Notebook artifact | nbformat |
| Testing | unittest, Streamlit AppTest, FastAPI TestClient |

Planned frontend stack for the UI overhaul:

- Next.js
- React
- TypeScript
- Tailwind CSS
- Radix UI or shadcn/ui
- TanStack Query
- ECharts, Vega-Lite, or Plotly.js

---

## Project Structure

```text
.
|-- app.py                         # Streamlit app
|-- api.py                         # FastAPI read-only artifact API
|-- dashboard_validation.py         # Dashboard and chart validation rules
|-- notebook_export.py              # Builds .ipynb audit notebooks
|-- requirements.txt                # Python dependencies
|-- worklog.md                      # Running project worklog
|-- agents/
|   |-- semantic_understanding.py   # Semantic dataset understanding agent
|   |-- metric_code_planner.py      # Generates pandas metric plans/code
|   |-- dashboard_planner.py        # Creates dashboard structure
|   |-- dashboard_critic.py         # Repairs weak dashboard plans
|   |-- analytical_brain.py         # Produces final insights
|-- docs/
|   |-- dashboard-design-guide.md
|   |-- project-introduction.md
|-- tests/
|   |-- test_*.py
|-- artifacts/                      # Generated local outputs, ignored by git
|   |-- metadata/
|   |-- datasets/
|   |-- semantic/
|   |-- metric_plans/
|   |-- dashboard/
|   |-- critiques/
|   |-- insights/
|   |-- notebooks/
|   |-- logs/
```

The `artifacts/` folder is created by the app. It stores generated files locally and should not be committed.

---

## Quick Start

### 1. Open A Terminal In The Project Folder

Example path:

```powershell
cd "C:\Users\Lord Vader\Documents\AI dashboaring"
```

### 2. Create A Python Virtual Environment

```powershell
py -3.12 -m venv .venv
```

If `py -3.12` does not work, try:

```powershell
python -m venv .venv
```

### 3. Activate The Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Create Your Local Environment File

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your OpenAI API key:

```text
OPENAI_API_KEY=your_key_here
```

Never commit `.env`.

### 6. Run The Streamlit App

```powershell
streamlit run app.py
```

Open the URL Streamlit prints, usually:

```text
http://localhost:8501
```

---

## Optional: Enable Notebook View

The notebook view is feature-flagged.

In `.env`:

```text
ENABLE_NOTEBOOK_VIEW=true
```

When enabled, the app shows a `Notebook` tab after dashboard artifacts exist.

The notebook:

- shows dataset context
- shows semantic understanding
- shows generated pandas code
- shows executed metric outputs
- shows dashboard plan and validation
- shows analytical brain output
- can be downloaded as `.ipynb`

Notebook generation is non-blocking. If notebook export fails, the dashboard should still work.

---

## Optional: Kaggle Dataset Import

The app can fetch datasets directly from Kaggle.

You need Kaggle authentication. The easiest option is:

```powershell
kaggle auth login
```

Or set credentials in `.env`:

```text
KAGGLE_API_TOKEN=your_token_here
```

Legacy Kaggle credentials may also work:

```text
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key
```

In the app:

1. Choose `Kaggle dataset`.
2. Enter a dataset reference like:

```text
owner/dataset-slug
```

3. Optionally enter a specific CSV filename.
4. Click `Fetch from Kaggle`.
5. Prepare the dataset.

---

## Run The FastAPI Artifact API

The API is currently read-only. It exposes saved artifacts for the future product frontend.

Start it with:

```powershell
uvicorn api:app --reload --port 8000
```

Then open:

```text
http://localhost:8000/api/health
```

Useful endpoints:

```text
GET /api/health
GET /api/runs
GET /api/runs/latest
GET /api/runs/{run_id}
GET /api/runs/{run_id}/notebook
```

Example:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/runs/latest
```

---

## Run The New Frontend Shell

The `ui-overhaul` branch includes an early read-only Next.js frontend in `frontend/`.

It does not generate dashboards yet. It reads saved artifacts from the FastAPI API and renders a product-style workspace with:

- run history
- validation status
- dashboard plan cards
- analytical insights
- notebook preview
- artifact availability

Start the API first:

```powershell
uvicorn api:app --reload --port 8000
```

In another terminal, install and run the frontend:

```powershell
cd frontend
npm install
npm run dev
```

If PowerShell blocks `npm`, use:

```powershell
npm.cmd install
npm.cmd run dev
```

Open:

```text
http://localhost:3000
```

If your API is not running on port `8000`, set:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:your_api_port
```

The frontend also has browser tests that capture screenshots of the main states:

```powershell
cd frontend
npm.cmd run test:e2e
```

Screenshots are written to:

```text
frontend/test-results/screenshots/
```

---

## How The Pipeline Works

The simplified workflow:

```text
CSV or Kaggle dataset
        |
        v
Dataset profiling and metadata
        |
        v
Semantic understanding agent
        |
        v
Metric code planner agent
        |
        v
Sandboxed pandas execution
        |
        v
Dashboard planner agent
        |
        v
Dashboard validation
        |
        v
Dashboard critic repair loop
        |
        v
Analytical brain agent
        |
        v
Dashboard + notebook + saved artifacts
```

Important design rule:

> LLMs plan and explain. Deterministic Python computes and validates.

This keeps the app more reliable than asking an LLM to directly invent chart values.

---

## The Agents

### Semantic Understanding Agent

File:

```text
agents/semantic_understanding.py
```

Input:

- dataset metadata
- column summaries
- sample rows
- optional dataset description

Output:

- domain
- primary entities
- important dimensions
- important metrics
- analytical goals
- suggested questions

### Metric Code Planner Agent

File:

```text
agents/metric_code_planner.py
```

Input:

- semantic understanding
- dataframe context

Output:

- metric plan
- analysis output contracts
- generated pandas code
- assumptions
- limitations

The code must create:

```python
analysis_outputs = {}
```

### Dashboard Planner Agent

File:

```text
agents/dashboard_planner.py
```

Input:

- metadata
- semantic understanding
- metric plan
- dataframe context

Output:

- dashboard title and summary
- KPI specs
- overview charts
- question views
- assumptions
- limitations

### Dashboard Critic Agent

File:

```text
agents/dashboard_critic.py
```

Input:

- dashboard plan
- validation report
- metric plan
- compact analysis outputs

Output:

- repaired dashboard plan
- repair notes
- remaining risks

### Analytical Brain Agent

File:

```text
agents/analytical_brain.py
```

Input:

- semantic output
- metric plan
- analysis outputs
- dashboard plan
- validation report

Output:

- executive summary
- key insights
- evidence
- business implications
- recommended actions
- watchouts
- follow-up questions

---

## Saved Artifacts

The app writes local files under `artifacts/`.

Common artifact folders:

| Folder | Purpose |
| --- | --- |
| `artifacts/datasets/` | Saved CSV files |
| `artifacts/metadata/` | Dataset profile and index |
| `artifacts/semantic/` | Semantic agent outputs |
| `artifacts/metric_plans/` | Metric plan and generated pandas code |
| `artifacts/dashboard/` | Dashboard plans and validation reports |
| `artifacts/critiques/` | Dashboard critic repairs |
| `artifacts/insights/` | Analytical brain outputs |
| `artifacts/notebooks/` | Generated `.ipynb` audit notebooks |
| `artifacts/logs/` | Application logs |

If something fails, check:

```text
artifacts/logs/app.log
```

---

## Run Tests

Run everything:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Run a specific test file:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_api_contracts
```

Run the new frontend browser checks:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e
```

Current tests cover:

- agent payload contracts
- generated code sanitizer behavior
- dashboard validation rules
- chart rendering contracts
- notebook generation
- feature flags
- artifact path uniqueness
- FastAPI read-only contracts
- Next.js shell rendering
- notebook preview rendering
- insights, validation, artifacts, and mobile browser states

---

## Common Problems

### `OPENAI_API_KEY` Not Found

Make sure `.env` exists and contains:

```text
OPENAI_API_KEY=your_key_here
```

### Streamlit Does Not Start

Make sure your virtual environment is activated:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then reinstall dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Kaggle Import Fails

Check Kaggle authentication:

```powershell
kaggle auth login
```

Also confirm the dataset reference looks like:

```text
owner/dataset-slug
```

### Dashboard Looks Strange

The app includes validation and critic repair, but generated dashboards can still be imperfect.

Things to inspect:

- dashboard validation report
- chart scale notes
- `analysis_outputs` in the notebook
- `artifacts/logs/app.log`

### Notebook Shows Old Output

Regenerate the dashboard, or delete the matching file in:

```text
artifacts/notebooks/
```

Then regenerate the dashboard.

---

## Development Branches

Important branches:

| Branch | Purpose |
| --- | --- |
| `main` | Stable current app |
| `ui-overhaul` | Product UI redesign and FastAPI/Next.js migration |

---

## Documentation

Start here:

- `README.md`: beginner setup and usage
- `docs/project-introduction.md`: detailed objectives, architecture, and agent communication
- `docs/dashboard-design-guide.md`: dashboard quality rules
- `worklog.md`: ongoing project decisions and implementation notes

---

## Design Philosophy

Dashboard Studio should not be a black box.

The app should always make it possible to answer:

- What did the system calculate?
- What code did it run?
- What data did it use?
- Why did it choose this chart?
- What assumptions did it make?
- What should I be careful about?

That is why the project stores structured artifacts, validation reports, critic notes, and notebooks.
