# Worklog

This file records the steps taken while preparing the project for git, along with the reason for each step.

## 2026-05-23

### Read the project brief

Reviewed `project-brief.md` and `overview.md.txt` to understand the intended application: a Streamlit/Python AI dashboarding system that ingests CSV files, profiles datasets, generates analytical questions, creates Plotly visualizations, produces grounded insights, and explains the workflow through an agent-based pipeline.

Reason: Before preparing the repository, the project direction and expected stack need to be clear enough to create useful repo metadata.

### Inspected the project folder

Checked the root directory and found:

- `.env`
- `project-brief.md`
- `overview.md.txt`

Reason: This showed that the project was still in an early documentation-only state and that local secrets were already present.

### Checked git availability

Tried to run `git status --short --branch`, then checked for `git` with `where.exe git`.

Result: Git is not currently available on PATH in this shell.

Reason: This confirms that the project can be prepared for git with files like `.gitignore`, but git commands such as `git init`, `git add`, and `git commit` cannot be run from this environment yet.

### Added `.gitignore`

Created a `.gitignore` covering:

- local environment files
- Python cache/build/test artifacts
- virtual environments
- Streamlit secrets
- uploaded data and generated artifacts
- SQLite/Chroma storage
- optional frontend build artifacts
- common OS/editor files

Reason: This protects secrets and generated files from being committed once git is available.

### Added `.env.example`

Created a safe example environment file with an empty `OPENAI_API_KEY` placeholder.

Reason: Contributors need to know which environment variables are expected without exposing real credentials.

### Added `README.md`

Created a README summarizing:

- the project goal
- MVP scope
- recommended stack
- architecture principles
- planned agent workflow
- local configuration steps
- source brief files

Reason: A first commit should explain what the project is, how it is configured, and where the source planning documents live.

### Verified generated files for secrets

Searched generated non-env files for obvious OpenAI key patterns.

Result: Only the placeholder in `README.md` was found; no real key was copied into the generated files.

Reason: The project already contains a local `.env`, so it is important to make sure new git-tracked files do not duplicate sensitive values.

### Checked brief document encoding

Inspected non-ASCII characters in the brief files after the terminal displayed some characters oddly.

Result: The files contain valid Unicode punctuation such as em dashes and curly apostrophes. The odd display appears to be console encoding behavior, not corrupted file content.

Reason: This avoids making unnecessary edits to the original brief documents.

### Added `worklog.md`

Created this parallel worklog file to record the steps taken and explain why each one was useful.

Reason: The user requested a companion file documenting the process.

### Added `.gitattributes`

Created a `.gitattributes` file to normalize text files and mark common project file types as text.

Reason: This helps keep line endings consistent when the repository is eventually initialized and committed.

### Established ongoing worklog practice

Confirmed that `worklog.md` will be updated throughout the project as a running journal of meaningful steps, results, and explanations.

Reason: Keeping this file current makes the development process easier to review, resume, and understand later.

### Verified OpenAI environment variable

Checked `.env` for configured variable names without printing the secret value.

Result: The local key is stored under `VITE_OPENAI_API_KEY`.

Reason: Future agent-building code needs to know where to read the OpenAI API key from, while keeping the actual credential out of chat and tracked files.

### Updated environment documentation

Updated `.env.example` and `README.md` to document both `OPENAI_API_KEY` and the existing `VITE_OPENAI_API_KEY` compatibility path.

Reason: Python backend agents should prefer `OPENAI_API_KEY`, but supporting the existing local variable name prevents unnecessary secret file edits during development.

### Started the Streamlit MVP

Created `app.py` with a basic Streamlit interface for uploading a CSV file, reading it with pandas, and displaying the dataframe.

Reason: The first functional milestone is to prove that the app can ingest structured data and render it back to the user.

### Added column metadata analysis

Implemented simple column profiling that records pandas dtype, inferred analytical role, row count, null count, null percentage, unique count, sample values, and basic statistics for numeric and datetime columns.

Reason: This metadata will become the deterministic input for later dataset-understanding and agent-planning steps.

### Added metadata persistence

Configured the app to save the latest dataset metadata as JSON at `artifacts/metadata/latest_metadata.json`.

Reason: Persisting metadata creates a traceable artifact that later agents can inspect without re-reading the original upload.

### Added Python dependencies

Created `requirements.txt` with `streamlit` and `pandas`.

Reason: The project now has runnable application code, so dependencies need to be explicit.

### Updated run instructions

Updated `README.md` with dependency installation and Streamlit launch commands.

Reason: The project should be easy to run from a fresh checkout once git is available.

### Hardened metadata JSON serialization

Updated metadata value conversion so pandas and numpy scalar values can be written safely to JSON.

Reason: Column statistics often contain non-native scalar types, and the metadata artifact should save reliably for arbitrary CSV inputs.

### Added in-memory metadata storage

Stored the generated dataset metadata in `st.session_state["dataset_metadata"]` after CSV ingestion.

Reason: Later app steps and agents can reuse the metadata during the same Streamlit session without reloading it from disk.

### Attempted local verification

Tried to compile and test `app.py` locally, then checked for Python and Streamlit executables.

Result: `python` resolves to the Microsoft Store app execution alias, while `py` and `streamlit` are not available on PATH.

Reason: The code has been prepared, but this environment cannot currently run the Streamlit app until a working Python installation and dependencies are available.

### Searched for installed Python

Checked PATH, common Python install locations, Conda-style locations, and broader user/program folders.

Result: Found an embedded Python under `C:\Users\Lord Vader\Documents\Wallpaper\python_embed\python.exe`, but the user asked not to use it for this project.

Reason: The project should rely on a normal system/user Python installation instead of an unrelated embedded interpreter.

### Installed Python 3.12

Installed Python 3.12.10 through `winget` using the official `Python.Python.3.12` package with machine scope.

Result: Python is available through the launcher as `py -3.12`, and the main executable is at `C:\Program Files\Python312\python.exe`.

Reason: A standard Python installation is needed to run and verify the Streamlit application.

### Installed app dependencies

Installed dependencies from `requirements.txt` with `py -3.12 -m pip install -r requirements.txt`.

Result: `pandas 3.0.3` and `streamlit 1.57.0` are installed. The executable script folder is not on PATH, so commands should use `py -3.12 -m streamlit`.

Reason: The app now has the runtime packages needed for local execution.

### Verified Python app dependencies

Compiled `app.py` with Python 3.12 and imported pandas and Streamlit to confirm installed versions.

Result: `app.py` compiled successfully, and both core dependencies import correctly.

Reason: This confirms the first app slice is syntactically valid and the Python environment can load the required packages.

### Updated Streamlit run command

Changed README run instructions from `streamlit run app.py` to `py -3.12 -m streamlit run app.py`.

Reason: The Streamlit script directory is not currently on PATH, so the module form is more reliable on this machine.

### Started the Streamlit app

Launched the app with `py -3.12 -m streamlit run app.py --server.headless true --server.port 8501`.

Result: The server started successfully at `http://localhost:8501` and returned HTTP 200.

Reason: Running the app locally verifies that Streamlit can serve the first MVP interface.

### Attempted browser smoke test

Tried to open `http://localhost:8501` in the Codex in-app browser.

Result: The browser connector did not expose an `iab` browser in this session, so visual browser automation could not proceed.

Reason: The server is running and reachable, but visual confirmation through the in-app browser is unavailable in the current tool context.

### Fixed Python and Streamlit PATH entries

Updated the user PATH so Python 3.12 and package scripts are found before the Microsoft Store `WindowsApps` alias.

Paths added ahead of the alias:

- `C:\Program Files\Python312`
- `C:\Program Files\Python312\Scripts`
- `C:\Users\Lord Vader\AppData\Roaming\Python\Python312\Scripts`

Result: `python --version` now resolves to Python 3.12.10, `pip --version` resolves to the Python 3.12 install, and `streamlit --version` resolves to Streamlit 1.57.0.

Reason: The app should run with simple commands like `python`, `pip`, and `streamlit` instead of requiring the `py -3.12 -m ...` workaround.

### Simplified README run command

Changed the Streamlit launch command in `README.md` back to `streamlit run app.py`.

Reason: The PATH fix makes the standard command work again.

### Created project virtual environment

Created a local `.venv` with `py -3.12 -m venv .venv`.

Reason: A project-local virtual environment makes the app more portable and avoids relying on globally installed Python packages.

### Installed dependencies into `.venv`

Installed `requirements.txt` using `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

Result: Streamlit and pandas were installed inside the project environment.

Reason: Future runs should use the project environment so dependency versions are isolated from the rest of the computer.

### Verified app through `.venv`

Compiled `app.py`, imported pandas and Streamlit, and checked the Streamlit version using the virtual environment.

Result: `app.py` compiled successfully, pandas 3.0.3 imported, and Streamlit 1.57.0 imported from `.venv`.

Reason: This confirms the app can run from the portable project environment.

### Updated README with venv setup

Changed the run instructions to create and activate `.venv`, install dependencies, and then run Streamlit.

Reason: The README should guide future setup on another computer without depending on this machine's global PATH or global packages.

### Restarted Streamlit from `.venv`

Stopped the earlier Streamlit process that was launched through the global Python setup and started the app with `.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8501`.

Result: The app is reachable at `http://localhost:8501` and returns HTTP 200.

Reason: The running local app should match the new project-local virtual environment workflow.

### Added application logging

Added a file logger in `app.py` that writes to `artifacts/logs/app.log`.

Result: CSV upload attempts, successful processing events, and CSV parsing exceptions are now recorded in a dedicated app log.

Reason: If a file upload fails, the UI should not be the only place to see the failure; a persistent log makes debugging easier.

### Documented upload failure logs

Updated `README.md` to mention `artifacts/logs/app.log`.

Reason: Users need to know where to look when CSV upload or parsing fails.

### Verified logging change

Compiled `app.py` through `.venv` and checked that the running Streamlit server still returns HTTP 200.

Result: The code compiles successfully and the app remains reachable.

Reason: The logging change should not break the existing CSV upload interface.

### Explained pandas CSV buffer overflow error

Investigated the upload error: `Error tokenizing data. C error: Buffer overflow caught - possible malformed input file.`

Meaning: pandas' fast C parser could not tokenize the CSV safely, usually because the file contains malformed rows, inconsistent columns, broken quotes, unusual delimiters, huge fields, or encoding issues.

Reason: Understanding the failure mode helps decide whether to repair the input file or make ingestion more tolerant.

### Added CSV parser fallbacks

Updated CSV ingestion so the app first tries pandas' default parser, then falls back to the Python parser with delimiter inference, then a more tolerant Python parser that skips malformed rows.

Result: The app should now handle more real-world messy CSV files and logs every failed parser attempt to `artifacts/logs/app.log`.

Reason: The MVP should be reliable with imperfect datasets instead of failing immediately on the first parser error.

### Began GitHub sync

Started syncing the local project with `https://github.com/Deadhood97/AI_dashboard.git`.

Reason: The project needs to be connected to the remote repository so progress can be versioned and shared.

### Installed Git

Installed Git for Windows 2.54.0 with `winget`.

Reason: Git was not previously available in this shell, so repository initialization and GitHub sync could not proceed.

### Checked remote repository

Ran `git ls-remote` against the GitHub repository.

Result: The remote was reachable and returned no refs, which indicates an empty repository.

Reason: Knowing whether the remote already has commits prevents accidentally overwriting existing repository history.

### Initialized local repository

Initialized this folder as a Git repository on the `main` branch and added the GitHub repository as `origin`.

Result: `.env`, `.venv`, `__pycache__`, and `artifacts` are ignored; source and documentation files are untracked and ready to stage.

Reason: The local project needs a Git history before it can be pushed to the empty remote.

### Prepared local Git identity

Detected that Git user name and email were not configured.

Planned local-only identity:

- name: `Deadhood97`
- email: `Deadhood97@users.noreply.github.com`

Reason: A Git identity is required for commits, and keeping it local avoids changing global machine settings.

### Created initial git commit

Staged the source, documentation, and configuration files and created the initial commit:

`2a012ca Initial Streamlit CSV profiler`

Result: The commit includes `.env.example`, `.gitattributes`, `.gitignore`, `README.md`, `app.py`, `overview.md.txt`, `project-brief.md`, `requirements.txt`, and `worklog.md`.

Reason: The project needed a first versioned checkpoint before pushing to GitHub.

### Pushed to GitHub

Pushed the local `main` branch to `origin/main`.

Result: The local branch now tracks `origin/main` at `https://github.com/Deadhood97/AI_dashboard.git`.

Reason: This completes the first sync between the local project and the GitHub repository.

### Added dataset description input

Added a Streamlit text area where the user can optionally describe the uploaded dataset's domain, source, and business context.

Reason: User-provided dataset context will be important later for the semantic understanding agent because column names and datatypes alone may not explain the business meaning of the data.

### Stored description in metadata schema

Updated metadata generation so the cleaned dataset description is stored at `dataset_description` and inside a `schema` object alongside the inferred column schema.

Result: `artifacts/metadata/latest_metadata.json` now contains both machine-inferred column metadata and user-provided dataset context.

Reason: Keeping the description in the schema gives future agents a stable place to read semantic context.

### Documented schema description support

Updated `README.md` to mention dataset description capture and the saved `schema` object.

Reason: The app behavior and metadata contract should be visible in project documentation.

### Wrapped Streamlit UI in `main()`

Moved Streamlit UI execution into a `main()` function guarded by `if __name__ == "__main__"`.

Reason: This allows helper functions like metadata generation to be imported and tested without running the Streamlit interface.

### Verified dataset description schema change

Compiled `app.py`, tested `build_dataset_metadata()` with a sample dataframe and description, and checked that the running Streamlit server still returns HTTP 200.

Result: The generated metadata includes both `dataset_description` and `schema.description`, and `schema.columns` contains the inferred column metadata.

Reason: This confirms the description is stored in the metadata contract that future semantic agents will consume.

### Made metadata CSV-specific

Updated metadata persistence so every CSV upload creates a separate metadata file in `artifacts/metadata/` named with the CSV filename, upload timestamp, and file hash.

Reason: Metadata should not only live in `latest_metadata.json`; multiple uploaded CSVs need separate metadata artifacts that do not overwrite each other.

### Added metadata index

Added `artifacts/metadata/metadata_index.json`, which records each generated metadata file along with source filename, hash, creation time, row count, and column count.

Reason: The app needs a simple catalog of uploaded dataset metadata files for later workflow and agent orchestration.

### Kept latest metadata pointer

Kept `artifacts/metadata/latest_metadata.json` as a convenience copy of the most recent metadata artifact.

