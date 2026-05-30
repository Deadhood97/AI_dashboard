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
  await expect(page.locator(".statGrid")).toBeVisible();
  await expect(page.locator(".runButton").first()).toBeVisible();
}

test("renders latest run workspace from the artifact API @screenshots", async ({ page }) => {
  await openLoadedApp(page);

  await expect(page.getByText("Current Run")).toBeVisible();
  await expect(page.getByRole("button", { name: "Dashboard", exact: true })).toHaveClass(/active/);
  await expect(page.locator(".stat").filter({ hasText: "Rows" })).toBeVisible();
  await expect(page.locator(".chartSpec").first()).toBeVisible();

  await screenshot("dashboard-workspace", page);
});

test("shows analytical insights and validation output @screenshots", async ({ page }) => {
  await openLoadedApp(page);
  await page.getByRole("button", { name: "Insights", exact: true }).click();

  await expect(page.locator(".narrative")).toBeVisible();
  await expect(page.getByText("Validation")).toBeVisible();
  await expect(page.locator(".insightCard").or(page.locator(".cleanState")).first()).toBeVisible();

  await screenshot("insights-validation", page);
});

test("renders notebook cells instead of only metadata @screenshots", async ({ page }) => {
  await openLoadedApp(page);
  await page.getByRole("button", { name: "Notebook", exact: true }).click();

  await expect(page.locator(".notebook")).toBeVisible();
  await expect(page.locator(".notebookMarkdown, .notebookCode").first()).toBeVisible();

  const firstCellText = await page.locator(".notebookMarkdown, .notebookCode").first().innerText();
  expect(firstCellText.trim().length).toBeGreaterThan(20);

  await screenshot("notebook-preview", page);
});

test("lists artifact availability for the selected run @screenshots", async ({ page }) => {
  await openLoadedApp(page);
  await page.getByRole("button", { name: "Artifacts", exact: true }).click();

  await expect(page.locator(".artifactGrid")).toBeVisible();
  await expect(page.locator(".artifact").filter({ hasText: "metadata" })).toBeVisible();
  await expect(page.locator(".artifact").filter({ hasText: "notebook" })).toBeVisible();

  await screenshot("artifact-inventory", page);
});

test("keeps the workspace usable on a mobile viewport @screenshots", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openLoadedApp(page);

  await expect(page.locator(".sidebar")).toBeVisible();
  await expect(page.locator(".topbar")).toBeVisible();
  await expect(page.getByRole("button", { name: "Notebook", exact: true })).toBeVisible();
  await expect(page.locator(".statGrid")).toBeVisible();

  await screenshot("mobile-dashboard", page);
});
