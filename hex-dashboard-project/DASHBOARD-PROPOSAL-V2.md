# Dashboard Proposal V2 — Collapsible Analysis Sections

## Context

This proposal restructures the dashboard from a flat scroll of charts into **collapsible analysis sections**, each mirroring a chapter in Tribe Capital's "A Quantitative Approach to Product-Market Fit." The goal is faithful adaptation of their framework to Anthropic's startup partnerships context, with minimal deviation from the original structure.

### Adaptation principle

Tribe Capital's framework was designed to assess product-market fit of SaaS companies by analysing their customer data. We are adapting it to assess the health of **Anthropic's startup partner portfolio** by analysing API consumption data. The mapping:

| Tribe Capital concept | Our adaptation |
|---|---|
| Company being assessed | Anthropic's partner portfolio |
| Customers | Startup partners (API accounts) |
| Users (MAU) | Active developers / API keys |
| Revenue (MRR) | API billing revenue |
| Customer activity | API calls / token consumption |
| Cohort | Partners onboarded in the same month |
| LTV | Cumulative revenue Anthropic earns from a partner |
| Retention | Partner still making API calls month-over-month |

### What we keep exactly as Tribe Capital presents it

1. The three-analysis structure (Growth Accounting → Cohort Analysis → Distribution)
2. The accounting identities (MAU and Revenue decompositions)
3. The three cohort visualisation approaches (Aging lines → Fixed-age trends → Heatmaps)
4. The CDF distribution chart with dual lines
5. The derived metrics (Quick Ratio, Gross Retention, Net Churn, CMGR)

### What we add (Anthropic-specific)

1. **Credit Economics** — a fourth analysis section not in Tribe Capital, because credits are the investment mechanism unique to this role
2. **Model Mix** — Haiku/Sonnet/Opus breakdown, unique to Anthropic's multi-model pricing
3. **Company drill-down** — Tribe Capital analyses a single company; we analyse a portfolio and need per-partner views

---

## Dashboard Structure

### Tab 1: Portfolio Overview

Six collapsible sections. Each section contains multiple **view modes** (tabs within the section) that show the same underlying data through different chart types — exactly as Tribe Capital presents multiple visualisations per analysis.

---

### Section 0: Portfolio Summary *(always open, not collapsible)*

**Purpose:** At-a-glance portfolio health. The "executive summary" row.

**Contents:**
- KPI cards: Total Revenue (expandable by model), Credits Deployed, Active Developers
- Top Performers table with credit payback progress bars
- Collapsed-state summaries for each section below (e.g. "QR 2.1x · 69 MAU · 92% gross retention")

---

### Section 1: ▼ Growth Accounting — Users

**Maps to:** Tribe Capital Analysis 1, applied to developer/user data
**SQL source:** `MAU_Growth_Accounting` query from the gist

**Tribe Capital presents this as:**
1. Total line chart with CMGR overlays
2. Growth accounting decomposition (stacked bar)
3. Derived metrics (Quick Ratio, Gross Retention)

**Our view modes:**

#### Mode A: Growth Accounting *(default)*
Stacked bar chart — the core Tribe Capital visualisation.
- Above axis: Retained (dark blue), New (green), Resurrected (light green)
- Below axis: Churned (red)
- One bar per month, aggregated across all partners
- **Filterable by company** — chip toggles to show single-company or portfolio-level

#### Mode B: Quick Ratio
Line chart showing developer Quick Ratio over time.
- Formula: `(New + Resurrected) / Churned`
- Benchmark lines at 1.0x (flat) and 2.0x (strong)
- Skips first month per company (no churn data at t=0)

#### Mode C: MAU Trend
Monthly Active Developers line chart.
- Per-company lines + dotted total line
- Equivalent to Tribe Capital's "total line with CMGR overlay"
- We show CMGR as a KPI rather than an overlay to keep the chart clean

**Section KPIs (shown in collapsed state):**
- Current MAU (total)
- Developer Quick Ratio (latest month)
- CMGR (3-month)

---

### Section 2: ▼ Growth Accounting — Revenue

**Maps to:** Tribe Capital Analysis 1, applied to revenue data
**SQL source:** `MRR_Growth_Accounting` query from the gist

