# Dashboard Design Guide

This guide is a compact rule set for AI-generated analytical dashboards. It is based on common dashboard design guidance from Tableau, Microsoft Power BI, and dashboard design research.

## Purpose First

- Start with the audience and decision being supported.
- Prefer dashboards that answer a few important questions clearly.
- Put the most important business signal first.
- Do not include details unless they are useful for monitoring or decision-making.

## Layout

- Keep the dashboard compact.
- Prefer two or three strong views over many weak views.
- Use no more than two overview charts and three supporting question views in the MVP.
- Put the highest-level information near the top-left or top of the dashboard.
- Order content from overview to diagnosis to supporting detail.
- Avoid duplicate charts that answer the same question.

## Chart Selection

- Use bars for comparing categories.
- Use lines only for continuous time or ordered sequences with at least two meaningful x-values.
- Use scatter plots only when both axes are numeric and varied.
- Use tables for detail, exceptions, and ranked lists that need several columns.
- Limit dashboard tables to 25 visible rows or fewer.
- Avoid chart variety for its own sake.
- Avoid pie, donut, gauge, 3D, and decorative charts in the MVP.

## Readability

- Limit categories, colors, and visible series.
- Avoid large legends and crowded stacked bars.
- Do not mix unrelated grains in one chart, such as varieties, regions, and designations in the same ranked bar.
- Do not rank categories by averages unless the sample size is visible and defensible.
- Prefer minimum sample-size filters for ratings, scores, averages, and rankings.
- Avoid raw text tables with many long rows; summarize text fields instead.

## Analytical Grounding

- Every chart must answer a named question.
- Every KPI must come from a scalar output or a clearly justified aggregation.
- Use computed facts for claims; label assumptions and limitations separately.
- Surface missingness, filtering, and sample-size limitations when they affect interpretation.
- Hide or repair charts that are technically renderable but analytically misleading.

## Validation Rules

- Reject charts whose source output is missing or empty.
- Reject line charts with fewer than two x-values.
- Reject scatter plots with non-numeric or near-constant axes.
- Reject average/rating rankings without sample-size support.
- Reject high-cardinality raw tables as dashboard visuals.
- Prefer fewer, clearer charts after validation repair.

## Sources

- Tableau, "Best Practices for Effective Dashboards": https://help.tableau.com/current/pro/desktop/en-gb/dashboards_best_practices.htm
- Tableau, "Visual Best Practices": https://help.tableau.com/current/pro/desktop/en-us/visual_best_practices.htm
- Microsoft Learn, "Tips for designing a great Power BI dashboard": https://learn.microsoft.com/en-sg/power-bi/create-reports/service-dashboards-design-tips
- Sarikaya et al., "Toward a Scalable Census of Dashboard Designs in the Wild": https://arxiv.org/abs/2306.16513
