"use client";

import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  CheckCircle2,
  CircleDot,
  Database,
  FileCode2,
  FileUp,
  History,
  LineChart,
  Loader2,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DashboardChart,
  RunBundle,
  RunSummary,
  importKaggleDataset,
  getLatestRun,
  getNotebook,
  getRun,
  getRuns,
  uploadDataset
} from "../lib/api";

const navItems = ["Source", "Dashboard", "Insights", "Notebook", "Artifacts"] as const;
type NavItem = (typeof navItems)[number];

function formatNumber(value?: number | null) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat().format(value);
}

function sourceLabel(sourceFile: string) {
  return sourceFile.replace(/^kaggle_/, "Kaggle: ").replace(/_/g, " ");
}

function statusTone(status?: string) {
  if (status === "passed") return "good";
  if (status === "passed_with_warnings") return "warn";
  if (status === "failed") return "bad";
  return "muted";
}

function chartIcon(chartType: string) {
  if (chartType.includes("line")) return <LineChart size={16} />;
  if (chartType === "table") return <FileCode2 size={16} />;
  return <BarChart3 size={16} />;
}

function artifactCount(run?: RunSummary) {
  if (!run) return 0;
  return Object.values(run.artifacts).filter(Boolean).length;
}

function joinSource(source: string[] | string | undefined) {
  if (!source) return "";
  return Array.isArray(source) ? source.join("") : source;
}