**Tribe Capital presents this as:**
1. Revenue line with CMGR overlays (3, 6, 12-month)
2. Revenue growth accounting decomposition (stacked bar with gains above, losses below)
3. Derived metrics annotations

**Our view modes:**

#### Mode A: Growth Accounting *(default)*
Stacked bar chart — the revenue decomposition.
- Above axis: Retained (dark blue), New (green), Expansion (purple), Resurrected (light green)
- Below axis: Churned (red), Contraction (amber)
- Aggregated across portfolio

#### Mode B: Revenue by Company
Line chart with company filter chips + Revenue/Tokens toggle.
- Same chart, two units — tokens and revenue are the same activity
- Per-company lines, toggleable

#### Mode C: Revenue by Model
Two charts side by side:
- Left: Total Revenue by Model (stacked bar per company — Sonnet/Opus/Haiku)
- Right: Portfolio Revenue by Model over time (stacked area)

**Section KPIs (shown in collapsed state):**
- Total MRR (latest month)
- Revenue CMGR (3-month)
- Gross Retention %

---

### Section 3: ▼ Cohort Analysis

**Maps to:** Tribe Capital Analysis 2
**SQL source:** `Cohorts_Cumulative_M` and `MAU_Retention_by_Cohort` queries from the gist

This is the most chart-rich section. Tribe Capital explicitly presents three visualisation "approaches" for cohort data. We replicate all three.

**Tribe Capital's three approaches:**
- **Approach A (Cohort Aging):** Multi-line graph, each line = one cohort, x-axis = months since onboarding, y-axis = metric. Shows how cohorts age.
- **Approach B (Fixed-Age Trend):** Pick a fixed age (e.g. month 6), plot the metric across cohorts. Shows whether newer cohorts are better/worse. Includes cohort size bars.
- **Approach C (Heatmap):** Matrix with rows = cohorts, columns = age. Reveals age effects (vertical), cohort effects (horizontal), seasonality (diagonal).

**Our view modes (sub-tabs within the section):**

#### Mode A: LTV — Cohort Aging Lines *(default)*
Multi-line chart, one line per partner.
- X-axis: Months since onboarding
- Y-axis: Cumulative revenue (LTV)
- Look for: Super-linear (curving up) = expanding partners. Sub-linear (flattening) = declining.
- **Clickable:** Click a partner's line → navigates to their company detail tab

#### Mode B: LTV — Heatmap
Heatmap matrix.
- Rows: Partners (or onboarding cohorts when we have more partners)
- Columns: Month 0, Month 1, ... Month N
- Color: Cumulative LTV (purple gradient)
- Reveals: Which partners accelerated early vs late, relative magnitude

#### Mode C: Developer Retention — Cohort Aging Lines
Multi-line chart showing retention decay.
- X-axis: Months since cohort start
- Y-axis: % of cohort developers still active
- Per-company lines
- 50% benchmark line
- Look for: Curve flattening = stable retention floor found

#### Mode D: Developer Retention — Heatmap
Heatmap matrix.
- Rows: Partners
- Columns: Cohort age (M0, M1, M2...)
- Color: Retention % (green → red)
- Reveals: Age effects (do all partners lose devs at month 3?), cohort effects (is one partner uniquely sticky?)

#### Mode E: Revenue Retention
Line chart showing revenue at month N / revenue at month 0.
- Per-company lines
- 1x baseline (dashed)
- Values above 1x = net expansion
- Look for: Stabilisation (asymptote) = predictable unit economics

#### Mode F: Gross Revenue Retention
Portfolio-level line showing retained revenue / prior period revenue.
- 70% benchmark line (B2B SaaS standard)
- This is the "floor" — how much revenue survives without any new business

**Section KPIs (shown in collapsed state):**
- Average LTV at month 12
- Logo retention at month 6
- Revenue retention at month 12

**Future enhancement (noted in project log):** When the portfolio grows beyond ~10 partners, Approach B (fixed-age trends with cohort size bars) becomes more valuable than Approach A. Currently with 3 partners, Approach A is more readable.

---

### Section 4: ▼ Distribution of PMF

**Maps to:** Tribe Capital Analysis 3
**No direct SQL source** — requires separate computation from raw data

**Tribe Capital presents this as:**
1. CDF chart with dual lines (% of customers vs % of revenue)
2. L28 engagement distribution (days active per month)