Reason: Some future development tasks may still benefit from a stable "latest upload" pointer, while the canonical per-upload metadata files preserve history.

### Documented multi-file metadata behavior

Updated `README.md` to explain the per-upload metadata files, metadata index, and latest metadata pointer.

Reason: The metadata storage behavior changed and should be clear before we build agents on top of it.

### Adjusted duplicate metadata behavior

Changed metadata filenames to use CSV filename plus file hash, without the upload timestamp.

Result: Uploading the same CSV file with the same name overwrites its existing metadata file, while changed files or different filenames still create separate metadata files.

Reason: Re-uploading the exact same dataset should refresh that dataset's metadata instead of creating duplicate historical entries.

### Made metadata index an upsert

Updated the metadata index writer to replace an existing entry when `source_file` and `file_sha256` match.

Reason: The index should mirror the overwrite behavior for identical file/name uploads instead of accumulating duplicate entries.

### Verified duplicate metadata behavior

Tested metadata saving with the same filename/hash twice and then with the same filename but a different hash.

Result: The same filename/hash reused and overwrote one metadata file, while the changed hash created a second metadata file. The index contained two entries.

Reason: This confirms the metadata store preserves separate datasets while avoiding duplicate artifacts for identical re-uploads.

### Started standalone semantic understanding agent

Added `agents/semantic_understanding.py` with a Pydantic `SemanticUnderstanding` output model and LangChain/OpenAI structured output chain.

Reason: The next project milestone is an agent that can turn dataset metadata plus `df.head()` output into semantic understanding fields for later dashboard planning.

### Added OpenAI key resolution for agents

Implemented API key loading from `.env`, preferring `OPENAI_API_KEY` and falling back to the existing local `VITE_OPENAI_API_KEY`.

Reason: The agent needs to use the existing OpenAI API key without exposing or copying the secret into tracked code.

### Added semantic agent CLI

Added a command-line path for running the semantic understanding agent against a metadata JSON file and a CSV file.

Reason: The agent is intentionally not integrated into Streamlit yet, but a standalone CLI makes it easy to test and iterate.

### Updated agent dependencies

Added `langchain-core`, `langchain-openai`, `python-dotenv`, `pydantic`, and `tabulate` to `requirements.txt`.

Reason: LangChain provides the OpenAI chat model and structured-output chain, dotenv loads local configuration, Pydantic defines the schema, and tabulate supports dataframe head markdown output.

### Documented standalone semantic agent

Updated `README.md` and `.env.example` with semantic agent usage and optional `OPENAI_MODEL` configuration.

Reason: The new agent should be discoverable and runnable before it is integrated into the app.

### Installed semantic agent dependencies

Installed the updated `requirements.txt` into `.venv`.

Result: LangChain, LangChain OpenAI, OpenAI SDK, python-dotenv, Pydantic, and tabulate are installed.

Reason: The standalone semantic agent needs these packages to build a structured-output OpenAI chain and render dataframe heads as markdown.

### Verified semantic agent offline

Compiled `app.py` and `agents/semantic_understanding.py`, instantiated the `SemanticUnderstanding` Pydantic model, and imported the new dependencies.

Result: Compilation, schema construction, and dependency imports all succeeded.

Reason: This validates the agent code shape without making a network call or spending API tokens.

### Ran semantic agent live smoke test

Called `generate_semantic_understanding()` with a tiny synthetic sales metadata payload and dataframe head.

Result: The OpenAI/LangChain structured-output call succeeded and returned valid `SemanticUnderstanding` JSON with domain, entities, dimensions, metrics, goals, and suggested questions.

Reason: This confirms the standalone agent can use the local OpenAI API key and return the exact schema needed for later integration.

### Integrated semantic agent into Streamlit UI

Added a `Semantic Understanding` tab that appears after CSV upload and includes a `Generate semantic understanding` button.

Reason: The user should be able to see what the app semantically understood about the uploaded dataset before later dashboarding agents act on it.

### Displayed semantic understanding output

Rendered the agent's dataset domain, primary entities, important dimensions, important metrics, analytical goals, and suggested questions in the UI.

Reason: Showing the structured output makes the app's interpretation transparent and easy for the user to inspect.

### Persisted semantic understanding artifacts

Added saving for semantic understanding JSON files under `artifacts/semantic/`, using the source CSV name and file hash.

Reason: Semantic understanding should be traceable as its own generated artifact, just like metadata.

### Added semantic agent UI error logging

Logged semantic agent failures to `artifacts/logs/app.log` and showed a Streamlit error message if generation fails.

Reason: OpenAI/API or parsing failures need a clear debugging path without exposing secrets.

### Verified semantic UI integration

Compiled `app.py` and `agents/semantic_understanding.py`, tested semantic artifact saving with a sample `SemanticUnderstanding` object, and checked that the running Streamlit server still returns HTTP 200.

Result: The semantic UI integration compiles, generated semantic output can be saved under `artifacts/semantic/`, and the app remains reachable.

Reason: This confirms the UI integration did not break the existing app before committing the change.

### Reconsidered app file structure

Noted that `app.py` began as a single-file MVP for speed, but the project now has enough behavior to justify splitting into coordinated modules.

Reason: Upload parsing, metadata persistence, semantic artifacts, logging, and UI rendering now represent separate responsibilities.

### Planned modular app structure

Planned a refactor where `app.py` becomes a thin Streamlit coordinator and implementation details move into focused modules.

Proposed structure:

```text
app.py
core/config.py
core/logging.py
data/ingestion.py
metadata/profiling.py
metadata/storage.py
semantic/storage.py
ui/semantic.py
agents/semantic_understanding.py
```

Responsibilities:

- `app.py`: page setup, user flow, tab layout, and coordination.
- `core/config.py`: shared artifact paths such as metadata, semantic output, and logs.
- `core/logging.py`: app logger setup.
- `data/ingestion.py`: CSV parser fallback logic.
- `metadata/profiling.py`: column role inference, JSON-safe conversion, column analysis, and dataset metadata construction.
- `metadata/storage.py`: metadata filenames, index updates, latest pointer, and save/load behavior.
- `semantic/storage.py`: semantic understanding artifact paths and persistence.
- `ui/semantic.py`: display helpers for semantic understanding output.
- `agents/semantic_understanding.py`: LangChain/OpenAI semantic understanding agent.

Dependency direction:

```text
app.py -> data / metadata / semantic / ui / agents
data -> core logging
metadata -> core config
semantic -> core config and agents schema
ui -> agents schema
agents -> LangChain/OpenAI only
```

Rules:

- Lower-level modules must not import `app.py`.
- Storage modules should not import Streamlit.
- Agent modules should not know about Streamlit session state.
- UI modules should render objects but not call OpenAI directly.
- Shared paths and logger setup should live outside `app.py` to prevent circular imports.

Reason: This keeps imports one-directional, reduces circular dependency risk, and makes each behavior easier to test before adding more agents.

### Fixed semantic output display bug

Moved the semantic understanding session-state lookup to after the generate button handler in `app.py`.

Result: When the user clicks `Generate semantic understanding`, the newly generated result should render immediately in the `Semantic Understanding` tab instead of showing the stale "Click the button" info message.

Reason: The previous code read session state before updating it, so Streamlit showed the success message while the display block still saw the old empty state.

### Added explicit dataset submission

Changed the Streamlit flow so uploading a CSV no longer immediately parses the file or generates metadata. The user now adds the dataset description, selects the CSV, and clicks `Submit dataset`.

Reason: The dataset description should be finalized before metadata/schema generation so the stored schema includes the intended user context.

### Added submitted dataset session state

Stored the submitted dataframe, metadata, metadata path, parser used, and dataset key in Streamlit session state after submission.

Reason: The app should avoid regenerating metadata on every Streamlit rerun while still resetting output when the file or description changes.

### Reset semantic output when input changes

Cleared prior semantic understanding results whenever the uploaded file or description changes before submission.

Reason: Semantic understanding must correspond to the currently submitted dataset and description, not a stale earlier upload.

### Kept submitted results visible across reruns

Adjusted the submit-button logic so previously submitted results stay visible on Streamlit reruns until the file or description changes.

Reason: Streamlit buttons are momentary, so the app needs to rely on session state after submission instead of hiding results when the button is no longer actively clicked.

### Started metric code planner agent

Added `agents/metric_code_planner.py` as a second standalone LangChain/OpenAI agent.

Reason: The next analytical step is to convert semantic understanding and dataframe sample rows into pandas code that calculates useful metrics.

### Defined metric code planner schema

Added Pydantic models `MetricDefinition` and `PandasMetricPlan`.

Result: The agent returns required columns, metric definitions, generated pandas code, expected output keys, assumptions, and limitations.

Reason: Generated code should be inspectable and explainable before it is executed.

### Added safety constraints to metric code prompt

Instructed the agent to assume `df` already exists, create an `analysis_outputs` dictionary, avoid file/network/API calls, avoid charts, and avoid `eval` or `exec`.

Reason: Code generation should remain deterministic and bounded before we add an execution layer.

### Added metric code planner CLI

Added a command-line interface that accepts a semantic understanding JSON file and CSV, then generates the metric code plan from `df.head()`.

Reason: The agent can be tested independently before integration into Streamlit or a sandboxed execution runtime.

### Documented metric code planner agent

Updated `README.md` with the standalone command for the metric code planner.

Reason: The new agent should be easy to discover and run from the project documentation.

### Strengthened metric planner structured output

Expanded the metric code planner output schema beyond raw code.

New structured sections:

- `agent_summary`
- `dashboard_metrics`
- `question_analyses`
- `analysis_outputs`
- `pandas_code`
- `assumptions`
- `limitations`

Reason: The metric planner should behave like an intelligent agent whose output can be inspected, rendered by the app, and consumed by later agents.

### Verified metric planner offline

Compiled the metric planner module and inspected the `PandasMetricPlan` schema fields.

Result: The schema contains `agent_summary`, `required_columns`, `dashboard_metrics`, `question_analyses`, `analysis_outputs`, `pandas_code`, `assumptions`, and `limitations`.

Reason: This validates the structured contract without making an API call.

### Ran metric planner live smoke test

Called the metric planner with a tiny retail sales semantic understanding and dataframe head.

Result: The OpenAI/LangChain structured-output call returned valid dashboard metric specs, question analyses, output specs, assumptions, limitations, and pandas code.

Reason: This confirms the agent behaves as an intelligent structured planner rather than only returning raw code.

### Tightened generated code instructions

Updated the metric planner prompt so defensive column conversions should be performed on a working dataframe copy and used in downstream calculations.

Reason: The live smoke test showed a possible mismatch where generated code converted a numeric column but still grouped on the original column.

### Added intelligent missing-value handling to metric planner

Updated `DashboardMetricSpec` and `QuestionAnalysisSpec` with a `missing_data_strategy` field.

Reason: Downstream agents and the UI need to know how missing values were handled for each planned metric or analysis.

### Strengthened metric planner NaN instructions

Updated the metric planner prompt so generated pandas code should handle NaN values intelligently instead of failing only because missing values exist.

Guidance added:

- drop rows only when required values are missing for a specific aggregation
- use numeric imputation such as 0, median, or mean only when analytically defensible
- use mode or `Unknown` labels for missing categorical dimensions when useful
- store missingness counts or data-quality notes in `analysis_outputs`
- raise errors only for missing required columns or unusable data after cleaning

Reason: Real datasets often contain missing values, and the analysis code should make explicit, explainable cleaning decisions rather than crash unnecessarily.

### Verified NaN-aware metric planner behavior

Ran a live metric planner smoke test with a dataframe head containing a missing category and missing sales value.

Result: The agent labeled missing categories as `Unknown`, dropped rows with missing sales for aggregation, added missingness information to `analysis_outputs`, and documented the strategy in the structured output.

Reason: This confirms the planner can make explainable missing-value handling choices instead of simply throwing errors on NaN values.

### Started dashboard planner agent

Added `agents/dashboard_planner.py`, a standalone LangChain/OpenAI agent that returns a structured `DashboardPlan`.

Reason: Dashboard layout and chart selection should be guided by an intelligent agent while remaining structured enough for the app and future agents to consume.

### Defined dashboard plan schema

Added structured models for dashboard KPIs, chart specs, question-answer views, and the overall dashboard plan.

Result: The dashboard planner returns a title, summary, data integrity notes, KPI specs, overview chart specs, question views, assumptions, and limitations.

Reason: Structured dashboard planning lets the app render safely without executing arbitrary LLM-generated code.

### Added Plotly dependency

Added `plotly` to `requirements.txt`.

Reason: The dashboard renderer needs Plotly charts.

### Added deterministic dashboard renderers

Added Streamlit rendering helpers for data integrity metrics, KPI cards, grouped chart data, Plotly charts, and dashboard plan display.

Reason: The agent should decide what to render, but deterministic app code should execute pandas/Plotly operations.

### Added Dashboard tab

Added a `Dashboard` tab that requires current semantic understanding, runs the dashboard planner on button click, saves the plan under `artifacts/dashboard/`, and renders the resulting dashboard.

Reason: Users need to see a basic dashboard with integrity checks, major KPIs, and answers to semantic-agent questions.

### Connected metric planner to dashboard planner

Updated the dashboard planner so it now consumes `PandasMetricPlan` output from the metric code planner in addition to metadata, semantic understanding, and `df.head()`.

Reason: The metric planner and dashboard planner should work together: one defines analytical computations and output specs, while the other decides how those planned outputs should appear in the dashboard.

### Updated dashboard generation flow

Changed the Streamlit Dashboard tab so `Generate dashboard` first runs the metric code planner, saves its structured output, then passes that metric plan into the dashboard planner.

Result: Metric plans are saved under `artifacts/metric_plans/`, and dashboard plans are saved under `artifacts/dashboard/`.

Reason: This avoids redundancy between agents and creates a clearer multi-agent pipeline.

### Updated dashboard planner CLI

Changed the dashboard planner CLI to require a saved metric plan JSON file.

Reason: Standalone dashboard planning should use the same inputs as the app pipeline.

### Verified dashboard planner pipeline

Ran a live smoke test where semantic understanding was passed into the metric code planner, then the resulting metric plan was passed into the dashboard planner.

Result: The pipeline returned a valid structured dashboard plan with KPI specs, overview chart specs, question views, assumptions, and limitations.

Reason: This confirms the metric planner and dashboard planner can operate as a connected multi-agent workflow.

### Tightened dashboard integrity grounding

Updated the dashboard planner prompt so data integrity notes must be grounded in metadata or `df.head()` evidence.

