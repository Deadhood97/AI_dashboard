export type ArtifactStatus = {
  metadata: boolean;
  dataset: boolean;
  semantic: boolean;
  metric_plan: boolean;
  analysis_outputs: boolean;
  dashboard: boolean;
  validation: boolean;
  critique: boolean;
  insights: boolean;
  notebook: boolean;
  trace: boolean;
};

export type RunSummary = {
  run_id: string;
  source_file: string;
  file_sha256: string;
  created_at?: string | null;
  row_count?: number | null;
  column_count?: number | null;
  artifacts: ArtifactStatus;
};

export type ValidationIssue = {
  severity: "info" | "warning" | "error";
  component: string;
  item_title: string;
  source_output_key?: string | null;
  message: string;
  suggested_fix: string;
};

export type ValidationReport = {
  status: "passed" | "passed_with_warnings" | "failed";
  issues: ValidationIssue[];
  rejected_chart_titles: string[];
  rejected_kpi_titles: string[];
};

export type DashboardChart = {
  title: string;
  chart_type: string;
  source_output_key: string;
  x?: string | null;
  y?: string | null;
  color?: string | null;
  metrics?: string[];
  top_n?: number | null;
  sort_by?: string | null;
  sort_order?: string;
  orientation?: string;
  scale_note?: string | null;
  rationale: string;
};

export type DashboardPlan = {
  dashboard_title: string;
  dashboard_summary: string;
  data_integrity_notes: string[];
  kpis: Array<{
    title: string;
    source_output_key: string;
    value_column?: string | null;
    rationale: string;
  }>;
  overview_charts: DashboardChart[];
  question_views: Array<{
    question: string;
    answer_strategy: string;
    chart: DashboardChart;
  }>;
  assumptions: string[];
  limitations: string[];
};

export type SerializedAnalysisOutput =
  | {
      kind: "table";
      type: string;
      columns: string[];
      rows: Array<Record<string, unknown>>;
      row_count: number;
      truncated: boolean;
    }
  | {
      kind: "mapping";
      type: string;
      value: Record<string, unknown>;
    }
  | {
      kind: "scalar";
      type: string;
      value: unknown;
    };

export type AnalysisOutputs = Record<string, SerializedAnalysisOutput>;

export type AnalyticalInsights = {
  narrative_title: string;
  executive_summary: string;
  key_insights: Array<{
    headline: string;
    explanation: string;
    evidence: string[];
    business_implication: string;
    recommended_action: string;
    confidence: string;
    impact: string;
    related_dashboard_items: string[];
  }>;
  watchouts: string[];
  follow_up_questions: string[];
};

export type RunTraceEvent = {
  stage: string;
  event_type: string;
  status: "running" | "completed" | "warning" | "failed" | "skipped" | string;
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  message: string;
  error_type?: string | null;
  error_message?: string | null;
  artifact_paths: Record<string, string>;
};

export type RunTrace = {
  run_id: string;
  job_id?: string | null;
  status: "running" | "completed" | "warning" | "failed" | "skipped" | string;
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  message: string;
  events: RunTraceEvent[];
};

export type RunBundle = {
  summary: RunSummary;
  metadata: Record<string, unknown>;
  semantic_understanding?: Record<string, unknown> | null;
  metric_plan?: Record<string, unknown> | null;
  analysis_outputs?: AnalysisOutputs | null;
  dashboard_plan?: DashboardPlan | null;
  validation_report?: ValidationReport | null;
  dashboard_critique?: Record<string, unknown> | null;
  analytical_insights?: AnalyticalInsights | null;
  notebook_available: boolean;
  trace?: RunTrace | null;
};

export type JobStatus = {
  job_id: string;
  run_id: string;
  status: "queued" | "running" | "completed" | "failed" | string;
  stage: string;
  message: string;
  started_at: string;
  finished_at?: string | null;
};

export type NotebookCell = {
  cell_type: "markdown" | "code";
  source: string[] | string;
  outputs?: Array<{
    output_type: string;
    data?: Record<string, string | string[]>;
    text?: string | string[];
  }>;
};

export type NotebookPayload = {
  nbformat: number;
  cells: NotebookCell[];
};

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function errorMessage(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) return `${response.status} ${response.statusText}`;
  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    if (typeof payload.detail === "string") return payload.detail;
  } catch {
    return text;
  }
  return text;
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return (await response.json()) as T;
}

export function getRuns() {
  return fetchJson<RunSummary[]>("/api/runs");
}

export function getLatestRun() {
  return fetchJson<RunBundle>("/api/runs/latest");
}

export function getRun(runId: string) {
  return fetchJson<RunBundle>(`/api/runs/${runId}`);
}

export function getNotebook(runId: string) {
  return fetchJson<NotebookPayload>(`/api/runs/${runId}/notebook`);
}

export function getTrace(runId: string) {
  return fetchJson<RunTrace>(`/api/runs/${runId}/trace`);
}

export function getJob(jobId: string) {
  return fetchJson<JobStatus>(`/api/jobs/${jobId}`);
}

export async function generateRun(runId: string, includeNotebook = true) {
  const response = await fetch(`${API_BASE}/api/runs/${runId}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ include_notebook: includeNotebook })
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return (await response.json()) as JobStatus;
}

export async function uploadDataset(file: File, description: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("description", description);

  const response = await fetch(`${API_BASE}/api/datasets/upload`, {
    method: "POST",
    body: form
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return (await response.json()) as RunBundle;
}

export async function importKaggleDataset(payload: {
  dataset_ref: string;
  requested_file?: string;
  description?: string;
}) {
  const response = await fetch(`${API_BASE}/api/datasets/kaggle`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return (await response.json()) as RunBundle;
}
