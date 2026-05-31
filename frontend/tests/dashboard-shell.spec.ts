import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const screenshotDir = path.join(process.cwd(), "test-results", "screenshots");

async function screenshot(pageName: string, page: import("@playwright/test").Page) {
  await fs.mkdir(screenshotDir, { recursive: true });
  await page.screenshot({
    path: path.join(screenshotDir, `${pageName}.png`),
    fullPage: true
  });
}

async function openLoadedApp(page: import("@playwright/test").Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.locator(".runButton").first()).toBeVisible();
}

function completeMockRun() {
  const summary = {
    run_id: "mock_run",
    source_file: "mock.csv",
    file_sha256: "abcdef",
    created_at: "2026-05-31T00:00:00+00:00",
    row_count: 2,
    column_count: 2,
    artifacts: {
      metadata: true,
      dataset: true,
      semantic: true,
      metric_plan: true,
      analysis_outputs: true,
      dashboard: true,
      validation: true,
      critique: false,
      insights: false,
      notebook: true,
      trace: true
    }
  };
  const bundle = {
    summary,
    metadata: { source_file: "mock.csv" },
    semantic_understanding: null,
    metric_plan: null,
    analysis_outputs: {
      category_totals: {
        kind: "table",
        type: "DataFrame",
        columns: ["category", "value"],
        rows: [
          { category: "Alpha", value: 10 },
          { category: "Beta", value: 20 }
        ],
        row_count: 2,
        truncated: false
      }
    },
    dashboard_plan: {
      dashboard_title: "Rendered Mock Dashboard",
      dashboard_summary: "Uses analysis output rows.",
      data_integrity_notes: [],
      kpis: [
        {
          title: "Average Value",
          source_output_key: "category_totals",
          value_column: "value",
          rationale: "Shows the average rendered KPI value."
        }
      ],
      overview_charts: [
        {
          title: "Category Totals",
          chart_type: "bar",
          source_output_key: "category_totals",
          x: "category",
          y: "value",
          metrics: [],
          top_n: 10,
          sort_order: "descending",
          orientation: "vertical",
          rationale: "Compares category totals."
        }
      ],
      question_views: [],
      assumptions: [],
      limitations: []
    },
    validation_report: { status: "passed", issues: [], rejected_chart_titles: [], rejected_kpi_titles: [] },
    dashboard_critique: null,
    analytical_insights: null,
    notebook_available: true,
    trace: {
      run_id: "mock_run",
      job_id: "job_mock",
      status: "completed",
      started_at: "2026-05-31T00:00:00+00:00",
      finished_at: "2026-05-31T00:00:02+00:00",
      duration_ms: 2000,
      message: "Dashboard artifacts generated.",
      events: [
        {
          stage: "metrics",
          event_type: "stage",
          status: "completed",
          started_at: "2026-05-31T00:00:00+00:00",
          finished_at: "2026-05-31T00:00:01+00:00",
          duration_ms: 1000,
          message: "Metric plan executed.",
          artifact_paths: { metric_plan: "metric.json", analysis_outputs: "outputs.json" }
        },
        {
          stage: "insights",
          event_type: "stage",
          status: "warning",
          started_at: "2026-05-31T00:00:01+00:00",
          finished_at: "2026-05-31T00:00:02+00:00",
          duration_ms: 1000,
          message: "Analytical insights generation failed.",
          error_type: "RuntimeError",
          error_message: "insights unavailable",
          artifact_paths: {}
        }
      ]
    }
  };
  const notebook = {
    nbformat: 4,
    cells: [
      {
        cell_type: "markdown",
        source: ["# Mock analysis notebook\n\nThis notebook explains the generated dashboard."]
      },
      {
        cell_type: "code",
        source: ["analysis_outputs['category_totals']"],
        outputs: []
      }
    ]
  };
  return { summary, bundle, notebook };
}