Reason: The live smoke test showed the planner could overstate missing-value issues when the synthetic metadata did not prove them.

### Audited generated dashboard output

Reviewed the generated renewable-energy dashboard plan, metric plan, semantic understanding, metadata, app renderer logic, and app logs.

Findings:

- Timeline charts are rendered from grouped data sorted by metric value, not by year, so time can appear out of order instead of left-to-right chronologically.
- Country-specific trend questions are collapsed into a single aggregated line because the renderer only supports `dimension` and `metric`, not a series/color column such as `country`.
- Multi-metric questions such as solar plus wind are split into separate single-metric charts, or only one metric is rendered, because chart specs only support one metric.
- Some dashboard KPIs do not match their stated rationale. For example, "Countries at 100% Renewable" uses a raw count of `country`, not a filtered count for countries reaching 100% renewable electricity in 2024-2025.
- Correlation is planned as a table with `metric=gdp`, but the renderer does not calculate correlation, so the dashboard cannot actually answer that question.
- Table views with filters, such as countries at 100% renewable electricity in 2024-2025, are rendered as generic grouped tables rather than applying the required threshold/year filters.
- The metric code planner creates useful named outputs, but the app does not execute or consume those outputs yet. The dashboard renderer recomputes simple charts directly from the dataframe, losing the richer analysis logic.
- The dashboard planner asks for analyses like "US, China, India, Germany", but the chart spec does not include filters, so the renderer cannot apply those selections.

Reason: The current dashboard generation is useful as a first prototype, but the agent plan and renderer contract are not expressive enough for time series, filtered views, multi-series charts, or computed answers.

### Upgraded metric-output render contract

Expanded metric planner `AnalysisOutputSpec` with `semantic_role`, `columns`, and `recommended_views`.

Reason: Dashboard planning needs to know whether each output is a scalar, ranked table, time series, entity time series, categorical comparison, correlation pair, distribution, raw table, or data-quality output.

### Upgraded dashboard chart contract

Added dashboard fields for `source_output_key`, `x`, `y`, `color`, `metrics`, `sort_by`, `sort_order`, and `orientation`.

Reason: The dashboard renderer needs explicit references to computed analysis outputs and enough display metadata to render timelines left-to-right, multi-line entity trends, scalar KPIs, and table fallbacks intelligently.

### Added constrained metric-plan execution

Added a local execution layer for metric planner pandas code.

Safety constraints:

- strips allowed pandas/numpy import lines and blocks all other imports
- blocks dangerous calls such as `open`, `exec`, `eval`, `compile`, `__import__`, and `input`
- blocks access to common filesystem/network/process modules
- provides a restricted builtins dictionary
- executes against a copy of the dataframe
- requires generated code to create an `analysis_outputs` dictionary

Reason: The dashboard needs to render the metric planner's named outputs, but generated code must be executed through guardrails.

### Switched dashboard renderer to analysis outputs

Changed KPI and chart rendering so dashboard specs read from `analysis_outputs` using `source_output_key`.

Result: The renderer can now support scalar outputs, dataframe outputs, series outputs, dictionaries, multi-line charts with `color`, multi-metric line charts, sorted timelines, and table fallbacks.

Reason: Rendering from planned outputs preserves the intelligence of the metric planner instead of recomputing shallow charts from raw dataframe columns.

### Verified upgraded dashboard contract

Compiled the app and agents, tested the constrained metric execution layer with a handcrafted metric plan, checked the running Streamlit server, and ran a live planner smoke test.

Result: The metric planner returned output specs with semantic roles and recommended views, and the dashboard planner returned chart specs with `source_output_key`, `x`, `y`, and ascending year sorting.

Reason: This confirms the new agent-to-renderer contract can support smarter dashboard rendering than the earlier raw-data chart guessing approach.

### Investigated dashboard generation failure

Checked `artifacts/logs/app.log` after dashboard generation failed.

Result: The failure occurred while executing generated metric planner pandas code, before dashboard planning. pandas raised `KeyError: [2025]`, which indicates generated code passed a data value such as a year into `dropna(subset=...)`, causing pandas to look for a column named `2025`.

Reason: This is a code-generation guardrail issue in the metric planner, not a Plotly rendering issue.

### Tightened metric code generation around `dropna`

Updated the metric planner prompt so `dropna(subset=...)` may only contain dataframe column-name strings, never data values such as years or category labels.

Reason: Year/category filters should use boolean masks such as `df_work["year"].isin([2024, 2025])`, then `dropna` should be applied only to required columns.

### Saved metric plan before execution

Changed the dashboard generation flow so the generated metric plan is saved before the app attempts to execute it.

Result: If metric execution fails, the failed metric plan remains available under `artifacts/metric_plans/` for debugging.

Reason: Execution failures need an inspectable artifact showing the exact generated code that failed.

### Replaced hardcoded `dropna` guard with repair loop

Removed the specific generated-code validator for `dropna(subset=[...])` because it was too narrowly tied to one pandas failure.

Added `repair_metric_code_plan()`, which sends the failed plan, semantic understanding, dataframe head, and execution error back to the metric planner agent for correction.

Result: Dashboard generation now attempts to generate a metric plan, execute it, and if execution fails, ask the agent to repair the full structured plan once before surfacing the error.

Reason: The scope of possible pandas code failures is broad, so the system should use intelligent repair rather than accumulating one-off hardcoded checks.

### Audited nonsensical dashboard charts

Inspected the generated dashboard artifacts and the screenshot showing the year-over-year renewable consumption and fossil-vs-renewable scatter charts.

Findings:

- The year-over-year chart showed only points around year 2000 because `top_n` was applied after sorting rows by year. This selected the first 10 rows, not the top 10 countries/entities.
- The scatter plot collapsed to fossil share 0 and renewable share 100 because `top_n` plus x-axis sorting selected one extreme corner of the data rather than a representative comparison.
- The metric agent was receiving only `df.head()`, which is not enough context for country/category values. This lets it guess labels such as `US` even when the dataset may store `United States`.
- A KPI titled "latest year" could still use `max`, which returns the highest historical value rather than the latest timestamp value.

Reason: The problem was not only chart choice. The app was treating row limits, category/entity limits, and sampling as the same operation, which made valid-looking specs render misleading charts.

### Improved dashboard chart limiting and agent context

Updated metadata to include categorical `top_values` and full `unique_values` when the cardinality is reasonable.

Added saved uploaded CSV copies under `artifacts/datasets/` so future debugging can replay a dashboard generation instead of relying only on in-memory Streamlit state.

Changed agent context from only `df.head()` to a richer dataframe context that includes dataset size, description, column metadata, value summaries, and the first rows.

Updated metric planner instructions to use exact category values from metadata or derive entities dynamically, rather than inventing aliases.

Updated dashboard planner instructions so `top_n` means categories/entities, not time-series rows, and so scatter plots are not reduced by extreme sorting.

Changed renderer behavior:

- multi-line/entity charts keep full timelines for selected entities
- scatter charts use a deterministic representative sample instead of sorting into an edge case
- tabular/bar charts still use ranked top-N behavior where that makes sense
- "latest" KPIs now prefer the latest temporal row over a generic max aggregation

Reason: The dashboard should preserve analytical meaning first, then limit visual complexity. The previous implementation limited visual complexity by cutting rows, which destroyed the meaning of the charts.

### Full dashboard pipeline audit

Audited the latest generated dashboard screenshot, saved dashboard JSON, saved metric plan JSON, app renderer, agent schemas, prompts, logs, and artifact storage.

Critical findings:

- Dashboard chart specs are too weak. They say `x`, `y`, `color`, `top_n`, and `source_output_key`, but they do not say whether the output is aggregated, what grain it has, what the intended entity is, or what a valid visual should look like.
- The metric planner can emit wide or tidy dataframes with multiple analytical dimensions, but the dashboard planner can still request one overloaded line chart for all of it.
- The renderer trusts chart specs too much. It does not reject charts with too many series, mixed grains, unreadable legends, single-year timelines, or extreme axis collapse.
- The repair loop only handles execution failure. It does not handle semantic failure, misleading output, unreadable charts, empty charts, or low-quality dashboard design.
- The current artifacts did not include the uploaded CSV for the dashboard run, so the exact bad dashboard could not be replayed after the fact. Uploaded CSV persistence has now been added for future runs.
- CLI paths in the agent modules still use simple `df.head()` context, while the Streamlit path now uses richer dataframe context. This creates inconsistent behavior between app and command-line testing.
- The dashboard UI presents every generated overview and question view. There is no ranking, pruning, or quality gate before display.

Root cause:

The system has intelligent planning agents, but no dashboard quality control layer. The app validates "can this execute?" and "can Plotly draw something?", but not "is this a meaningful chart?" or "does this answer the analytical question?"

Recommended architecture change:

1. Add deterministic metric-output validation immediately after metric execution.
2. Add deterministic dashboard-spec validation before rendering.
3. Add a dashboard critic/validator agent that reviews validation summaries and asks for repaired plans when the visuals are not analytically useful.
4. Add a quality gate that hides or converts failed charts to tables with a visible warning.
5. Persist validation reports alongside metric plans and dashboard plans.

Reason: The app should not treat generated dashboard plans as trusted UI. Generated plans should be proposals that must pass structural, statistical, and semantic checks before display.

### Added dashboard validation pipeline

Created `dashboard_validation.py` with structured validation models and deterministic checks.

Validation now checks:

- declared metric outputs exist
- metric outputs are not unexpectedly empty
- metric output specs match actual output columns
- KPI source outputs exist
- chart source outputs exist
- chart x/y columns exist
- line charts have at least two x-axis values
- line charts do not exceed the allowed visible series count
- line charts do not ignore extra categorical dimensions with multiple values
- bar charts have usable x/y fields
- scatter plots use numeric axes with meaningful variance
- scatter plots avoid excessive color legends

Integrated validation into the dashboard generation flow.

Result:

- every generated dashboard now receives a `DashboardValidationReport`
- validation reports are saved under `artifacts/dashboard/*_dashboard_validation.json`
- validation status is logged with dashboard generation
- invalid KPI cards are hidden
- invalid charts are hidden before rendering
- rejected chart sections show the validation error and suggested fix instead of plotting misleading visuals

Reason: The dashboard planner can propose charts, but the app must treat those proposals as untrusted until they pass quality checks.

### Tightened dashboard planner against validation rules

Updated the dashboard planner prompt to avoid charts that will fail validation.

Rules added:

- do not plot outputs with extra categorical dimensions unless those dimensions are filtered, aggregated, or represented visually
- keep line and multi-line charts to 12 visible series or fewer
- avoid timelines with fewer than two time values
- avoid scatter plots unless both axes are numeric and varied
- prefer ranked bars or tables when outputs have too many entities or mixed grains

Reason: The validator blocks bad charts after planning, but the planner should also learn to propose cleaner dashboard specs up front.

### Added dashboard critic agent

Created `agents/dashboard_critic.py`.

The critic agent receives:

- dataset metadata
- semantic understanding
- metric plan
- original dashboard plan
- deterministic validation report
- dataframe context

It returns a structured `DashboardCritique` containing:

- a critique summary
- a complete repaired dashboard plan
- repair notes
- remaining risks

Reason: The deterministic validator can identify invalid charts, but an LLM critic is better suited to rewriting the dashboard plan into a cleaner analytical experience.

### Integrated critic repair loop

Added `generate_validated_dashboard_plan()` to the app.

Flow:

1. dashboard planner generates an initial plan
2. deterministic validator checks the plan against executed metric outputs
3. if validation fails, the critic agent repairs the dashboard plan once
4. deterministic validator checks the repaired plan again
5. only the final validated plan is saved and rendered

Critique artifacts are saved under `artifacts/critiques/*_dashboard_critique.json`.

The UI now shows critic repair notes in an expander when a repair happened.

Reason: This creates a feedback loop where bad generated dashboards are corrected before the user sees them, while keeping deterministic validation as the final quality gate.

### Added dashboard design guide support

Reviewed current dashboard-design guidance from Tableau, Microsoft Power BI, and dashboard design research, then created `docs/dashboard-design-guide.md` as a compact local guide for the dashboard agents.

Connected the guide to both the dashboard planner and dashboard critic prompts.

Reason: The dashboard agents should not rely only on generic LLM judgment. A stable local guide gives them explicit rules about purpose, layout, chart selection, readability, sample-size-aware rankings, and validation expectations.

### Tightened dashboard quality validation

Replayed the latest `winemag-data-first150k` dashboard artifacts and found that the original validation passed charts that were technically renderable but analytically weak.

Problems found:

- Average wine rating rankings used many categories without sample-size support.
- Top winery rankings surfaced wineries with only one or two records.
- Region and variety comparisons mixed unrelated grains in the same chart.
- The description prediction view rendered a 150,930-row raw text table.

Updated deterministic validation to reject:

- Average/rating rankings without count support.
- Top average/rating charts where visible winners have fewer than 5 records.
- Mixed-grain bar charts using fields such as `group_type` or `region_type`.
- Very large unlimited tables.
- Large raw text tables.

Also updated the metric planner prompt to require count/sample-size columns and minimum sample-size filtering for average/rating/score rankings.

Verification: Replayed the old wine dashboard through the new validator. It now fails and rejects the weak charts instead of marking the dashboard as clean.

Reason: The app needs to distinguish "Plotly can draw this" from "this is a meaningful dashboard." This change makes the quality gate much closer to what a human analyst would reject.

### Tightened visible dashboard curation

Reviewed the latest generated wine dashboard after the design-guide and validation changes.

Finding: The output was still not good enough because the system had converted weak charts into too many table views. This made the dashboard technically safer but still hard to read.

Changes made:

- Fixed validation for scalar and dictionary metric outputs so usable KPI/text outputs are not incorrectly marked as missing columns.
- Added unique Plotly chart keys to avoid duplicate Streamlit chart ID errors when similar charts are rendered.
- Render dictionary/text outputs as compact metric summaries instead of raw one-row dataframes.
- Capped table displays at 25 rows.
- Capped visible overview charts at 2.
- Capped visible question views at 3.
- Prioritized chart-like views before table views when choosing which question views to show.
- Updated the dashboard planner, critic, and design guide to explicitly prefer compact dashboards with limited tables.

Verification: Replayed the latest wine dashboard artifacts. The visible output is now reduced to one overview bar chart, one winery bar chart, one modeling summary, and one 25-row table instead of a long wall of tables.

Reason: A dashboard quality gate should improve the user-facing dashboard, not merely replace bad charts with too many tables.

### Fixed Kaggle dashboard generation indentation failure

