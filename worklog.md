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
