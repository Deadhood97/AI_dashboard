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
  PlayCircle,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AnalysisOutputs,
  DashboardChart,
  RunBundle,
  RunSummary,
  SerializedAnalysisOutput,
  generateRun,
  getJob,
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

function artifactTotal(run?: RunSummary) {
  if (!run) return 0;
  return Object.keys(run.artifacts).length;
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
                  {formatNumber(run.row_count)} rows - {artifactCount(run)}/{artifactTotal(run)} artifacts
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

function RunActions({ bundle }: { bundle?: RunBundle }) {
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<string | null>(null);
  const runId = bundle?.summary.run_id;
  const hasDataset = Boolean(bundle?.summary.artifacts.dataset);

  const generationMutation = useMutation({
    mutationFn: () => {
      if (!runId) {
        throw new Error("Select a run first.");
      }
      return generateRun(runId, true);
    },
    onSuccess: (job) => setJobId(job.job_id)
  });

  const jobQuery = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 1500;
    }
  });

  const job = jobQuery.data;
  const jobIsActive = generationMutation.isPending || job?.status === "queued" || job?.status === "running";

  useEffect(() => {
    setJobId(null);
  }, [runId]);

  useEffect(() => {
    if (job?.status !== "completed" && job?.status !== "failed") return;
    queryClient.invalidateQueries({ queryKey: ["runs"] });
    queryClient.invalidateQueries({ queryKey: ["latest-run"] });
    if (runId) {
      queryClient.invalidateQueries({ queryKey: ["run", runId] });
      queryClient.invalidateQueries({ queryKey: ["notebook", runId] });
    }
  }, [job?.status, queryClient, runId]);

  return (
    <section className="actionBar">
      <button
        className="primaryButton"
        disabled={!hasDataset || jobIsActive}
        onClick={() => generationMutation.mutate()}
        type="button"
      >
        {jobIsActive ? <Loader2 size={16} className="spin" /> : <PlayCircle size={16} />}
        {jobIsActive ? "Generating" : "Generate dashboard"}
      </button>
      <div className="actionStatus">
        {job ? (
          <>
            <strong>{job.status}</strong>
            <span>{job.status === "failed" ? job.message : job.stage.replaceAll("_", " ")}</span>
          </>
        ) : generationMutation.isError ? (
          <>
            <strong>failed</strong>
            <span>{String(generationMutation.error.message)}</span>
          </>
        ) : (
          <>
            <strong>{artifactCount(bundle?.summary)}/{artifactTotal(bundle?.summary)} artifacts</strong>
            <span>{hasDataset ? "Ready to run agents" : "Load a dataset first"}</span>
          </>
        )}
      </div>
    </section>
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

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function asNumber(value: unknown): number | null {
  if (isNumber(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function outputRows(output?: SerializedAnalysisOutput): Array<Record<string, unknown>> {
  if (!output) return [];
  if (output.kind === "table") return output.rows;
  if (output.kind === "mapping") return [output.value];
  if (output.kind === "scalar") return [{ value: output.value }];
  return [];
}

function outputColumns(output?: SerializedAnalysisOutput): string[] {
  if (!output) return [];
  if (output.kind === "table") return output.columns;
  if (output.kind === "mapping") return Object.keys(output.value);
  return ["value"];
}

function valueLabel(value: unknown) {
  const numeric = asNumber(value);
  if (numeric !== null) return formatNumber(Number(numeric.toFixed(2)));
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function formatDuration(durationMs?: number | null) {
  if (durationMs === null || durationMs === undefined) return "-";
  if (durationMs < 1000) return `${durationMs} ms`;
  return `${(durationMs / 1000).toFixed(1)} s`;
}

function calculateRenderedKpi(
  output: SerializedAnalysisOutput | undefined,
  valueColumn?: string | null
) {
  if (!output) return "Missing";
  if (output.kind === "scalar") return valueLabel(output.value);
  if (output.kind === "mapping") {
    if (valueColumn && valueColumn in output.value) return valueLabel(output.value[valueColumn]);
    const firstNumeric = Object.values(output.value).find((value) => asNumber(value) !== null);
    return valueLabel(firstNumeric ?? Object.values(output.value)[0]);
  }

  const rows = output.rows;
  if (rows.length === 0) return "-";
  const numericValues = rows
    .map((row) => asNumber(valueColumn ? row[valueColumn] : undefined))
    .filter((value): value is number => value !== null);
  if (numericValues.length > 0) {
    const average = numericValues.reduce((sum, value) => sum + value, 0) / numericValues.length;
    return valueLabel(average);
  }
  return valueLabel(rows[0][valueColumn || output.columns[0]]);
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

function DataTable({ output, columns }: { output: SerializedAnalysisOutput; columns?: string[] }) {
  const rows = outputRows(output).slice(0, 25);
  const tableColumns = (columns?.length ? columns : outputColumns(output)).slice(0, 8);
  if (rows.length === 0) return <div className="renderEmpty">No rows returned.</div>;

  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            {tableColumns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {tableColumns.map((column) => (
                <td key={column}>{valueLabel(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BarRenderer({ chart, output }: { chart: DashboardChart; output: SerializedAnalysisOutput }) {
  const allRows = outputRows(output);
  const rows = allRows.slice(0, chart.top_n ?? 12);
  const xKey = chart.x || outputColumns(output)[0];
  const yKey = chart.y || outputColumns(output).find((column) => allRows.some((row) => asNumber(row[column]) !== null));
  if (!xKey || !yKey) return <DataTable output={output} />;

  const colorKey = chart.color && outputColumns(output).includes(chart.color) ? chart.color : null;
  if (colorKey && chart.orientation !== "horizontal") {
    const grouped = new Map<string, { total: number; segments: Array<{ label: string; value: number }> }>();
    for (const row of allRows) {
      const groupLabel = valueLabel(row[xKey]);
      const segmentLabel = valueLabel(row[colorKey]);
      const value = Math.max(asNumber(row[yKey]) ?? 0, 0);
      const group = grouped.get(groupLabel) ?? { total: 0, segments: [] };
      group.total += value;
      group.segments.push({ label: segmentLabel, value });
      grouped.set(groupLabel, group);
    }
    const groups = Array.from(grouped.entries()).slice(0, chart.top_n ?? 12);
    const maxTotal = Math.max(...groups.map(([, group]) => group.total), 1);

    return (
      <div className="barViz stacked">
        {groups.map(([label, group]) => {
          const height = `${Math.max((group.total / maxTotal) * 100, 2)}%`;
          return (
            <div className="barRow" key={label}>
              <span className="barLabel" title={label}>{label}</span>
              <span className="barTrack" style={{ height }}>
                {group.segments.map((segment, index) => {
                  const segmentHeight = `${Math.max((segment.value / Math.max(group.total, 1)) * 100, 2)}%`;
                  return (
                    <span
                      className="barSegment"
                      key={`${segment.label}-${index}`}
                      style={{ height: segmentHeight }}
                      title={`${segment.label}: ${valueLabel(segment.value)}`}
                    />
                  );
                })}
              </span>
              <strong>{valueLabel(group.total)}</strong>
            </div>
          );
        })}
      </div>
    );
  }

  const values = rows.map((row) => asNumber(row[yKey]) ?? 0);
  const max = Math.max(...values.map((value) => Math.abs(value)), 1);
  const horizontal = chart.orientation === "horizontal";

  return (
    <div className={`barViz ${horizontal ? "horizontal" : ""}`}>
      {rows.map((row, index) => {
        const value = values[index];
        const size = `${Math.max((Math.abs(value) / max) * 100, 2)}%`;
        return (
          <div className="barRow" key={`${valueLabel(row[xKey])}-${index}`}>
            <span className="barLabel">{valueLabel(row[xKey])}</span>
            <span className="barTrack">
              <span className="barFill" style={horizontal ? { width: size } : { height: size }} />
            </span>
            <strong>{valueLabel(value)}</strong>
          </div>
        );
      })}
    </div>
  );
}

function LineRenderer({ chart, output }: { chart: DashboardChart; output: SerializedAnalysisOutput }) {
  const rows = outputRows(output).slice(0, 80);
  const xKey = chart.x || outputColumns(output)[0];
  const yKey = chart.y || chart.metrics?.[0] || outputColumns(output).find((column) => rows.some((row) => asNumber(row[column]) !== null));
  if (!xKey || !yKey) return <DataTable output={output} />;

  const points = rows
    .map((row, index) => ({ index, label: valueLabel(row[xKey]), value: asNumber(row[yKey]) }))
    .filter((point): point is { index: number; label: string; value: number } => point.value !== null);
  if (points.length < 2) return <DataTable output={output} />;

  const min = Math.min(...points.map((point) => point.value));
  const max = Math.max(...points.map((point) => point.value));
  const span = max - min || 1;
  const path = points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * 100;
      const y = 100 - ((point.value - min) / span) * 86 - 7;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <div className="lineViz">
      <svg viewBox="0 0 100 100" role="img" aria-label={chart.title} preserveAspectRatio="none">
        <path d={path} />
      </svg>
      <div className="axisMeta">
        <span>{points[0].label}</span>
        <strong>{valueLabel(min)} - {valueLabel(max)}</strong>
        <span>{points[points.length - 1].label}</span>
      </div>
    </div>
  );
}

function ScatterRenderer({ chart, output }: { chart: DashboardChart; output: SerializedAnalysisOutput }) {
  const rows = outputRows(output).slice(0, 120);
  const xKey = chart.x || outputColumns(output)[0];
  const yKey = chart.y || outputColumns(output)[1];
  if (!xKey || !yKey) return <DataTable output={output} />;
  const points = rows
    .map((row) => ({ x: asNumber(row[xKey]), y: asNumber(row[yKey]) }))
    .filter((point): point is { x: number; y: number } => point.x !== null && point.y !== null);
  if (points.length < 2) return <DataTable output={output} />;
  const minX = Math.min(...points.map((point) => point.x));
  const maxX = Math.max(...points.map((point) => point.x));
  const minY = Math.min(...points.map((point) => point.y));
  const maxY = Math.max(...points.map((point) => point.y));
  const spanX = maxX - minX || 1;
  const spanY = maxY - minY || 1;
  return (
    <div className="scatterViz">
      <svg viewBox="0 0 100 100" role="img" aria-label={chart.title}>
        {points.map((point, index) => (
          <circle
            cx={6 + ((point.x - minX) / spanX) * 88}
            cy={94 - ((point.y - minY) / spanY) * 88}
            key={index}
            r="2.2"
          />
        ))}
      </svg>
      <div className="axisMeta">
        <span>{xKey}</span>
        <strong>{points.length} points</strong>
        <span>{yKey}</span>
      </div>
    </div>
  );
}

function RenderedChart({ chart, outputs }: { chart: DashboardChart; outputs?: AnalysisOutputs | null }) {
  const output = outputs?.[chart.source_output_key];
  if (!output) return <ChartSpecCard chart={chart} />;

  return (
    <article className="renderedChart">
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
      {chart.chart_type === "bar" || chart.chart_type === "histogram" ? <BarRenderer chart={chart} output={output} /> : null}
      {chart.chart_type === "line" || chart.chart_type === "multi_line" ? <LineRenderer chart={chart} output={output} /> : null}
      {chart.chart_type === "scatter" ? <ScatterRenderer chart={chart} output={output} /> : null}
      {chart.chart_type === "table" || chart.chart_type === "text" || chart.chart_type === "kpi" ? <DataTable output={output} /> : null}
      {chart.scale_note ? <div className="note">{chart.scale_note}</div> : null}
    </article>
  );
}

function DashboardView({ bundle }: { bundle: RunBundle }) {
  const plan = bundle.dashboard_plan;
  if (!plan) return <EmptyState title="No dashboard plan" />;
  const outputs = bundle.analysis_outputs;

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
              <strong className="kpiValue">{calculateRenderedKpi(outputs?.[kpi.source_output_key], kpi.value_column)}</strong>
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
            <RenderedChart chart={chart} key={chart.title} outputs={outputs} />
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
              <RenderedChart chart={view.chart} outputs={outputs} />
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
  const trace = bundle.trace;
  return (
    <div className="workspaceStack">
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

      <section className="panel">
        <div className="panelTitle">
          <History size={17} />
          Run Trace
        </div>
        {!trace ? (
          <div className="traceEmpty">No trace artifact for this run.</div>
        ) : (
          <div className="traceTimeline">
            <div className={`traceSummary ${trace.status}`}>
              <strong>{trace.status.replaceAll("_", " ")}</strong>
              <span>{formatDuration(trace.duration_ms)}</span>
              <small>{trace.message || trace.run_id}</small>
            </div>
            {trace.events.map((event, index) => (
              <article className={`traceEvent ${event.status}`} key={`${event.stage}-${index}`}>
                <div className="traceEventHead">
                  <strong>{event.stage.replaceAll("_", " ")}</strong>
                  <span>{event.status}</span>
                  <small>{formatDuration(event.duration_ms)}</small>
                </div>
                {event.message ? <p>{event.message}</p> : null}
                {event.error_message ? (
                  <p className="traceError">
                    {event.error_type ? `${event.error_type}: ` : ""}
                    {event.error_message}
                  </p>
                ) : null}
                {Object.keys(event.artifact_paths).length > 0 ? (
                  <div className="traceArtifacts">
                    {Object.keys(event.artifact_paths).map((name) => (
                      <span key={name}>{name.replaceAll("_", " ")}</span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
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
        <RunActions bundle={bundle} />
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