async function routeCompleteMockRun(page: import("@playwright/test").Page) {
  const { summary, bundle, notebook } = completeMockRun();
  await page.route("**/api/runs", (route) => route.fulfill({ json: [summary] }));
  await page.route("**/api/runs/latest", (route) => route.fulfill({ json: bundle }));
  await page.route("**/api/runs/mock_run/notebook", (route) => route.fulfill({ json: notebook }));
}

test("renders latest run workspace from the artifact API @screenshots", async ({ page }) => {
  await routeCompleteMockRun(page);
  await openLoadedApp(page);
  await page.getByRole("button", { name: "Dashboard", exact: true }).click();

  await expect(page.getByRole("button", { name: "Dashboard", exact: true })).toHaveClass(/active/);
  await expect(page.locator(".stat").filter({ hasText: "Rows" })).toBeVisible();
  await expect(page.locator(".renderedChart, .chartSpec").first()).toBeVisible();

  await screenshot("dashboard-workspace", page);
});

test("renders charts from analysis outputs when the API provides data", async ({ page }) => {
  await routeCompleteMockRun(page);

  await page.goto("/");
  await page.getByRole("button", { name: "Dashboard", exact: true }).click();

  await expect(page.locator(".renderedChart").filter({ hasText: "Category Totals" })).toBeVisible();
  await expect(page.locator(".barFill").first()).toBeVisible();
  await expect(page.locator(".kpi").filter({ hasText: "15" })).toBeVisible();
  await expect(page.locator(".chartSpec")).toHaveCount(0);
});

test("renders colored bar outputs as grouped chart segments", async ({ page }) => {
  const { summary, bundle } = completeMockRun() as { summary: unknown; bundle: any };
  bundle.analysis_outputs = {
    outcome_mix: {
      kind: "table",
      type: "DataFrame",
      columns: ["segment", "outcome", "share"],
      rows: [
        { segment: "Alpha", outcome: "Won", share: 0.7 },
        { segment: "Alpha", outcome: "Lost", share: 0.3 },
        { segment: "Beta", outcome: "Won", share: 0.4 },
        { segment: "Beta", outcome: "Lost", share: 0.6 }
      ],
      row_count: 4,
      truncated: false
    }
  };
  bundle.dashboard_plan.overview_charts = [
    {
      title: "Outcome Mix",
      chart_type: "bar",
      source_output_key: "outcome_mix",
      x: "segment",
      y: "share",
      color: "outcome",
      metrics: [],
      top_n: 10,
      sort_order: "descending",
      orientation: "vertical",
      rationale: "Compares outcome shares by segment."
    }
  ];

  await page.route("**/api/runs", (route) => route.fulfill({ json: [summary] }));
  await page.route("**/api/runs/latest", (route) => route.fulfill({ json: bundle }));

  await page.goto("/");
  await page.getByRole("button", { name: "Dashboard", exact: true }).click();

  await expect(page.locator(".renderedChart").filter({ hasText: "Outcome Mix" })).toBeVisible();
  await expect(page.locator(".barViz.stacked")).toBeVisible();
  await expect(page.locator(".barSegment")).toHaveCount(4);
  await expect(page.locator(".barLabel").filter({ hasText: "Alpha" })).toHaveCount(1);
});