function ShellState({
  selectedRunId,
  onSelectRun
}: {
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
}) {
  const runsQuery = useQuery({ queryKey: ["runs"], queryFn: getRuns });
  const runs = runsQuery.data ?? [];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brandMark">DS</div>
        <div>
          <strong>Dashboard Studio</strong>
          <span>Artifact workspace</span>
        </div>
      </div>

      <div className="sidebarSection">
        <div className="sectionLabel">
          <History size={14} />
          Runs
        </div>
        {runsQuery.isLoading ? (
          <div className="mutedRow">
            <Loader2 size={14} className="spin" />
            Loading runs
          </div>
        ) : (
          <div className="runList">
            {runs.map((run) => (
              <button
                className={`runButton ${selectedRunId === run.run_id ? "active" : ""}`}
                key={run.run_id}
                onClick={() => onSelectRun(run.run_id)}
              >
                <span>{sourceLabel(run.source_file)}</span>
                <small>
                  {formatNumber(run.row_count)} rows - {artifactCount(run)}/9 artifacts
                </small>
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function Header({ bundle }: { bundle?: RunBundle }) {
  const status = bundle?.validation_report?.status ?? "not validated";
  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">Current Run</div>
        <h1>{bundle?.dashboard_plan?.dashboard_title ?? "Dashboard Studio"}</h1>
        <p>{bundle?.dashboard_plan?.dashboard_summary ?? "Select or generate a dashboard run."}</p>
      </div>
      <div className="statusPills">
        <span className={`pill ${statusTone(status)}`}>
          <ShieldCheck size={15} />
          {status.replaceAll("_", " ")}
        </span>
        <span className="pill">
          <Database size={15} />
          {formatNumber(bundle?.summary.row_count)} rows
        </span>
        <span className="pill">
          <BookOpen size={15} />
          {bundle?.notebook_available ? "Notebook ready" : "No notebook"}
        </span>
      </div>
    </header>
  );
}

function StatStrip({ bundle }: { bundle: RunBundle }) {
  const validationIssues = bundle.validation_report?.issues ?? [];
  const insights = bundle.analytical_insights?.key_insights ?? [];
  return (
    <section className="statGrid">
      <div className="stat">
        <span>Rows</span>
        <strong>{formatNumber(bundle.summary.row_count)}</strong>
      </div>
      <div className="stat">
        <span>Columns</span>
        <strong>{formatNumber(bundle.summary.column_count)}</strong>
      </div>
      <div className="stat">
        <span>Validation Issues</span>
        <strong>{validationIssues.length}</strong>
      </div>
      <div className="stat">
        <span>Insights</span>
        <strong>{insights.length}</strong>
      </div>
    </section>
  );
}

function ChartSpecCard({ chart }: { chart: DashboardChart }) {
  return (
    <article className="chartSpec">
      <div className="chartHeader">
        <div>
          <div className="chartTitle">{chart.title}</div>
          <p>{chart.rationale}</p>
        </div>
        <span className="chartType">
          {chartIcon(chart.chart_type)}
          {chart.chart_type}
        </span>
      </div>
      <div className="fieldGrid">
        <span>source</span>
        <code>{chart.source_output_key}</code>
        <span>x</span>
        <code>{chart.x ?? chart.metrics?.join(", ") ?? "-"}</code>
        <span>y</span>
        <code>{chart.y ?? "-"}</code>
        <span>limit</span>
        <code>{chart.top_n ?? "none"}</code>
      </div>
      {chart.scale_note ? <div className="note">{chart.scale_note}</div> : null}
    </article>
  );
}

function DashboardView({ bundle }: { bundle: RunBundle }) {
  const plan = bundle.dashboard_plan;
  if (!plan) return <EmptyState title="No dashboard plan" />;

  return (
    <div className="workspaceStack">
      <StatStrip bundle={bundle} />

      <section className="panel">
        <div className="panelTitle">
          <Sparkles size={17} />
          KPIs
        </div>
        <div className="kpiGrid">
          {plan.kpis.map((kpi) => (
            <div className="kpi" key={kpi.title}>
              <span>{kpi.source_output_key}</span>
              <strong>{kpi.title}</strong>
              <p>{kpi.rationale}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panelTitle">
          <BarChart3 size={17} />
          Overview
        </div>
        <div className="cardGrid">
          {plan.overview_charts.map((chart) => (
            <ChartSpecCard chart={chart} key={chart.title} />
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panelTitle">
          <CircleDot size={17} />
          Question Views
        </div>
        <div className="questionList">
          {plan.question_views.map((view) => (
            <div className="questionItem" key={view.question}>
              <h3>{view.question}</h3>
              <p>{view.answer_strategy}</p>
              <ChartSpecCard chart={view.chart} />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function SourceView({ onRunCreated }: { onRunCreated: (runId: string) => void }) {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadDescription, setUploadDescription] = useState("");
  const [kaggleRef, setKaggleRef] = useState("");
  const [kaggleFile, setKaggleFile] = useState("");
  const [kaggleDescription, setKaggleDescription] = useState("");

  function handleCreated(bundle: RunBundle) {
    queryClient.invalidateQueries({ queryKey: ["runs"] });
    queryClient.invalidateQueries({ queryKey: ["latest-run"] });
    onRunCreated(bundle.summary.run_id);
  }

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) {
        throw new Error("Choose a CSV file first.");
      }
      return uploadDataset(selectedFile, uploadDescription);
    },
    onSuccess: handleCreated
  });

  const kaggleMutation = useMutation({
    mutationFn: () =>
      importKaggleDataset({
        dataset_ref: kaggleRef,
        requested_file: kaggleFile,
        description: kaggleDescription
      }),
    onSuccess: handleCreated
  });

  function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    uploadMutation.mutate();
  }

  function submitKaggle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    kaggleMutation.mutate();
  }

  return (
    <div className="workspaceStack">
      <section className="sourceHero">
        <div>
          <div className="eyebrow">Source</div>
          <h2>Load a dataset</h2>
          <p>
            Upload a local CSV or import a Kaggle dataset. This creates a saved run that the agents can use next.
          </p>
        </div>
      </section>

      <section className="sourceGrid">
        <form className="sourceCard" onSubmit={submitUpload}>
          <div className="panelTitle">
            <FileUp size={17} />
            Upload CSV
          </div>
          <label>
            CSV file
            <input
              accept=".csv,text/csv"
              type="file"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <label>
            Business context
            <textarea
              placeholder="Optional notes about the dataset, target audience, or business question."
              value={uploadDescription}
              onChange={(event) => setUploadDescription(event.target.value)}
            />
          </label>
          <button className="primaryButton" disabled={uploadMutation.isPending} type="submit">
            {uploadMutation.isPending ? "Uploading..." : "Upload dataset"}
          </button>
          {uploadMutation.isError ? <div className="formError">{String(uploadMutation.error.message)}</div> : null}
          {uploadMutation.isSuccess ? <div className="formSuccess">Dataset uploaded and selected.</div> : null}
        </form>

        <form className="sourceCard" onSubmit={submitKaggle}>
          <div className="panelTitle">
            <Database size={17} />
            Import From Kaggle
          </div>
          <label>
            Dataset reference
            <input
              placeholder="owner/dataset-slug"
              value={kaggleRef}
              onChange={(event) => setKaggleRef(event.target.value)}
            />
          </label>
          <label>
            CSV filename
            <input
              placeholder="Optional, defaults to the first CSV"
              value={kaggleFile}
              onChange={(event) => setKaggleFile(event.target.value)}
            />
          </label>
          <label>
            Additional context
            <textarea
              placeholder="Optional notes appended to Kaggle metadata."
              value={kaggleDescription}
              onChange={(event) => setKaggleDescription(event.target.value)}
            />
          </label>
          <button className="primaryButton" disabled={kaggleMutation.isPending || !kaggleRef.trim()} type="submit">
            {kaggleMutation.isPending ? "Importing..." : "Import from Kaggle"}
          </button>
          {kaggleMutation.isError ? <div className="formError">{String(kaggleMutation.error.message)}</div> : null}
          {kaggleMutation.isSuccess ? <div className="formSuccess">Kaggle dataset imported and selected.</div> : null}
        </form>
      </section>
    </div>
  );
}

function InsightsView({ bundle }: { bundle: RunBundle }) {
  const insights = bundle.analytical_insights;
  const issues = bundle.validation_report?.issues ?? [];
  return (
    <div className="workspaceStack">
      <section className="panel narrative">
        <div className="panelTitle">
          <Sparkles size={17} />
          {insights?.narrative_title ?? "Analytical Narrative"}
        </div>
        <p>{insights?.executive_summary ?? "No analytical brain output exists for this run yet."}</p>
      </section>

      <section className="insightGrid">
        {(insights?.key_insights ?? []).map((insight) => (
          <article className="insightCard" key={insight.headline}>
            <div className="insightMeta">
              <span>{insight.impact} impact</span>
              <span>{insight.confidence} confidence</span>
            </div>
            <h3>{insight.headline}</h3>
            <p>{insight.explanation}</p>
            <strong>Recommended action</strong>
            <p>{insight.recommended_action}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <div className="panelTitle">
          <AlertTriangle size={17} />
          Validation
        </div>
        {issues.length === 0 ? (
          <div className="cleanState">
            <CheckCircle2 size={18} />
            No validation issues.
          </div>
        ) : (
          <div className="issueList">
            {issues.map((issue, index) => (
              <div className={`issue ${issue.severity}`} key={`${issue.item_title}-${index}`}>
                <strong>{issue.item_title}</strong>
                <p>{issue.message}</p>
                <small>{issue.suggested_fix}</small>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function NotebookView({ runId, enabled }: { runId: string; enabled: boolean }) {
  const notebookQuery = useQuery({
    queryKey: ["notebook", runId],
    queryFn: () => getNotebook(runId),
    enabled
  });

  if (!enabled) return <EmptyState title="No notebook artifact" />;
  if (notebookQuery.isLoading) return <LoadingState label="Loading notebook" />;
  if (notebookQuery.isError) return <EmptyState title="Could not load notebook" />;

  const cells = notebookQuery.data?.cells ?? [];
  return (
    <div className="notebook">
      {cells.slice(0, 14).map((cell, index) => {
        const source = joinSource(cell.source);
        if (cell.cell_type === "markdown") {
          return (
            <section className="notebookMarkdown" key={index}>
              <pre>{source}</pre>
            </section>
          );
        }
        return (
          <section className="notebookCode" key={index}>
            <pre>{source}</pre>
            {(cell.outputs ?? []).length > 0 ? (
              <div className="outputBadge">{cell.outputs?.length} captured output</div>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}

function ArtifactsView({ bundle }: { bundle: RunBundle }) {
  const entries = Object.entries(bundle.summary.artifacts);
  return (
    <section className="panel">
      <div className="panelTitle">
        <FileCode2 size={17} />
        Artifacts
      </div>
      <div className="artifactGrid">
        {entries.map(([name, exists]) => (
          <div className="artifact" key={name}>
            <span className={exists ? "dot good" : "dot muted"} />
            <strong>{name.replaceAll("_", " ")}</strong>
            <small>{exists ? "available" : "missing"}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function EmptyState({ title }: { title: string }) {
  return <div className="emptyState">{title}</div>;
}

function LoadingState({ label }: { label: string }) {
  return (
    <div className="emptyState">
      <Loader2 size={18} className="spin" />
      {label}
    </div>
  );
}

export default function Home() {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [active, setActive] = useState<NavItem>("Source");

  const latestQuery = useQuery({
    queryKey: ["latest-run"],
    queryFn: getLatestRun,
    enabled: selectedRunId === null
  });
  const runQuery = useQuery({
    queryKey: ["run", selectedRunId],
    queryFn: () => getRun(selectedRunId as string),
    enabled: selectedRunId !== null
  });

  const bundle = useMemo(
    () => (selectedRunId ? runQuery.data : latestQuery.data),
    [latestQuery.data, runQuery.data, selectedRunId]
  );
  const isLoading = selectedRunId ? runQuery.isLoading : latestQuery.isLoading;

  return (
    <main className="appShell">
      <ShellState selectedRunId={selectedRunId} onSelectRun={setSelectedRunId} />
      <section className="mainPane">
        <Header bundle={bundle} />
        <nav className="viewTabs">
          {navItems.map((item) => (
            <button className={active === item ? "active" : ""} key={item} onClick={() => setActive(item)}>
              {item}
            </button>
          ))}
        </nav>
        {isLoading || !bundle ? (
          active === "Source" ? (
            <SourceView onRunCreated={setSelectedRunId} />
          ) : (
            <LoadingState label="Loading dashboard run" />
          )
        ) : (
          <>
            {active === "Source" ? <SourceView onRunCreated={setSelectedRunId} /> : null}
            {active === "Dashboard" ? <DashboardView bundle={bundle} /> : null}
            {active === "Insights" ? <InsightsView bundle={bundle} /> : null}
            {active === "Notebook" ? (
              <NotebookView runId={bundle.summary.run_id} enabled={bundle.notebook_available} />
            ) : null}
            {active === "Artifacts" ? <ArtifactsView bundle={bundle} /> : null}
          </>
        )}
      </section>
    </main>
  );
}