Investigated why dashboard generation failed for the Kaggle housing affordability dataset.

Finding: The failure happened before dashboard planning. The metric code planner returned pandas code with invalid leading indentation, and `validate_generated_code()` calls `ast.parse()` before execution. The initial metric plan failed with:

- `IndentationError: unexpected indent`

The automatic metric repair loop then returned code with the same syntax problem, so `generate_executable_metric_plan()` exhausted its repair attempt and the app showed that the dashboard could not be produced.

Changes made:

- Updated `sanitize_generated_code()` to dedent generated pandas code before validation.
- Added support for stripping accidental markdown code fences from generated code.
- Added an indentation fallback for uneven top-level indentation while preserving normal nested blocks.
- Added `tests/test_generated_code_sanitizer.py` with standard-library `unittest` coverage for indented code and fenced code.

Verification:

- `python -m unittest tests.test_generated_code_sanitizer` passes.
- `python -m py_compile app.py tests/test_generated_code_sanitizer.py` passes.

Reason: The app should be strict about unsafe or invalid generated code, but it should tolerate harmless formatting artifacts from structured LLM output before deciding the metric plan is unusable.

### Started frontend product polish pass

Reviewed the current Streamlit UI from a product/design perspective.

Finding: The dashboard output was becoming analytically strong, but the frontend still felt too much like a raw prototype. The main issues were:

- source controls competed with the dashboard content
- many generic info/success boxes made the flow feel noisy
- chart titles duplicated Plotly titles
- tabs were organized around implementation details rather than user jobs
- the visual system relied almost entirely on Streamlit defaults

Changes made:

- Added a restrained visual system with custom spacing, tabs, buttons, metrics, sidebar styling, and section headers.
- Renamed the product surface to `Dashboard Studio`.
- Moved source selection, upload/Kaggle input, and dataset preparation into the sidebar.
- Reframed main tabs as `Preview`, `Schema`, `Understanding`, `Dashboard`, and `Artifacts`.
- Added polished empty states for unloaded datasets and incomplete analysis stages.
- Replaced loud artifact/status captions with quieter artifact path helpers.
- Added dataset summary metrics after preparation.
- Removed duplicated Plotly chart titles and let the app-level chart headers carry the hierarchy.
- Wrapped repeated dashboard charts in bordered containers to make the dashboard easier to scan.
- Renamed dashboard sections from generic labels such as `Major KPIs` and `Overview Charts` to product-oriented sections like `Key Measures`, `Dataset Health`, `Overview`, and `Question Views`.

Verification:

- `python -m py_compile app.py` passes.
- Streamlit AppTest smoke checks pass for both upload mode and Kaggle mode.

Reason: The app should feel like a serious analytics workspace, not a collection of generated Streamlit controls. The frontend needs to communicate trust, workflow state, and dashboard hierarchy as clearly as the backend does.

### Fixed broken frontend theme and first screen

Reviewed a user-provided screenshot after the first frontend polish pass.

Finding: The app was visually broken because Streamlit was running in dark theme while the custom CSS assumed a light product surface. This created unreadable sidebar controls, low-contrast labels, a dark empty main canvas, and an empty-state card that looked like a blank generated placeholder.

Changes made:

- Added `.streamlit/config.toml` to force a coherent light theme.
- Updated global CSS so the app, sidebar, inputs, text areas, upload control, buttons, metrics, and empty state all use explicit product colors.
- Removed the decorative kicker from the page header because it competed with Streamlit chrome and felt too marketing-like.
- Reduced page title sizing, especially on mobile.
- Rewrote the first-screen empty state into a clear onboarding panel with three workflow steps: load data, generate context, review output.
- Added mobile-aware copy telling users to open the source panel from the top-left control.
- Took desktop and mobile screenshots after the fix:
  - `artifacts/screenshots/dashboard-studio-desktop-fixed.png`
  - `artifacts/screenshots/dashboard-studio-mobile-fixed.png`

Verification:

- `python -m py_compile app.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer` passes.
- Streamlit AppTest smoke check passes.
- Playwright screenshots confirm readable desktop and mobile first screens.

Reason: Best frontend practice for this product is not decorative polish. It is clear workflow state, strong contrast, calm density, mobile-safe instructions, and a layout that makes the next action obvious.

### Added analytical brain agent

Planned and started the final insight agent: the analytical brain.

Goal: After the semantic agent, metric planner, dashboard planner, validation, and optional critic repair have produced a dashboard, the analytical brain synthesizes the generated outputs into high-quality business insights.

Structured input:

- dataset metadata
- semantic understanding agent output
- metric code planner output
- compacted deterministic analysis outputs
- final dashboard plan
- dashboard validation report
- dataframe context

Structured output:

- narrative title
- executive summary
- prioritized key insights
- evidence for each insight
- business implication
- recommended action
- confidence
- impact
- related dashboard items
- watchouts
- follow-up questions

Changes made:

- Added `agents/analytical_brain.py`.
- Added `AnalyticalBrainInput`, `AnalyticalBrainResult`, and `DashboardInsight` Pydantic models.
- Used OpenAI structured output for the analytical brain result.
- Added compacting for tabular analysis outputs before sending them to the LLM.
- Wired the analytical brain after dashboard validation in the app.
- Saved analytical insight artifacts under `artifacts/insights/`.
- Rendered analytical insights near the top of the Dashboard tab before health/KPI/chart sections.
- Made the analytical brain non-blocking so the dashboard still renders if insight generation fails.
- Removed parser details from the visible dataset summary because users do not need that implementation detail in the main product UI.

Verification:

- `python -m py_compile app.py agents/analytical_brain.py agents/dashboard_critic.py agents/dashboard_planner.py agents/metric_code_planner.py dashboard_validation.py tests/test_generated_code_sanitizer.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer` passes.
- Streamlit AppTest smoke checks pass for upload and Kaggle modes.

Reason: The dashboard should not only show computed views; it should explain what matters. The analytical brain turns validated dashboard outputs into a clear, evidence-backed narrative while keeping all inputs and outputs structured for reliability and future notebook tracing.

### Moved chart scale quality into critic loop

Reviewed a dashboard screenshot where bar charts had values clustered around the 50s and 60s but were rendered from a zero baseline. The charts were technically correct, but the scale hid the meaningful differences.

Initial thought was to auto-scale charts in the renderer, but that would make scale changes invisible to the dashboard quality process. Revised approach:

- Added explicit `value_axis_min`, `value_axis_max`, and `scale_note` fields to `DashboardChartSpec`.
- Updated dashboard planner guidance to use narrowed scales only when needed and to disclose them.
- Updated deterministic validation to flag bar and line charts where values are tightly clustered and a zero baseline hides meaningful differences.
- Made that scale issue an error so the dashboard critic repair loop is invoked.
- Updated dashboard critic guidance so it repairs scale issues by setting explicit axis bounds and a visible scale note, rather than silently changing rendering.
- Passed compact analysis output samples into the critic so it can see the actual values and choose a sensible range with padding.
- Updated the renderer to apply only declared axis ranges from the chart spec, and to display the declared `scale_note`.
- Added `tests/test_dashboard_scale_validation.py` to verify clustered charts require declared scale metadata and pass once the scale is explicitly documented.

Verification:

- `python -m py_compile app.py dashboard_validation.py agents/dashboard_planner.py agents/dashboard_critic.py agents/analytical_brain.py tests/test_dashboard_scale_validation.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer tests.test_dashboard_scale_validation` passes.
- Streamlit AppTest smoke check passes.

Reason: Scale is an analytical design decision, not a renderer convenience. The critic should call it out, repair it explicitly, and leave a visible note so the user understands when an axis does not start at zero.

### Added artifact-backed app history and agent cache

Reviewed a state problem where clicking dashboard actions could make the app feel like the fetched/prepared data had disappeared. The root issue was that the UI treated the sidebar source widgets as the only source of truth, while prepared datasets and generated agent artifacts already existed on disk.

Changes made:

- Added dataset hydration from `artifacts/metadata/latest_metadata.json` and the saved dataset CSV.
- Added restore helpers for semantic understanding, dashboard plans, metric plans, validation reports, critiques, analytical insights, and deterministic analysis outputs.
- Added stable cache keys for semantic and dashboard artifacts.
- Changed the main flow so an empty source panel can still restore the latest prepared dataset instead of returning to a blank start screen.
- Stopped clearing prepared state just because source widget values differ; downstream state is cleared only when preparing a new dataset.
- Added visible captions when dataset, semantic output, or dashboard artifacts are restored from history.
- Restored dashboards rerun only deterministic metric code locally; semantic/dashboard/critic/analytical agents are not called again when matching artifacts already exist.

Verification:

- `python -m py_compile app.py dashboard_validation.py agents/dashboard_critic.py agents/dashboard_planner.py agents/analytical_brain.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer tests.test_dashboard_scale_validation` passes.
- Streamlit AppTest smoke check passes.

Reason: The app should behave like a workspace, not a one-shot form. Once data or agent outputs have been created, they should be remembered and reused until the user intentionally prepares a different dataset or regenerates a step.

### Guarded dashboard history against stale artifacts

Investigated a dashboard restore issue where chart cards showed messages such as:

- `Missing analysis output: mental_wellbeing_by_demographic`
- `Missing analysis output: top_regions_innovation_rate`

Finding: The saved dashboard plan referenced output keys that were not produced by the saved metric plan for the same dataset. The app restored both artifacts from history but did not check whether their contracts still matched before rendering.

Changes made:

- Added `missing_dashboard_output_keys()` to compare dashboard KPI/chart `source_output_key` values against current `analysis_outputs`.
- Updated dashboard artifact restore so stale dashboard history is rejected if referenced output keys are missing.
- Recompute validation during restore from the restored metric outputs instead of trusting an old validation artifact blindly.
- Added a final render-time compatibility check so broken chart cards are not shown if stale state is already in memory.
- Added `clear_dashboard_history_state()` to remove stale dashboard state while preserving the prepared dataset and semantic output.
- The UI now shows a single warning explaining that saved dashboard history is out of sync and asks the user to regenerate, instead of rendering multiple broken chart cards.

Verification:

- `python -m py_compile app.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer tests.test_dashboard_scale_validation` passes.
- Streamlit AppTest smoke check passes.

Reason: History is useful only if restored artifacts still satisfy their contracts. Dashboard plans and metric outputs must be treated as a matched pair; otherwise the app should invalidate the dashboard layer and ask for regeneration.

### Fixed current dashboard generation errors

Checked current logs after dashboard generation failed on the athlete performance dataset.

Findings:

- The latest metric plan first generated prohibited imports.
- The repair attempt produced a custom `pointbiserialr` helper that still depended on Python import machinery, causing `KeyError: '__import__'` inside the sandbox.
- A previous scale-rule edit accidentally made the dashboard planner system prompt a 3-item tuple instead of the required `(role, template)` pair.
- Analytical insight generation could fail when compacted pandas outputs contained non-JSON-native values such as `Interval`.

Changes made:

- Fixed the dashboard planner prompt tuple by merging the scale guidance into the system prompt string.
- Strengthened metric planner and repair prompts to avoid scipy/sklearn/statsmodels and import-dependent statistical helpers.
- Directed correlation-style analyses toward pandas/numpy-native operations.
- Increased metric plan repair attempts from 1 to 2.
- Added safe builtins commonly needed by generated pandas code: `isinstance`, `zip`, `all`, and `any`.
- Tightened generated-code validation to reject access to interpreter internals such as `__builtins__`, `__loader__`, and `__spec__`.
- Added scipy/sklearn/statsmodels to blocked roots.
- Made analytical brain output compaction JSON-safe.
- Made dashboard critic output compaction JSON-safe as well, since it now receives analysis output samples.

Verification:

- `python -m py_compile app.py agents/metric_code_planner.py agents/dashboard_planner.py agents/dashboard_critic.py agents/analytical_brain.py dashboard_validation.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer tests.test_dashboard_scale_validation` passes.
- Streamlit AppTest smoke check passes.

Reason: Generated metric code should stay inside the deterministic pandas/numpy sandbox. When it needs statistical summaries, it must use safe dataframe operations rather than import-dependent helper functions.

### Improved metric syntax repair diagnostics

Investigated the current UI error:

- `Could not generate dashboard: invalid syntax (<unknown>, line 62)`

Finding: The metric planner produced invalid Python with a dangling `else:` block. The repair loop retried twice, but it did not pass the sanitized failing code back into the repair prompt, making it harder for the LLM to fix the exact syntax problem. The sanitizer could also raise `SyntaxError` while trying to prepare failing code for diagnostics.

Changes made:

- Updated `repair_metric_code_plan()` to accept `failing_code`.
- Added explicit repair instructions: return plain top-level Python only, no markdown fences, no dangling `else/elif`, and complete every conditional block.
- Updated `generate_executable_metric_plan()` to pass sanitized failing code into each repair attempt.
- Added failed metric-plan artifact logging under `artifacts/metric_plans/*_failed_metric_plan_*.json`.
- Changed `sanitize_generated_code()` so non-indentation syntax errors are returned for validation/repair instead of being raised inside the sanitizer.
- Added a regression test covering dangling `else` behavior.

Verification:

- `python -m py_compile app.py agents/metric_code_planner.py agents/dashboard_planner.py agents/dashboard_critic.py agents/analytical_brain.py dashboard_validation.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer tests.test_dashboard_scale_validation` passes.
- Streamlit AppTest smoke check passes.

Reason: When generated code is syntactically invalid, the repair agent needs the exact failing code and the app needs a saved artifact for debugging. Syntax validation should fail in the validation step, not inside code cleanup.

### Bug audit

Reviewed the current working tree after the state/history, analytical brain, metric repair, and chart scale changes.

Findings:

- `dashboard_validation.py` rejects wide-form `multi_line` specs even though the dashboard planner and renderer support `metrics=[...]` without a single `y` column. Reproduced with a two-metric dataframe: validator returns `Line charts require both x and y fields.`
- `dashboard_validation.py` does not warn for valid bar charts with many categories when `x` and `y` are both valid and `top_n` is missing. Reproduced with 30 categories: validator returns no issues.
- Artifact history keys include semantic context, but artifact file paths are still based only on source filename and file hash. Reusing the same data file with a changed description can overwrite or restore stale semantic/dashboard/insight artifacts.
- Failed metric plan artifacts use second-level timestamps, so multiple repair failures in the same second can overwrite each other.
- Dashboard restore currently requires the saved validation artifact to exist even though it recomputes validation during restore. This can prevent otherwise usable dashboard + metric artifacts from being restored.

Verification:

- `python -m py_compile app.py agents/metric_code_planner.py agents/dashboard_planner.py agents/dashboard_critic.py agents/analytical_brain.py dashboard_validation.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer tests.test_dashboard_scale_validation` passes.
- Added a small local reproduction for validator behavior; no source changes made during this audit.

Reason: The remaining issues are mostly cross-agent contract mismatches rather than syntax errors. Fixing these should make dashboard generation and history restore feel much more predictable.

### Fixed critic compaction crash and added contract tests

Checked the current app log after dashboard generation still failed.

Finding:

- The latest failure was in the dashboard critic repair path, not the metric planner. The critic now receives `analysis_outputs` so it can make better chart repairs, but its compaction helper treated any pandas object with `head()` and `to_dict()` as a dataframe.
- Pandas `Series` also has those methods, but `Series.to_dict()` does not accept `orient="records"`, causing: `TypeError: Series.to_dict() got an unexpected keyword argument 'orient'`.
- The athlete metric outputs include Series outputs such as `injury_indicator_counts` and `data_quality_missing_counts`, so this crash was deterministic once dashboard validation triggered critic repair.

Changes made:

- Updated `agents/dashboard_critic.py` and `agents/analytical_brain.py` to use the dataframe record-sample path only when the output has dataframe-style `columns`.
- Added `tests/test_analysis_output_compaction.py` for Series and DataFrame compaction.
- Hardened dashboard validation so wide-form `multi_line` charts can use `metrics=[...]` without a single `y` field, matching the renderer contract.
- Added validation for missing metric columns in chart specs.
- Fixed the many-category bar warning so valid bar charts with no `top_n` are checked.
- Changed failed metric-plan artifact paths to include a UUID suffix after a test showed fast retries can collide even with microsecond timestamps on Windows.
- Added `tests/test_dashboard_contract_validation.py` and `tests/test_artifact_paths.py`.

Verification:

- `python -m py_compile app.py agents/metric_code_planner.py agents/dashboard_planner.py agents/dashboard_critic.py agents/analytical_brain.py dashboard_validation.py` passes.
- `python -m unittest tests.test_generated_code_sanitizer tests.test_dashboard_scale_validation tests.test_analysis_output_compaction tests.test_dashboard_contract_validation tests.test_artifact_paths` passes: 12 tests.
- Executed the saved athlete metric plan locally; it produced 15 outputs and both critic/analytical compaction handled the Series outputs.
- `Invoke-WebRequest http://localhost:8501` returns 200.
- Streamlit AppTest smoke check reports 0 exceptions.

Reason: The app is now a multi-agent contract pipeline. Tests need to cover boundaries between agent output schemas, pandas runtime values, validation, repair, and artifact storage, not just individual functions.

### Added tests for all agents

Added agent-level regression tests that do not call external LLMs.

Coverage added:

- Semantic agent:
  - Chain builder constructs with mocked OpenAI client.
  - `generate_semantic_understanding()` sends compact metadata JSON and dataframe context into the chain.
- Metric code planner:
  - Chain builder constructs with mocked OpenAI client.
  - `generate_metric_code_plan()` sends structured semantic JSON and dataframe context into the chain.
- Dashboard planner:
  - Chain builder constructs with mocked OpenAI client, catching prompt tuple regressions.
  - `generate_dashboard_plan()` sends metadata, semantic understanding, metric plan JSON, dataframe context, and design guide.
- Dashboard critic:
  - Chain builder constructs with mocked OpenAI client.
  - `repair_dashboard_plan()` sends compacted dataframe and Series analysis outputs, dashboard plan, validation report, and design guide.
- Analytical brain:
  - Chain builder constructs with mocked OpenAI client.
  - `build_analytical_brain_input()` compacts analysis outputs into structured input.
  - `generate_analytical_insights()` sends metadata, semantic output, metric plan, compact analysis outputs, dashboard plan, and validation report.

Verification:

- `python -m py_compile app.py agents/metric_code_planner.py agents/dashboard_planner.py agents/dashboard_critic.py agents/analytical_brain.py dashboard_validation.py tests/test_agents_contracts.py` passes.
- `python -m unittest discover -s tests` passes: 18 tests.
- `Invoke-WebRequest http://localhost:8501` returns 200.

Reason: The safest way to test LLM agents here is to test the structured boundaries and payload plumbing with mocked chains, while keeping deterministic validation and pandas-output tests separate.

### Planned Jupyter notebook integration

Goal: Add a notebook artifact and app view that explains how the dashboard was produced step by step, with generated code, executed outputs, validation results, and analytical-brain insights embedded.

Planned architecture:

- Add a notebook builder module, likely `notebook_export.py`, using `nbformat` to create `.ipynb` artifacts deterministically from saved pipeline state.
- Save notebooks under `artifacts/notebooks/`, keyed by the same dashboard/history key used for metric plan, dashboard plan, validation, critique, and insights.
- Generate a notebook after successful dashboard generation and restore it from history when compatible artifacts already exist.
- Render the notebook inside the Streamlit app in a new tab, probably named `Notebook`, using a safe HTML conversion path or a structured in-app cell renderer.
- Provide a download button for the `.ipynb` artifact.

Notebook structure:

1. Dataset context:
   - Dataset source, row/column counts, description, schema summary, and a small dataframe preview.
2. Semantic understanding:
   - Domain, entities, dimensions, metrics, analytical goals, and suggested questions.
3. Metric plan:
   - Plain-language metric plan summary.
   - Required columns.
   - Output contracts.
   - Generated pandas code as a code cell.
4. Executed metric outputs:
   - One section per `analysis_outputs` key.
   - DataFrame/Series previews as executed outputs.
   - Scalar outputs as markdown or display values.
5. Dashboard plan:
   - KPIs, chart specs, question views, assumptions, limitations, and scale notes.
6. Validation and critic:
   - Validation status, rejected components, warnings/errors, and critic repair notes when present.
7. Analytical brain:
   - Executive summary.
   - Key insights with evidence, implication, recommendation, confidence, and impact.
   - Watchouts and follow-up questions.
8. Reproducibility footer:
   - Artifact paths, generation timestamp, app version/commit if available, and caveats about external LLM generation.

Execution model:

- Do not let arbitrary notebook code run from the browser.
- The app should execute metric code through the existing sandbox first, then serialize outputs into notebook cells.
- The notebook can include generated code cells for transparency, but rendered outputs should come from the already validated app execution.
- Optional later enhancement: use `nbclient` in a controlled local environment to execute only trusted generated notebook cells after the app sandbox passes.

Product behavior:

- The frontend dashboard remains the polished consumption view.
- The notebook becomes the explanation and audit trail view.
- Agents should write structured outputs once; both the dashboard and notebook render from those same artifacts.
- History should prevent rerunning agents for the same dataset/context unless artifacts are stale or the user explicitly regenerates.

Testing plan:

- Unit test notebook generation from fake semantic, metric, dashboard, validation, critic, insight, and analysis-output objects.
- Assert expected markdown/code cell order and key titles.
- Assert DataFrame, Series, scalar, dict, and empty outputs render without errors.
- Assert notebooks are keyed/restored consistently with dashboard history.
- Add a Streamlit smoke test ensuring the Notebook tab renders when a notebook artifact exists.

Reason: A notebook artifact gives the app a traceable analytical narrative without turning the frontend into a code notebook. It also creates a stable bridge for future agent orchestration and step-by-step debugging.

### Implemented safe notebook sidecar

Implemented the first notebook integration behind a feature flag.

Changes made:

- Added `notebook_export.py`.
  - Builds renderable `.ipynb` notebooks with `nbformat`.
  - Includes dataset context, dataframe preview, semantic understanding, metric plan, generated pandas code, executed metric outputs, dashboard plan, validation report, critic notes, analytical brain output, and reproducibility details.
  - Embeds captured outputs as notebook code-cell outputs instead of executing notebook code in the app.
- Added `NOTEBOOK_DIR = artifacts/notebooks`.
- Added `ENABLE_NOTEBOOK_VIEW` feature flag.
  - Default is disabled.
  - Truthy values: `1`, `true`, `yes`, `on`.
- Added optional `Notebook` tab in the Streamlit app only when the flag is enabled.
- Added notebook artifact rendering in the app.
  - Markdown cells render as markdown.
  - Code cells render as Python code.
  - HTML/text outputs render below code cells.
  - Notebook download button provides the `.ipynb`.
- Added notebook generation after successful dashboard generation.
  - Generation is non-blocking: notebook errors are logged and do not fail the dashboard.
  - Notebook generation uses existing saved pipeline artifacts and sandboxed metric outputs.
- Added notebook restore support from saved dashboard artifacts.
- Added `nbformat` to `requirements.txt`.
- Added `ENABLE_NOTEBOOK_VIEW=false` to `.env.example`.

Tests added:

- `tests/test_notebook_export.py`
  - Validates notebook structure.
  - Confirms DataFrame, Series, and scalar outputs are represented.
  - Confirms written `.ipynb` is valid JSON notebook format.
- `tests/test_notebook_feature_flag.py`
  - Confirms notebook view is disabled by default.
  - Confirms explicit truthy/falsey values behave correctly.

Verification:

- `python -m py_compile app.py notebook_export.py agents/metric_code_planner.py agents/dashboard_planner.py agents/dashboard_critic.py agents/analytical_brain.py dashboard_validation.py` passes.
- `python -m unittest discover -s tests` passes: 23 tests.
- Streamlit AppTest smoke check passes with notebook disabled: 0 exceptions.
- Streamlit AppTest smoke check passes with `ENABLE_NOTEBOOK_VIEW=true`: 0 exceptions.
- `Invoke-WebRequest http://localhost:8501` returns 200.

Reason: The notebook layer is an observer sidecar, not a participant in the core dashboard pipeline. The feature flag and non-blocking generation keep the current app path safe while adding an audit trail when enabled.

### Enabled notebook feature flag locally

Enabled notebook view for the local app.

Changes made:

- Set `ENABLE_NOTEBOOK_VIEW=true` in local `.env` without printing or modifying secrets.
- Updated `app.py` startup to call `load_dotenv(dotenv_path=".env")` so app-level feature flags are loaded before rendering tabs.

Verification:

- Confirmed `notebook_view_enabled()` returns `True` after loading `.env`.
- `python -m unittest discover -s tests` passes: 23 tests.
- Streamlit AppTest smoke check passes: 0 exceptions.

Reason: The feature flag existed, but the app needed to load `.env` at startup for the Notebook tab to appear reliably.

### Fixed current dashboard and notebook rendering issues

Investigated the current Dubai real estate dashboard and notebook output.

Findings:

- The dashboard validation report was `failed` because an unused metric output, `listing_counts_over_time`, declared wide columns (`n_listings_secondary`, `n_listings_offplan`, `n_listings_rental`) but the executed code produced a long-form output (`year_month`, `listing_type`, `listing_count`).
- The actual dashboard used `listing_counts_time_series`, not the stale `listing_counts_over_time` output, so the unused output contract drift should not fail the rendered dashboard.
- The app showed a success message even when validation status was `failed`.
- The notebook appeared to show only metadata because the first Dataset Context section embedded a huge raw metadata JSON object, including long `unique_values` lists.
- The “Top Communities by Avg Rental Price” chart was visually broken because horizontal bar rendering swapped x/y a second time. The dashboard spec already had numeric value on `x` and category on `y`; the renderer inverted it into `x=community`, `y=price`.

Changes made:

- Updated dashboard validation so unused metric-output schema drift is a warning, while referenced output drift still fails dashboard validation.
- Updated dashboard generation feedback:
  - `failed` -> warning
  - `passed_with_warnings` -> warning
  - `passed` -> success
- Compacted notebook metadata:
  - Dataset Context now uses compact metadata.
  - Added a `metadata_columns` output table.
  - Removed huge raw `unique_values` dumps from the rendered notebook.
- Rebuilt the current Dubai validation artifact and notebook artifact from saved pipeline state without rerunning agents.
- Fixed horizontal bar rendering so numeric fields stay on x and category labels stay on y.
- Added `tests/test_chart_rendering_contracts.py`.
- Added regression coverage for unused metric-output schema drift.

Verification:

- Recomputed current Dubai validation status: `passed_with_warnings`.
- Rebuilt current Dubai notebook: 39 cells, no raw `unique_values` dump.
- `python -m unittest discover -s tests` passes: 25 tests.
- Streamlit AppTest smoke check passes: 0 exceptions.
- `Invoke-WebRequest http://localhost:8501` returns 200.

Reason: Dashboard validation should distinguish between broken rendered outputs and stale unused declarations. The notebook should explain the pipeline without burying the user in raw metadata. Horizontal bar rendering must respect the dashboard spec's axis contract.

### Fixed clipped line chart scales

Investigated the overview chart "Secondary Price per Sqft Over Time".

Finding:

- The metric output had 76 monthly rows from `2020-01` through `2026-04`.
- The dashboard chart spec manually set `value_axis_min=300` and `value_axis_max=380`.
- Actual secondary prices later rise above `580`, so Plotly clipped most of the line outside the visible y-axis range.
- The chart therefore showed only a small visible slice, making it look like the data ended around 2021.
- The listing-count overview had the same class of issue: axis max was `9000`, while the data reached `9087`.

Changes made:

- Added validation that declared chart scales must not clip actual plotted values.
- Added a regression test for line charts whose declared y-axis range hides data.
- Removed manual scales from the current Dubai overview charts and rebuilt the saved dashboard validation + notebook artifacts.

Verification:

- Current Dubai validation status is now `passed_with_warnings`.
- Remaining warning is only the unused metric-output schema drift for `listing_counts_over_time`.
- `python -m unittest discover -s tests` passes: 26 tests.
- Streamlit AppTest smoke check passes: 0 exceptions.

Reason: Axis narrowing can be useful for tightly clustered data, but it must never silently hide part of the series. If a scale clips values, the validator should reject it before the dashboard renders.

### Checked phishing rate chart code

Investigated the "Phishing Rate by Email Subject" chart.

Finding:

- The chart uses `source_output_key="phishing_rate_by_subject"`.
- Generated metric code groups by `subject`, counts total emails, sums `is_phishing`, and computes `phishing_rate = phishing_count / email_count`.
- Executed output has 10 subjects:
  - 5 subjects have phishing rate `1.0`.
  - 5 subjects have phishing rate `0.0`.
- The dashboard chart uses `top_n=10`, so it includes all subjects. The zero-rate subjects render as bars with height zero, leaving only rotated labels on the x-axis.

Interpretation:

- The calculation is not broken; it reflects a very strong synthetic relationship between subject lines and the phishing label.
- The visualization is awkward because zero-height bars are visually absent while labels remain.
- A better dashboard treatment would show the top phishing subjects plus `email_count`/`phishing_count`, or use a table for all subjects with counts and rates.

Reason: The issue is chart usefulness rather than code execution. The model selected a technically valid bar chart, but the binary 0/1 pattern makes the output look strange without counts or a table.

### Planned UI overhaul

Goal: Move Dashboard Studio from a generic Streamlit prototype into a polished analytics product UI while preserving the current Python agent pipeline.

Diagnosis:

- Streamlit is useful for fast internal tools, but it makes it hard to build a distinctive product interface, precise layout, rich navigation, custom chart interactions, and resilient frontend state.
- The current UI also feels generic because it uses broad tabs, repeated bordered containers, default chart rendering, visible artifact/debug language, and limited workflow hierarchy.
- The core product needs to feel like an analytical workspace: clear source state, agent progress, dashboard output, notebook/audit trail, validation, and history should be organized as first-class product surfaces.

Recommended architecture:

- Keep Python as the analytics and agent backend.
- Add a real frontend app:
  - Next.js + React + TypeScript for the product shell.
  - Tailwind CSS for layout primitives.
  - Radix UI or shadcn/ui for accessible controls, dialogs, tabs, menus, sheets, and command surfaces.
  - TanStack Query for server state and artifact polling.
  - Zustand or Jotai for local UI state.
  - Apache ECharts, Vega-Lite, or Plotly.js for richer chart rendering. Prefer a declarative chart schema so dashboard plans can map cleanly into frontend charts.
- Add a Python API layer:
  - FastAPI exposes dataset upload/import, semantic generation, dashboard generation, job status, artifacts, notebook JSON, validation, and history.
  - Streamlit can remain as an internal/debug shell during migration.

Product redesign direction:

- App shell:
  - Left rail for datasets/history/jobs.
  - Top bar with source status, run state, validation state, and export actions.
  - Main workspace with tabs or segmented views: Dataset, Understanding, Dashboard, Insights, Notebook, Artifacts.
- Dashboard page:
  - Less “card stack,” more analytical report layout.
  - KPI strip only when values are genuinely important.
  - Chart sections grouped by analytical purpose, not agent internals.
  - Chart footers should show concise scale/sample-size/data-quality caveats.
  - Validation warnings should be integrated near affected charts, not hidden in logs.
- Notebook page:
  - Render notebook cells as an audit trail, but visually designed like a readable analysis document.
  - Collapsible generated-code cells.
  - Outputs displayed as tables/charts with consistent styling.
- Agent activity:
  - Use a run timeline: Dataset parsed, semantic agent, metric planner, dashboard planner, critic, analytical brain, notebook artifact.
  - Persist job state and make reusing history obvious.
- Visual style:
  - Quiet operational UI, not a marketing page.
  - High contrast text, restrained neutral background, one strong action color, semantic status colors.
  - Compact typography and stable chart dimensions.
  - Avoid default Streamlit visuals, oversized empty space, generic bordered cards, and raw artifact labels in the main user path.

Safe migration plan:

1. Define frontend-facing API contracts from existing artifacts.
   - Dataset metadata.
   - Semantic understanding.
   - Metric plan summary.
   - Dashboard plan.
   - Validation report.
   - Analytical insights.
   - Notebook cells.
2. Build FastAPI read-only endpoints first.
   - Serve existing artifacts without changing generation.
   - Add tests for API payloads.
3. Build Next.js shell against existing artifacts.
   - No generation actions at first.
   - Dashboard and notebook are read-only.
4. Add job actions.
   - Upload/import dataset.
   - Generate understanding.
   - Generate dashboard.
   - Poll job status.
5. Move chart rendering to frontend.
   - Start with bars, lines, tables, KPIs.
   - Add validation-aware chart guards before rendering.
6. Keep Streamlit available behind an internal/dev command until the React frontend is stable.

Reason: The UI should become a product-grade analytical workspace while the proven Python agent pipeline remains intact. Separating frontend and backend gives us design freedom without destabilizing data generation.

### UI overhaul priority ladder

Divided the product UI overhaul into implementation priority levels.

Critical:

- Establish a stable frontend-facing API contract over existing artifacts.
- Keep Streamlit working while a new frontend is developed.
- Do not change generation behavior yet.
- Expose runs, latest run bundle, dashboard plan, validation, insights, and notebook data through read-only endpoints.
- Add tests so a future React/Next.js frontend does not depend on private Streamlit state.

High:

- Build a Next.js + React + TypeScript product shell.
- Add an app frame with left rail, top status bar, run history, and main workspace.
- Render existing dashboard plans from API payloads.
- Render notebook/audit trail from API notebook JSON.
- Add frontend chart guards for invalid specs, missing data, clipped scales, zero-only bars, and sample-size caveats.

Medium:

- Add generation actions to the frontend.
- Introduce job status polling for semantic, metric, dashboard, critic, analytical brain, and notebook steps.
- Add richer history and artifact comparison.
- Improve chart interaction: tooltips, sorting, table fallback, value labels, export controls.

Low:

- Visual refinement, transitions, empty states, keyboard shortcuts, command palette, theme tokens, and polish.
- Replace Streamlit fully only after the new frontend covers current workflows.

### Implemented critical UI-overhaul foundation

Implemented the critical first slice: a read-only FastAPI contract over current artifacts.

Changes made:

- Added `api.py`.
  - `GET /api/health`
  - `GET /api/runs`
  - `GET /api/runs/latest`
  - `GET /api/runs/{run_id}`
  - `GET /api/runs/{run_id}/notebook`
- Added `ArtifactStore` abstraction so tests can use temporary artifact roots.
- Added typed response models:
  - `ArtifactStatus`
  - `RunSummary`
  - `RunBundle`
- Added CORS for local frontend development on `localhost:3000`.
- Added `fastapi` and `uvicorn` to `requirements.txt`.
- Added `tests/test_api_contracts.py`.

Verification:

- `python -m unittest tests.test_api_contracts` passes.
- `python -m py_compile api.py` passes.

Reason: A product-grade frontend needs stable artifact APIs before we build visual surfaces. This keeps the UI overhaul decoupled from agent execution and reduces the chance of breaking the current app.

### Documentation priority ladder

Classified documentation work into the same priority model as the UI overhaul.

Critical:

- Rewrite `README.md` so a beginner can understand, install, run, and troubleshoot the project.
- Add a detailed introduction page explaining objective, architecture, agent communication, artifacts, validation, notebook audit trail, and UI-overhaul direction.
- Include setup commands for Streamlit, FastAPI, tests, Kaggle, and notebook feature flag.

High:

- Add API reference documentation with example payloads.
- Add agent schema reference for each structured input/output model.
- Add dashboard validation rule reference.
- Add notebook artifact guide.

Medium:

- Add contributor guide.
- Add troubleshooting guide with known errors and fixes.
- Add end-to-end example walkthroughs using saved Kaggle datasets.
- Add architecture decision records for major design choices.

Low:

- Add screenshots, demo GIFs, polished diagrams, branding copy, and a docs site.

### Implemented critical documentation foundation

Implemented the critical documentation slice.

Changes made:

- Rewrote `README.md` as a beginner-friendly guide.
  - Explains what Dashboard Studio does.
  - Includes project structure.
  - Includes setup and run instructions.
  - Includes `.env`, OpenAI, Kaggle, notebook flag, Streamlit, FastAPI, tests, artifacts, and troubleshooting.
  - Explains current branches and development direction.
- Added `docs/project-introduction.md`.
  - Covers objective, product promise, architecture, agent workflow, artifact flow, validation, notebook purpose, UI-overhaul direction, and success criteria.
  - Includes Mermaid diagrams for pipeline flow, agent communication, artifact flow, and future frontend architecture.
  - Includes UI-overhaul and documentation priority ladders.

Reason: The project has grown from a simple Streamlit prototype into a multi-agent analytics system. The docs need to help beginners run it while also helping future contributors understand the architecture.

### Implemented high-priority read-only frontend shell

Started the high-priority UI overhaul work after completing the critical API contract.

Changes made:

- Added `frontend/` Next.js app.
  - React + TypeScript.
  - TanStack Query for API state.
  - Lucide icons.
  - Custom CSS product shell.
- Added read-only views:
  - Run history sidebar.
  - Top status bar with validation, row count, notebook availability.
  - Dashboard plan view with KPI cards, overview chart specs, and question views.
  - Insights view with analytical brain output and validation issues.
  - Notebook preview from `.ipynb` JSON.
  - Artifact availability view.
- Added frontend API client for:
  - `/api/runs`
  - `/api/runs/latest`
  - `/api/runs/{run_id}`
  - `/api/runs/{run_id}/notebook`
- Updated `.gitignore` to exclude `.next/`.
- Added frontend run instructions to `README.md`.
- Updated `docs/project-introduction.md` with high-priority frontend progress.

Verification:

- `npm.cmd install` completed in `frontend/`.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- `.\.venv\Scripts\python.exe -m unittest discover -s tests` passes: 31 tests.
- Started FastAPI on `http://localhost:8000`; `/api/health` returns 200.
- Started Next.js frontend on `http://localhost:3000`; HTTP request returns 200.
- `/api/runs/latest` returns the latest artifact bundle.
- Added Playwright end-to-end tests for dashboard, insights, notebook, artifacts, and mobile states.
- `npm.cmd run test:e2e` passes: 5 browser tests.
- Screenshots saved in `frontend/test-results/screenshots/`.

Notes:

- npm reported two moderate advisories in the JavaScript dependency tree. Did not run forced upgrades because that can introduce breaking changes.
- Browser screenshots are now generated through Playwright test runs and ignored by git as runtime artifacts.

Reason: The first product frontend should be read-only and artifact-backed. This lets us improve the UI without changing or risking the agent generation pipeline.

### Added Desktop launcher shortcut support

Added `scripts/launch_dashboard_studio.ps1` as a one-click launcher target.

Behavior:

- Starts the FastAPI artifact API on `127.0.0.1:8000` when it is not already running.
- Installs frontend dependencies if `frontend/node_modules` is missing.
- Starts the Next.js frontend on `127.0.0.1:3000` when it is not already running.
- Opens the browser to the frontend.
- Writes launcher logs to `artifacts/logs/shortcut-*.log`.

Reason: A Desktop shortcut should open the app directly instead of requiring a beginner to remember the separate API and frontend commands.

### Restored source import workflow in the new frontend

The first Next.js shell was read-only, so upload and Kaggle import were still only available in Streamlit. Added those source entry points to the new UI.

Changes made:

- Added FastAPI ingestion endpoints:
  - `POST /api/datasets/upload`
  - `POST /api/datasets/kaggle`
- Added run artifact creation for uploaded/imported CSV files.
- Added a `Source` tab in the Next.js frontend.
- Added upload form for local CSV files.
- Added Kaggle import form for dataset reference, optional CSV filename, and extra context.
- Added API contract tests for upload and Kaggle ingestion.
- Added Playwright coverage and screenshot for the Source tab.

Verification:

- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- `.\.venv\Scripts\python.exe -m unittest discover -s tests` passes: 33 tests.
- `npm.cmd run test:e2e` passes: 6 browser tests.
- Restarted the local API and confirmed `POST /api/datasets/upload` is registered.

Reason: The new product frontend needs the same first-mile dataset workflow as the old Streamlit app; otherwise users land in a read-only artifact viewer with no obvious way to start.

### Added generation actions and job polling to the new frontend

Continued the UI-overhaul work by letting the Next.js frontend start the saved-run dashboard pipeline through FastAPI.

Changes made:

- Added FastAPI job models and an in-memory `JobManager`.
- Added `POST /api/runs/{run_id}/generate`.
  - Starts the semantic, metric, dashboard, validation, insights, and optional notebook pipeline for an existing saved run.
  - Uses the saved dataset artifact instead of Streamlit session state.
  - Writes artifacts through the FastAPI `ArtifactStore` paths.
- Added `GET /api/jobs/{job_id}` for polling queued/running/completed/failed status.
- Added frontend API client methods for generation and job polling.
- Added a top-level generation action bar in the Next.js app.
  - Shows artifact count before generation.
  - Shows live stage/status while a generation job is running.
  - Refreshes run, history, and notebook queries when the job completes.
- Added API contract coverage for the generation endpoint with a fake generation runner.
- Updated README and project introduction docs with the new endpoints and frontend behavior.

Verification:

- `python -m py_compile api.py` passes.
- `python -m unittest tests.test_api_contracts` passes: 8 tests.
- `python -m unittest discover -s tests` passes: 34 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- FastAPI started on `http://127.0.0.1:8000`; `/api/health` returns 200.
- Next.js started on `http://127.0.0.1:3000`; HTTP request returns 200.
- `npm.cmd run test:e2e` passes: 6 browser tests.

Note:

- Attempted an additional Codex in-app browser check, but the Browser plugin did not expose an `iab` browser in this session. Playwright still verified the rendered local frontend.

Reason: The product frontend now has a real path from dataset run to generated dashboard artifacts, rather than relying on Streamlit for all agent execution. Job polling gives the frontend a stable contract for long-running agent work.

### Added shared contract layer for agent handoffs

Implemented the first contract-layer pass so agents and deterministic pipeline steps share one canonical schema language.

Changes made:

- Added a new `contracts/` package.
  - `contracts/base.py` defines `CONTRACT_LAYER_VERSION`, stable schema ids, and an optional future artifact envelope.
  - `contracts/semantic.py` owns `SemanticUnderstanding`.
  - `contracts/metrics.py` owns metric planning specs and `PandasMetricPlan`.
  - `contracts/dashboard.py` owns dashboard KPI/chart/question specs and `DashboardPlan`.
  - `contracts/validation.py` owns `ValidationIssue` and `DashboardValidationReport`.
  - `contracts/critique.py` owns `DashboardCritique`.
  - `contracts/insights.py` owns analytical brain input/result contracts.
- Updated agents, validator, app orchestration, and notebook export so production handoff types come from `contracts`.
- Preserved old import paths by re-exporting contract models from the existing agent and validation modules.
- Added `scripts/export_contract_schemas.py`.
- Exported JSON Schemas to `docs/contracts/schemas/`.
- Added `docs/contracts/agent-contracts.md` explaining producers, consumers, artifacts, and schema files.
- Updated README and project introduction docs to mention the shared contract layer.
- Added `tests/test_contract_layer.py`.

Cohesion checks:

- Production agent code no longer imports shared handoff models from sibling agent modules.
- Agent modules still keep old public imports working for compatibility.
- Contract modules import without loading LangChain/OpenAI clients.
- Sample semantic, metric, dashboard, validation, critique, and insight payloads validate through the new contract package.

Verification:

- `python -m py_compile contracts\__init__.py contracts\base.py contracts\semantic.py contracts\metrics.py contracts\dashboard.py contracts\validation.py contracts\critique.py contracts\insights.py agents\semantic_understanding.py agents\metric_code_planner.py agents\dashboard_planner.py agents\dashboard_critic.py agents\analytical_brain.py dashboard_validation.py notebook_export.py app.py scripts\export_contract_schemas.py` passes.
- `python -m unittest tests.test_contract_layer` passes: 4 tests.
- `python -m unittest discover -s tests` passes: 38 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.

Reason: The agents already had structured outputs, but the definitions were scattered across agent modules. Centralizing the contracts makes every handoff explicit and keeps semantic understanding, metric planning, dashboard planning, validation, critique, and insight generation speaking the same language.

### Rendered frontend dashboards from analysis outputs

Fixed the new frontend's dashboard view so it can render actual computed metric outputs instead of only showing dashboard plan specifications.

Changes made:

- Added `analysis_outputs` to FastAPI artifact status and run bundles.
- Added `artifacts/analysis_outputs/*_analysis_outputs.json` as a compact serialized metric-output artifact.
- Added serializer helpers for DataFrame, Series, dict, list, tuple, and scalar analysis outputs.
- Updated dashboard generation to write serialized analysis outputs after metric execution.
- Updated frontend API types to include serialized analysis outputs.
- Replaced spec-only dashboard cards with rendered views when output data is available:
  - KPI cards calculate visible values from scalar, mapping, or table outputs.
  - Bar/histogram specs render compact bar views.
  - Line/multi-line specs render compact SVG line previews.
  - Scatter specs render compact point previews.
  - Table/text/KPI specs render data tables.
  - Missing output data still falls back to the spec card, which is useful for debugging stale or incomplete artifacts.
- Updated artifact counts to use the actual artifact key count instead of a hard-coded total.
- Added a rigorous mocked Playwright test proving that when the API provides `analysis_outputs`, the frontend renders `.renderedChart` and bar marks instead of `.chartSpec` fallback cards.
- Updated README, project introduction docs, and contract docs to mention analysis-output artifacts and rendered frontend previews.

Verification:

- `python -m unittest tests.test_api_contracts` passes: 9 tests.
- `python -m unittest discover -s tests` passes: 39 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- `npm.cmd run test:e2e` passes: 7 browser tests.

Reason: The Next.js dashboard previously looked like a finished dashboard but only displayed the dashboard plan's chart contracts. Persisting compact analysis outputs and rendering them in the frontend closes the loop from agent planning to computed data to visible dashboard output.

### Cleaned generated runtime state for a fresh start

Removed stale generated runtime files so future runs start against the current contract/API/frontend shape.

Cleaned:

- `artifacts/` runtime outputs, leaving a fresh `artifacts/logs/` directory.
- `frontend/.next/`.
- `frontend/test-results/`.
- Python `__pycache__/` directories under the project, tests, agents, and contracts.

Stopped local listeners on ports `3000`, `8000`, and `8501` first because the Next.js dev server had locked files under `.next`.

Preserved:

- Source code.
- Documentation.
- Tests.
- `.env`.
- `.venv`.
- `frontend/node_modules/`.
- `worklog.md`.

Verification:

- `artifacts/` now contains only `artifacts/logs/`.
- Removed frontend build/test output directories are absent.
- Removed Python cache directories are absent.

Reason: Historical artifacts were produced by older pipeline shapes and no longer represented the current system. Clearing generated state avoids confusing the new frontend renderer and contract layer with stale saved runs.

### Hardened Kaggle CSV Import Edge Cases

Fixed Kaggle imports where the API lists a CSV such as `train.csv` but downloads it as `train.csv.zip`.

Changes made:

- Normalized Kaggle download handling so `fetch_kaggle_dataset()` returns real CSV bytes whether Kaggle provides a plain CSV, a listed `.csv.zip`, or a CSV nested inside a downloaded zip.
- Extracted downloaded zip files into isolated `_extracted` folders instead of the download root.
- Matched selected files using normalized Kaggle-style paths, basenames, and `.zip`-stripped names.
- Skipped unsafe zip members with absolute paths, empty path parts, `.` parts, or `..` traversal.
- Added `tests/test_kaggle_import.py` with mocked Kaggle API coverage for zipped CSVs, nested CSV members, multiple CSV members, unsafe zip paths, and listed `.csv.zip` selection.
- Updated README troubleshooting to document zipped Kaggle CSV support.

Verification:

- `python -m py_compile app.py tests\test_kaggle_import.py` passes.
- `python -m unittest tests.test_kaggle_import` passes: 5 tests.
- `python -m unittest discover -s tests` passes: 44 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- Live smoke test for `rohitsahoo/sales-forecasting` now selects `train.csv`, extracts `train.csv.zip`, and returns 2,129,689 bytes from `train.csv`.

Reason: Kaggle's file API can list a CSV contract while `dataset_download_file()` materializes a zip on disk. Normalizing that boundary keeps the rest of the pipeline speaking the same language: a selected Kaggle dataset file becomes CSV bytes before metadata, analysis, dashboard planning, or frontend rendering touch it.

### Modularized backend core out of app.py

Refactored the current Streamlit app so shared backend behavior now lives in focused `core/` modules instead of being defined inside `app.py`.

Changes made:

- Added `core/` as the canonical backend package.
  - `core/config.py` owns artifact directory constants and feature flags.
  - `core/csv_io.py` owns CSV fallback parsing and named byte-file helpers.
  - `core/kaggle_import.py` owns Kaggle refs, file selection, zip extraction, metadata text, and imports.
  - `core/dataset_metadata.py` owns dataframe profiling, metadata contracts, dataframe context, and data-integrity summaries.
  - `core/artifacts.py` owns artifact path builders and save helpers.
  - `core/metric_execution.py` owns generated-code sanitization, validation, execution, and metric-plan repair.
  - `core/pipeline.py` owns dashboard planning, validation, and critic repair orchestration.
- Updated `api.py` so FastAPI generation and Kaggle imports use `core.*` directly instead of importing backend helpers from `app.py`.
- Kept `app.py` as the Streamlit UI shell and compatibility surface.
- Preserved old imports such as `from app import fetch_kaggle_dataset`, `sanitize_generated_code`, `failed_metric_plan_path_for`, and `notebook_view_enabled`.
- Updated README and project introduction docs to describe `core/` as the backend home.

Regression coverage added:

- Module-boundary tests prove `core.*` imports without importing Streamlit and `api.py` does not import `app.py`.
- CSV ingestion tests cover default parsing, delimiter fallback, malformed rows, invalid input, and named byte files.
- Kaggle tests now cover URL normalization, invalid refs, basename matching, listed `.csv.zip`, downloaded zip extraction, nested CSVs, Windows-style zip member paths, multiple CSV preference, unsafe paths, and missing CSV failure.
- Dataset metadata tests cover inferred roles, stats/nulls/samples/top values, representative values, metadata fields, dataframe context, and integrity summaries.
- Artifact tests cover path builders, metadata index deduplication, dataset writes, model JSON saves, failed metric plans, and notebook writes.
- Metric execution tests cover sanitizer behavior, unsafe-code rejection, safe execution, missing/non-dict outputs, repair loop behavior, final failure, and persisted failed attempts.
- Pipeline tests cover planner/validator/critic flow for passing and repaired dashboards.
- Compatibility tests prove old `app.py` imports still resolve.

Verification:

- `python -m py_compile app.py api.py core\__init__.py core\config.py core\csv_io.py core\kaggle_import.py core\dataset_metadata.py core\artifacts.py core\metric_execution.py core\pipeline.py` passes.
- `python -m unittest discover -s tests` passes: 74 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.

Reason: `app.py` had become the dependency hub for Streamlit UI, ingestion, artifacts, metadata, generated-code execution, and pipeline orchestration. Moving backend responsibilities into platform-neutral `core` modules gives FastAPI, tests, and future frontend work a clean backend surface while keeping the Streamlit app working.

### Added contract validation at agent boundaries

Wrapped agent handoff boundaries with Pydantic `.model_validate()` through a shared `validate_contract()` helper.

Changes made:

- Added `validate_contract()` to `contracts/base.py`.
- Validated raw agent outputs before returning from:
  - semantic understanding generation
  - metric plan generation
  - metric plan repair
  - dashboard plan generation
  - dashboard critique repair
  - analytical brain input/result generation
- Validated upstream contract inputs before agents serialize them into downstream prompts.
- Validated metric plans in generated-code execution and repair loops.
- Validated dashboard plans, validation reports, and critiques in the dashboard orchestration pipeline.
- Validated deterministic dashboard validation inputs and final validation reports.
- Added tests proving raw dict payloads from agent and validator boundaries are normalized into the canonical contract models.

Why this is required:

- LLM structured output usually returns a Pydantic object, but provider/tooling changes, tests, repairs, stale artifacts, and future adapters can hand back dict-like payloads.
- `.model_validate()` makes every handoff explicit: downstream agents receive contract-confirmed objects, not hopeful shapes.
- This keeps the contract layer meaningful as the shared language between semantic understanding, metric planning, dashboard planning, validation, critique, and insights.

Verification:

- `python -m py_compile contracts\base.py agents\semantic_understanding.py agents\metric_code_planner.py agents\dashboard_planner.py agents\dashboard_critic.py agents\analytical_brain.py core\metric_execution.py core\pipeline.py dashboard_validation.py` passes.
- `python -m unittest tests.test_agents_contracts tests.test_contract_layer tests.test_metric_execution tests.test_core_pipeline tests.test_dashboard_contract_validation` passes: 27 tests.
- `python -m unittest discover -s tests` passes: 80 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.

Reason: The system now fails fast at agent and deterministic boundary edges when a handoff violates the shared contract language, instead of letting shape drift surface later as rendering, validation, or notebook errors.

### Added agent timeout guardrails and compact dataframe context

Diagnosed a run that appeared stuck at the metrics stage after importing the UFC Kaggle dataset.

What happened:

- The run successfully wrote metadata, dataset, and semantic artifacts.
- No metric-plan or analysis-output artifacts were written.
- Replaying the metric step in the foreground did not return within several minutes, which pointed to an unbounded metric-planner LLM call rather than a deterministic pandas execution error.
- The UFC dataframe context was materially larger than the prior sales run because it had more columns, a long description, and richer categorical summaries.

Changes made:

- Added shared OpenAI client guardrails in `agents/semantic_understanding.py`:
  - `DEFAULT_LLM_TIMEOUT_SECONDS = 90.0`
  - `DEFAULT_LLM_MAX_RETRIES = 1`
  - `OPENAI_TIMEOUT_SECONDS` and `OPENAI_MAX_RETRIES` environment overrides.
- Applied those timeout/retry settings to semantic, metric planning, metric repair, dashboard planning, dashboard critique, and analytical insight agents.
- Added compact agent context helpers in `core/dataset_metadata.py`.
  - Long descriptions are truncated for prompts.
  - Very large unique/sample lists are trimmed.
  - Column names, roles, nulls, stats, top values, and representative values remain available.
- Restarted the API cleanly from the project `.venv` so runtime dependencies match tests.

Why this helps:

- Timeout does not make the metric agent smarter; it prevents a slow provider/tool call from holding the job forever.
- Compact context reduces token pressure and makes the metric planner less likely to stall.
- A better future architecture is to split metric planning into smaller stages and allow partial metric outputs, but this pass keeps behavior compatible while adding a bounded failure mode.

Verification:

- `.venv\Scripts\python.exe -m py_compile agents\semantic_understanding.py agents\metric_code_planner.py agents\dashboard_planner.py agents\dashboard_critic.py agents\analytical_brain.py core\dataset_metadata.py tests\test_agents_contracts.py tests\test_dataset_metadata.py` passes.
- `.venv\Scripts\python.exe -m unittest tests.test_dataset_metadata tests.test_agents_contracts` passes: 18 tests.
- `.venv\Scripts\python.exe -m unittest discover -s tests` passes: 85 tests.
- `git diff --check` reports only existing CRLF conversion warnings, no whitespace errors.

### Audited long-running and misleading failure boundaries

Performed a reliability audit focused on issues like the metrics-stage hang and runs showing failed/stuck while partial artifacts exist.

Findings:

- Metric agent calls now have LLM timeouts, but failed metric attempts from the FastAPI generation path were not being persisted because `metadata=None` was passed to metric execution.
- Generated metric code could still contain `while` loops, which created an obvious infinite-execution risk even with safe imports blocked.
- API generation swallowed optional insights/notebook failures without server logs.
- Job failures returned a failed status to the frontend but did not log backend tracebacks, making diagnosis depend on reproducing the issue manually.
- FastAPI dataset ingestion still used a local `pd.read_csv` and simplified metadata builder instead of the canonical `core.csv_io` and `core.dataset_metadata` path.
- The frontend artifact contract was missing `analysis_outputs`.
- Failed jobs did not invalidate the run bundle, so partial artifacts written before failure could be invisible until a manual refresh.
- Switching runs could leave the previous job status visible in the action bar.

Fixes made:

- FastAPI now passes run metadata into `generate_executable_metric_plan()` so failed metric-plan attempts can be saved.
- Generated metric code validation now rejects `while` loops.
- API job failures, optional insights failures, and optional notebook failures are logged with tracebacks.
- FastAPI dataset saves now use `read_csv_with_fallbacks()` and `build_dataset_metadata()` from `core`.
- API upload coverage now proves semicolon-delimited CSVs parse through the same core fallback path and receive rich metadata.
- Frontend `ArtifactStatus` now includes `analysis_outputs`.
- Frontend API errors now unwrap FastAPI `detail` messages instead of showing raw JSON blobs.
- Frontend job completion and failure both invalidate run data so artifact status catches up.
- Frontend clears old job state when the selected run changes.

Verification:

- `.venv\Scripts\python.exe -m py_compile api.py core\metric_execution.py tests\test_api_contracts.py tests\test_metric_execution.py` passes.
- `.venv\Scripts\python.exe -m unittest tests.test_api_contracts tests.test_metric_execution tests.test_csv_ingestion tests.test_dataset_metadata` passes: 28 tests.
- `.venv\Scripts\python.exe -m unittest discover -s tests` passes: 87 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- `git diff --check` reports only existing CRLF conversion warnings, no whitespace errors.

Remaining architecture note:

- The more robust long-term fix is to split metric planning into smaller stages: metric specs first, code generation per output or output group, independent execution, and partial successful artifacts. That would make one slow or bad metric less likely to block the whole dashboard, but it is a larger pipeline contract change.

### Added structured run tracing

Implemented durable run-scoped tracing so generation runs can be inspected from artifacts/API/frontend without manually reading logs.

Changes made:

- Added `core/run_tracing.py`.
  - Defines `RunTrace` and `RunTraceEvent`.
  - Writes incremental trace JSON to `artifacts/traces/{run_id}_trace.json`.
  - Supports running, completed, warning, failed, and skipped events.
  - Trace writes are best-effort and log failures without killing generation.
- Added `core/run_orchestration.py`.
  - Moved FastAPI dashboard-generation orchestration out of `api.py`.
  - Wraps generation stages in trace events:
    - dataset context
    - semantic understanding
    - metrics
    - dashboard planning/validation
    - critic repair
    - insights
    - notebook
    - complete
  - Required stage failures mark the trace failed and re-raise.
  - Optional insights/notebook failures become warning events.
  - Critic repair attempts are surfaced through a lightweight callback from `core.pipeline`.
- Added trace artifact path support.
  - `ArtifactStatus` now includes `trace`.
  - Run bundles now include `trace` when present and `null` for older runs.
  - Added `GET /api/runs/{run_id}/trace`.
- Updated frontend API types and Artifacts tab.
  - Added `RunTrace` and `RunTraceEvent` types.
  - Artifacts inventory now includes trace status.
  - Artifacts view renders a run trace timeline with status, duration, messages, errors, and produced artifact labels.
  - Older runs show “No trace artifact for this run.”
- Stabilized frontend e2e tests by routing screenshot tests to a complete mocked run instead of relying on whichever local artifact is currently latest.

Verification:

- `.venv\Scripts\python.exe -m py_compile api.py core\config.py core\artifacts.py core\pipeline.py core\run_tracing.py core\run_orchestration.py tests\test_run_tracing.py tests\test_api_contracts.py tests\test_core_artifacts.py tests\test_core_boundaries.py` passes.
- `.venv\Scripts\python.exe -m py_compile api.py core\*.py` equivalent using PowerShell-expanded file list passes.
- `.venv\Scripts\python.exe -m unittest tests.test_run_tracing tests.test_api_contracts tests.test_core_artifacts tests.test_core_boundaries tests.test_core_pipeline` passes: 28 tests.
- `.venv\Scripts\python.exe -m unittest discover -s tests` passes: 92 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- `npm.cmd run test:e2e` passes: 8 tests.
- `git diff --check` reports only existing CRLF conversion warnings, no whitespace errors.

Reason: Job polling is ephemeral and logs are not run-scoped enough for product debugging. The trace artifact gives each run a durable timeline that shows partial success, optional warnings, required failures, and produced artifacts in the same language as the rest of the pipeline.

### Stitched dashboard critic repair boundary after failed run

Investigated a failed Kaggle dashboard generation run for `rohitsahoo/sales-forecasting`.

What happened:

- Kaggle import succeeded.
- Semantic understanding succeeded.
- Metric planning and metric execution succeeded.
- The run failed during dashboard critic repair.
- The critic returned a repaired dashboard chart with `orientation: null`.
- The new contract validation correctly rejected that payload because `orientation` must be `"vertical"` or `"horizontal"`.

Fixes made:

- Updated `DashboardChartSpec` to normalize `null` values for fields that already have safe defaults:
  - `orientation: null` becomes `"vertical"`.
  - `sort_order: null` becomes `"descending"`.
  - `metrics: null` becomes `[]`.
- Updated dashboard pipeline repair handling so critic repair is optional resilience, not a hard dependency.
  - If critic repair still returns an invalid payload, the pipeline logs the failure.
  - The original dashboard plan and validation report are kept and saved instead of aborting the run.
- Added regression tests for null chart defaults and failed critic repair fallback.

Why it broke now:

- Before contract validation, malformed repaired chart fields could drift downstream silently.
- After adding `.model_validate()`, the system correctly failed fast at the critic handoff.
- The missing piece was resilience policy: strict validation is right, but optional repair should not prevent saving the already generated dashboard and validation report.

Verification:

- `python -m unittest tests.test_agents_contracts tests.test_core_pipeline tests.test_dashboard_contract_validation` passes: 19 tests.
- `python -m unittest discover -s tests` passes: 82 tests.
- `npm.cmd run typecheck` passes.
- `npm.cmd run build` passes.
- Restarted FastAPI on `http://127.0.0.1:8000`.
- Regenerated `kaggle-rohitsahoo-sales-forecasting-train_dbb0f167b27c` with notebook disabled.
- Job completed successfully and wrote dashboard, validation, critique, and insights artifacts.
- Validation status is `passed_with_warnings`.

Reason: Contract validation should catch schema drift, but a failed optional repair pass should not throw away a usable dashboard. This keeps the pipeline strict at boundaries while still resilient in recovery paths.

### Added targeted cleanup for model routing and dashboard view quality

Stabilized the current dashboard pipeline work before changing models.

Changes made:

- Added `core/model_config.py`.
  - Keeps the old shared default model as `gpt-4.1-mini`.
  - Adds role-specific model resolution:
    - `OPENAI_SEMANTIC_MODEL`
    - `OPENAI_METRIC_CODE_MODEL`
    - `OPENAI_METRIC_REPAIR_MODEL`
    - `OPENAI_DASHBOARD_MODEL`
    - `OPENAI_DASHBOARD_CRITIC_MODEL`
    - `OPENAI_INSIGHTS_MODEL`
  - Falls back from explicit function argument, to role-specific env var, to `OPENAI_MODEL`, to default.
  - Centralizes `OPENAI_TIMEOUT_SECONDS` and `OPENAI_MAX_RETRIES`.
- Updated semantic, metric code, metric repair, dashboard planner, dashboard critic, and insights agents to use role-based model config.
- Added a fresh-run metadata normalization guard so new metadata consistently exposes `pandas_dtype`, `dtype`, `inferred_role`, null counts, null percentages, and schema column details.
- Tightened dashboard validation so bar charts fail validation when they ignore extra categorical dimensions with multiple values.
- Improved the frontend bar renderer for colored grouped outputs so repeated category rows render as stacked segments instead of duplicate labels.
- Added `scripts/compare_model_runs.py` to compare before/after model-change runs by artifact presence, metric repair count, validation issues, dashboard shape, trace warnings/failures, and stage durations.
- Documented role-specific model env vars and the comparison script in `.env.example` and `README.md`.

Why this cleanup was needed:

- The previous model setting was a single global default hidden in the semantic agent.
- Metric code generation is the stage most likely to benefit from a stronger model, but upgrading every agent at once would increase cost and make regressions harder to isolate.
- Dashboard views were technically valid by schema but could still be visually incoherent when the renderer could not represent the requested grain.
- Before/after run comparison gives us evidence for whether a stronger metric/code model improves the app.

Verification:

- `.venv\Scripts\python.exe -m py_compile core\model_config.py core\dataset_metadata.py api.py app.py notebook_export.py dashboard_validation.py agents\semantic_understanding.py agents\metric_code_planner.py agents\dashboard_planner.py agents\dashboard_critic.py agents\analytical_brain.py scripts\compare_model_runs.py` passes.
- `.venv\Scripts\python.exe -m unittest tests.test_model_config tests.test_dataset_metadata tests.test_dashboard_contract_validation tests.test_agents_contracts` passes: 30 tests.
- `.venv\Scripts\python.exe -m unittest discover -s tests` passes: 98 tests.
- `npm.cmd run typecheck` passes from `frontend/`.
- `npm.cmd run build` passes from `frontend/`.
- `scripts\compare_model_runs.py` successfully produces a comparison report for existing run artifacts.

### Added metric and dashboard model benchmarks

Added separate benchmark harnesses so model changes can be tested at the pipeline stage where they matter.

Changes made:

- Added `scripts/benchmark_metric_models.py`.
  - Benchmarks only the metric path:
    - saved metadata
    - saved semantic understanding
    - dataframe context
    - metric planner
    - sandbox execution
    - metric repair loop
  - Varies only `OPENAI_METRIC_CODE_MODEL` and `OPENAI_METRIC_REPAIR_MODEL`.
  - Saves reports to `artifacts/benchmarks/metric_models/`.
- Added `scripts/benchmark_dashboard_models.py`.
  - Benchmarks only dashboard planning and deterministic validation.
  - Reuses fixed metadata, semantic understanding, metric plan, and analysis outputs.
  - Varies only `OPENAI_DASHBOARD_MODEL` and `OPENAI_DASHBOARD_CRITIC_MODEL`.
  - Saves reports to `artifacts/benchmarks/dashboard_models/`.
- Added tests for both benchmark scripts.

Real-world benchmark dataset:

- Kaggle dataset: `uciml/iris`
- File: `Iris.csv`
- Size: 5,107 bytes
- Baseline full run: `kaggle-iris-baseline_600ac44f23c2`

Metric-only benchmark results:

- `gpt-4.1-mini`
  - status: succeeded
  - duration: 62.834 seconds
  - failed attempts: 1
  - declared outputs: 6
  - produced outputs: 7
- `gpt-4.1`
  - status: succeeded
  - duration: 31.77 seconds
  - failed attempts: 1
  - declared outputs: 6
  - produced outputs: 6
- `gpt-5-mini`
  - status: failed
  - duration: 290.466 seconds
  - failed attempts: 3
  - final error: `NameError: name 'type' is not defined`

Dashboard-only benchmark results:

- `gpt-4.1-mini`
  - status: succeeded
  - duration: 18.0 seconds
  - validation: passed
  - errors: 0
  - warnings: 0
  - critic used: false
  - KPIs: 2
  - overview charts: 2
  - question views: 3
  - chart mix: 3 bar, 1 histogram, 1 table
- `gpt-4.1`
  - status: succeeded
  - duration: 10.3 seconds
  - validation: passed
  - errors: 0
  - warnings: 0
  - critic used: false
  - KPIs: 2
  - overview charts: 2
  - question views: 3
  - chart mix: 2 bar, 1 histogram, 2 table

Conclusion:

- `gpt-4.1` is the best next model candidate for metric and dashboard stages.
- `gpt-5.2` failed the full upgraded metric run with a timeout after sandbox/repair failures.
- `gpt-5-mini` failed the metric-only benchmark and was much slower.
- The next practical upgrade is to set:
  - `OPENAI_METRIC_CODE_MODEL=gpt-4.1`
  - `OPENAI_METRIC_REPAIR_MODEL=gpt-4.1`
  - optionally `OPENAI_DASHBOARD_MODEL=gpt-4.1`
  - optionally `OPENAI_DASHBOARD_CRITIC_MODEL=gpt-4.1`

Reasoning:

- The pipeline problem is not generic code-writing ability; it is constrained, sandbox-safe pandas generation.
- Stronger reasoning models can overbuild in this context. The failed `gpt-5.2` run tried more ambitious feature-importance and nearest-centroid style logic, then hit sandbox and timeout failures.
- `gpt-5-mini` also failed the isolated metric benchmark after multiple repair attempts, so it was not a safer middle ground for the metric step.
- `gpt-4.1` gave the best practical signal: it succeeded in the same production metric path, completed faster than `gpt-4.1-mini`, and produced output counts that matched the declared contract exactly.
- The dashboard benchmark showed the same pattern: `gpt-4.1` passed validation with no issues and was faster than `gpt-4.1-mini`.
- We should upgrade only the stages with benchmark evidence instead of changing every agent. This keeps cost and regression surface smaller, and it preserves semantic/insight behavior until we have separate evidence for those roles.

Tradeoff:

- `gpt-4.1` may cost more than `gpt-4.1-mini`, but the benchmark suggests it can reduce time and produce cleaner contracts in the two most fragile stages.
- This does not solve deeper architecture issues like monolithic metric generation. The durable long-term fix is still to split metric planning/code generation per output so one bad metric cannot block an entire dashboard.

Verification:

- `.venv\Scripts\python.exe -m py_compile scripts\benchmark_metric_models.py scripts\benchmark_dashboard_models.py tests\test_benchmark_metric_models.py tests\test_benchmark_dashboard_models.py` passes.
- `.venv\Scripts\python.exe -m unittest tests.test_benchmark_metric_models tests.test_benchmark_dashboard_models tests.test_model_config tests.test_metric_execution` passes.

### Applied benchmark-winning model routing

Updated the running app configuration to use the benchmark-winning model for code-heavy and dashboard-planning stages.

Changes made:

- Updated local `.env` with:
  - `OPENAI_METRIC_CODE_MODEL=gpt-4.1`
  - `OPENAI_METRIC_REPAIR_MODEL=gpt-4.1`
  - `OPENAI_DASHBOARD_MODEL=gpt-4.1`
  - `OPENAI_DASHBOARD_CRITIC_MODEL=gpt-4.1`
- Updated `.env.example` to show the same recommended role-specific defaults.
- Restarted FastAPI on `http://127.0.0.1:8000`.

Verification:

- API health check returns `{"status": "ok"}`.
- Model routing check resolves:
  - metric code: `gpt-4.1`
  - metric repair: `gpt-4.1`
  - dashboard: `gpt-4.1`
  - dashboard critic: `gpt-4.1`
  - semantic: `gpt-4.1-mini`
  - insights: `gpt-4.1-mini`
- `.venv\Scripts\python.exe -m unittest tests.test_model_config tests.test_benchmark_metric_models tests.test_benchmark_dashboard_models` passes: 11 tests.

Reasoning:

- We applied the model change after benchmarking, not before, because the full `gpt-5.2` experiment showed that a nominally stronger coding model can be worse under this app's sandbox constraints.
- The chosen routing keeps `gpt-4.1-mini` for semantic and insights because those stages were not the observed bottleneck and were not part of the strongest benchmark signal.
- Metric code and metric repair are upgraded together because repair quality depends on the same code-generation constraints as the initial metric plan.
- Dashboard planner and critic are upgraded together because critic repair must speak the same chart/view language as the planner and deterministic validator.
- Updating `.env.example` makes the benchmark-backed recommendation reproducible, while updating local `.env` makes the currently running app ready for fresh testing.

Remaining risk:

- The benchmark used the small Iris dataset. The routing should be validated on at least one wider real-world dataset and one messier Kaggle CSV before treating it as final.
- If `gpt-4.1` still produces occasional sandbox failures on larger datasets, the next fix should be prompt/architecture refinement, not jumping straight back to `gpt-5.2`.