**Our view modes:**

#### Mode A: Revenue Concentration (CDF) *(default)*
Dual-line CDF chart.
- X-axis: Cumulative % of partners (sorted by revenue, descending)
- Y-axis: Cumulative % of total portfolio revenue
- Diagonal reference line (45° = perfectly even distribution)
- Hover shows partner name + revenue
- Interpretation: Separation between the curve and diagonal = concentration risk

#### Mode B: Engagement Distribution (L28)
Bar chart / histogram.
- X-axis: Days with API calls per 28-day window (1-28)
- Y-axis: % of developers at each engagement level
- Aggregated across portfolio or filterable by company
- Median line + top/bottom quintile markers
- Interpretation: Bimodal = some power users, some experimenters. Uniform = healthy adoption.

**Section KPIs (shown in collapsed state):**
- Top partner as % of total revenue
- Median L28 engagement
- % of developers in "power user" quintile (≥14 days active)

---

### Section 5: ▼ Credit Economics

**NOT in Tribe Capital** — this is Anthropic-specific. The credit program is the investment mechanism; this section measures ROI on that investment.

**View modes:**

#### Mode A: Payback Curves *(default)*
Line chart per partner.
- X-axis: Months since onboarding
- Y-axis: Cumulative (Revenue × Gross Margin) − Credits
- Breakeven line at y=0
- Partners crossing breakeven = payback achieved

#### Mode B: Credit Burn & Conversion
Table or timeline showing each partner's credit lifecycle:
- Credits granted, consumed, remaining
- Monthly burn rate + projected exhaustion date
- Post-credit status: Converted / Expanding / Flat / Declining / Dormant

**Section KPIs (shown in collapsed state):**
- Portfolio credit ROI (total rev / total credits)
- Partners past breakeven: X of Y
- Average payback period

---

## Tab 2+: Company Detail

Same section structure, but single-company scope. Each section shows the same analysis types but for one partner only.

### Company Summary *(always open)*
- Hero card (name, stage, vertical, location, description)
- KPIs: Total Revenue (expandable by model), Latest MRR, Token CAGR, Credit ROI, Active Devs, Dev Quick Ratio

### ▼ Growth Accounting — Users
Modes: `Growth Accounting` | `Quick Ratio` | `Cohort Retention`
- GA: Stacked bar for this company's developer decomposition
- QR: Line chart of this company's developer quick ratio over time
- Retention: This company's developer cohort retention curve

### ▼ Growth Accounting — Revenue
Modes: `Growth Accounting` | `Revenue & Tokens` | `By Model` | `Model Mix`
- GA: Stacked bar (same as portfolio but single-company)
- Revenue & Tokens: Dual line charts
- By Model: Stacked area showing Sonnet/Opus/Haiku revenue
- Model Mix: 100% stacked area showing proportions over time

### ▼ Adoption & Reliability
Modes: `API Calls & Devs` | `Latency & Errors` | `Engagement Depth`
- Dual-axis chart: API call volume bars + active developer line
- Latency + error rate dual-axis
- L28 engagement distribution for this company

---

## UI Pattern: Collapsible Sections with View Modes

```
┌─────────────────────────────────────────────────────┐
│ ▼ Growth Accounting — Users          QR 2.1x · 69 MAU │
│                                                       │
│  ┌──────────────────┬─────────────┬───────────┐       │
│  │ Growth Accounting│ Quick Ratio │ MAU Trend │       │
│  └──────────────────┴─────────────┴───────────┘       │
│                                                       │
│  ┌─────────────────────────────────────────────┐      │
│  │                                             │      │
│  │  (active chart renders here based on        │      │
│  │   selected mode tab)                        │      │
│  │                                             │      │
│  └─────────────────────────────────────────────┘      │
│                                                       │
└─────────────────────────────────────────────────────────┘
```

**Behaviour:**
- Click section header → collapse/expand (with smooth animation)
- Collapsed state shows section title + summary KPIs in the header bar
- Mode tabs switch which chart is visible (no page scroll, no re-render — just show/hide)
- All sections start expanded by default on page load
- Company filter chips appear within relevant modes (not at section level)
- Sections remember their expanded/collapsed state during the session