test("shows upload and Kaggle import entry points @screenshots", async ({ page }) => {
  await routeCompleteMockRun(page);
  await openLoadedApp(page);

  await expect(page.getByRole("button", { name: "Source", exact: true })).toHaveClass(/active/);
  await expect(page.getByRole("button", { name: "Upload dataset", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Import from Kaggle", exact: true })).toBeVisible();
  await expect(page.getByPlaceholder("owner/dataset-slug")).toBeVisible();

  await screenshot("source-import", page);
});

test("shows analytical insights and validation output @screenshots", async ({ page }) => {
  await routeCompleteMockRun(page);
  await openLoadedApp(page);
  await page.getByRole("button", { name: "Insights", exact: true }).click();

  await expect(page.locator(".narrative")).toBeVisible();
  await expect(page.getByText("Validation", { exact: true })).toBeVisible();
  await expect(page.locator(".insightCard").or(page.locator(".cleanState")).first()).toBeVisible();

  await screenshot("insights-validation", page);
});

test("renders notebook cells instead of only metadata @screenshots", async ({ page }) => {
  await routeCompleteMockRun(page);
  await openLoadedApp(page);
  await page.getByRole("button", { name: "Notebook", exact: true }).click();

  await expect(page.locator(".notebook")).toBeVisible();
  await expect(page.locator(".notebookMarkdown, .notebookCode").first()).toBeVisible();

  const firstCellText = await page.locator(".notebookMarkdown, .notebookCode").first().innerText();
  expect(firstCellText.trim().length).toBeGreaterThan(20);

  await screenshot("notebook-preview", page);
});

test("lists artifact availability for the selected run @screenshots", async ({ page }) => {
  await routeCompleteMockRun(page);
  await openLoadedApp(page);
  await page.getByRole("button", { name: "Artifacts", exact: true }).click();

  await expect(page.locator(".artifactGrid")).toBeVisible();
  await expect(page.locator(".artifact").filter({ hasText: "metadata" })).toBeVisible();
  await expect(page.locator(".artifact").filter({ hasText: "notebook" })).toBeVisible();

  await screenshot("artifact-inventory", page);
});

test("renders structured run trace in artifacts view", async ({ page }) => {
  const summary = {
    run_id: "trace_run",
    source_file: "trace.csv",
    file_sha256: "abcdef",
    created_at: "2026-05-31T00:00:00+00:00",
    row_count: 2,
    column_count: 2,
    artifacts: {
      metadata: true,
      dataset: true,
      semantic: true,
      metric_plan: true,
      analysis_outputs: true,
      dashboard: true,
      validation: true,
      critique: false,
      insights: false,
      notebook: false,
      trace: true
    }
  };
  const bundle = {
    summary,
    metadata: {},
    semantic_understanding: null,
    metric_plan: null,
    analysis_outputs: null,
    dashboard_plan: null,
    validation_report: null,
    dashboard_critique: null,
    analytical_insights: null,
    notebook_available: false,
    trace: {
      run_id: "trace_run",
      job_id: "job-1",
      status: "completed",
      started_at: "2026-05-31T00:00:00+00:00",
      finished_at: "2026-05-31T00:00:01+00:00",
      duration_ms: 1000,
      message: "done",
      events: [
        {
          stage: "metrics",
          event_type: "stage",
          status: "warning",
          started_at: "2026-05-31T00:00:00+00:00",
          finished_at: "2026-05-31T00:00:01+00:00",
          duration_ms: 1000,
          message: "Metric warning",
          error_type: "RuntimeError",
          error_message: "repair used",
          artifact_paths: { metric_plan: "metric.json" }
        }
      ]
    }
  };

  await page.route("**/api/runs", (route) => route.fulfill({ json: [summary] }));
  await page.route("**/api/runs/latest", (route) => route.fulfill({ json: bundle }));

  await page.goto("/");
  await page.getByRole("button", { name: "Artifacts", exact: true }).click();

  await expect(page.getByText("Run Trace")).toBeVisible();
  await expect(page.locator(".traceEvent.warning").filter({ hasText: "metrics" })).toBeVisible();
  await expect(page.getByText("RuntimeError: repair used")).toBeVisible();
});

test("keeps the workspace usable on a mobile viewport @screenshots", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await routeCompleteMockRun(page);
  await openLoadedApp(page);

  await expect(page.locator(".sidebar")).toBeVisible();
  await expect(page.locator(".topbar")).toBeVisible();
  await expect(page.getByRole("button", { name: "Notebook", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Upload dataset", exact: true })).toBeVisible();

  await screenshot("mobile-dashboard", page);
});
