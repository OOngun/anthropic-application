# Archived Features

## SaaS Health Charts (Social+Capital style)
**Archived from:** commit 7ce845a (2026-03-25)
**Reason:** Broke LTV curves on company detail views
**Files:** `saas_health_charts.patch`

### What it added
- **Cumulative MRR Build-Up** — Stacked bar: Beginning MRR + Net New MRR
- **Gross MRR Churn (%)** — Line chart with 3% benchmark line
- **New MRR vs Cancelled MRR** — Mirrored bar chart
- **Expansion Breakdown** — New + Expansion vs Cancelled (mirrored bars)
- **SaaS Health section** in company detail tabs with mode tabs
- **Case study integration** for CS01 (WriteFlow) with Quick Ratio & Avg Gross Churn KPIs

### To restore
```bash
cd hex-dashboard-project
git apply archived/saas_health_charts.patch
```