**Interaction: Chart → Company drill-down**
- On portfolio cohort charts (LTV lines, retention lines), clicking a company's trace navigates to that company's detail tab
- Hover hint: "Click company line to drill down →"

---

## Mapping to Tribe Capital's Original Sequence

The essay presents analyses in this order with specific rationale:

| Order | Tribe Capital | Our Section | Why this order |
|---|---|---|---|
| 1 | Growth Accounting | Sections 1 + 2 | "Provides the top-line growth picture" — start with the headline |
| 2 | Cohort Analysis | Section 3 | "Provides lifetime of a customer picture" — deeper layer |
| 3 | Distribution of PMF | Section 4 | "Provides degree of variability" — the nuance |
| — | (not in TC) | Section 5 | Credit Economics — Anthropic-specific, at the end because it's about our investment, not partner health |

We split Growth Accounting into Users (Section 1) and Revenue (Section 2) because they use different accounting identities (users = binary active/inactive; revenue = continuous with expansion/contraction). Tribe Capital presents them together but distinguishes them conceptually. Separating them makes each section more focused.

---

## Implementation Notes

### What's already built and stays
- All chart computations (revenue GA, dev GA, cohort LTV, retention, heatmaps, concentration)
- Top performers table with credit payback bars
- Company filter chips on revenue chart
- Revenue/tokens toggle
- Expandable KPI cards
- Clickable chart → company navigation

### What changes
- Flat section headers → collapsible sections with mode tabs
- Charts grouped into sections instead of sequential
- Some charts that are currently always visible become mode-switchable
- Add CMGR display (currently not shown)
- Add cohort Approach B (fixed-age trend) when portfolio grows

### Data generation needed
- L28 engagement distribution already exists in data
- Developer cohort data already generated
- No new data needed — just UI restructuring

---

## Project Log — Insights for Future Adaptation

1. **Approach B (fixed-age trends) deferred** — With only 3 partners, Approach A (aging lines) is more readable. When portfolio reaches ~10+ partners, Approach B becomes the primary view and Approach A becomes secondary. Flag for re-evaluation at that scale.

2. **Revenue Quick Ratio removed** — User feedback: not yet well-understood. The growth accounting stacked bar communicates the same information more intuitively. Consider re-introducing as an annotation on the GA chart rather than a separate chart.

3. **Credit Economics is novel** — No direct Tribe Capital equivalent. The payback curve is our invention. Worth validating with the Anthropic team whether this matches how they think about credit ROI internally.

4. **Token CAGR = Revenue CAGR** — In our synthetic data, these are identical because revenue = tokens × fixed blended rate. In production, model mix shifts would cause divergence. The dashboard correctly shows both but they'll only differ with real data.

5. **Distribution section is thin** — With 3 partners, the CDF chart is trivially three points. The L28 engagement distribution is more interesting at this scale. Consider promoting L28 to the default mode and demoting CDF until portfolio grows.

6. **Heatmap rows = partners, not cohorts** — Tribe Capital's heatmap rows are monthly onboarding cohorts (dozens of rows). Ours are partners (3 rows). When portfolio grows, we should switch to cohort-month rows for the heatmap to match the original pattern-recognition value (vertical/horizontal/diagonal effects).

7. **Collapsible sections with mode tabs** — This UI pattern is not in Tribe Capital (they use a linear essay format). It's our adaptation for a dashboard context where space is limited and the user needs to context-switch between views. The mode tabs specifically solve the problem of showing multiple visualisations of the same data (which Tribe Capital does by placing charts sequentially in prose).

---

## References

- [A Quantitative Approach to Product-Market Fit (Tribe Capital)](https://tribecap.co/essays/a-quantitative-approach-to-product-market-fit)
- [Growth Accounting & LTV SQL (Social Capital)](https://gist.github.com/hsurreal/4062f2639d4bb6fab6fb)
- Tribe Capital's three analysis types: Growth Accounting, Cohort Analysis, Distribution of PMF
- SQL gist implements 10 queries: DAU, WAU, MAU, First_DT, MAU_Growth_Accounting, MAU_Retention_by_Cohort, MRR_Growth_Accounting, Cohorts_Cumulative (weekly), Cohorts_Cumulative_M (monthly), DAU_Growth_Accounting
