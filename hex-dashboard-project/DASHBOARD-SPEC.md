# Dashboard Specification — Anthropic EMEA Startup Partnerships

## Strategic Context

The startup credit program is fundamentally a **customer acquisition cost (CAC) play**. Credits are an investment to create switching costs and long-term revenue:

1. **Land** — Deploy credits ($25K base) to remove the cost barrier for startups to build on Claude
2. **Integrate** — Startup builds prompts, chains, and product features on Claude's API. Every line of integration code increases switching cost.
3. **Lock-in** — Once Claude is wired into their product loop, migrating to OpenAI/Gemini means rewriting prompts, re-testing behaviour, retraining the team. This is the moat.
4. **Convert** — Credits exhaust → startup starts paying. The bet has paid off.
5. **Expand** — Usage scales with their growth. Revenue compounds.

The dashboard exists to answer: **is this investment strategy working, and which startups should we double down on vs. cut loose?**

What we're really measuring isn't just volume — it's **depth of integration**:
- A startup burning tokens on experiments = low value
- A startup with Claude in their core product loop = high value, even at lower absolute token count
- Consistency (daily API calls = production; sporadic bursts = experimenting)
- Breadth of model usage (multiple models = real system architecture, not one prompt)
- Growth trajectory (small but accelerating = they've found PMF with Claude in the loop)

## Scope

This dashboard monitors **direct API partners only** — startups that call Anthropic's API with their own API keys and receive credit grants through the partnerships program.

It does not cover:
- Cloud provider access (AWS Bedrock / Google Vertex) — Anthropic has limited visibility into usage routed through cloud marketplaces
- Embedded/platform deals (e.g. Notion) — these are enterprise agreements where the platform is the customer, not individual end-users
- Self-serve customers — no credit grant, no partnership relationship

## Data Sources

All metrics derive from data Anthropic can directly observe:

| Source | What it contains |
|---|---|
| API logs | Every request — tokens (input/output), model used, timestamp, API key |
| Billing | Revenue per account, per model, per period |
| Credit ledger | Grants issued, credits consumed, balance remaining |
| Console / Workspace | Seats, API keys created, projects (if partner uses Console) |

We do **not** have access to: partner ARR, burn rate, runway, headcount, end-user metrics, LTV of their customers, or any internal financial data.

## Analytical Framework

Adapted from Tribe Capital / Social Capital's growth accounting framework ([SQL reference](https://gist.github.com/hsurreal/4062f2639d4bb6fab6fb), [essay](https://tribecap.co/essays/a-quantitative-approach-to-product-market-fit)). Their framework treats product-market fit assessment like financial accounting — standardised, universal metrics applied to understand business health. We adapt it from SaaS customer analysis to **API partner analysis**.

### Core Principle: Growth Accounting

Every period, the active population (users or revenue) can be decomposed into mutually exclusive categories. This is not a model — it's an **accounting identity**. The numbers must balance.

**User identity:**
```
MAU(t) = Retained(t) + New(t) + Resurrected(t)
MAU(t-1) = Retained(t) + Churned(t)
```

**Revenue identity:**
```
Revenue(t) = Retained(t) + New(t) + Resurrected(t) + Expansion(t)
Revenue(t-1) = Retained(t) + Churned(t) + Contraction(t)
```

Revenue has two extra categories (expansion, contraction) because users who are present in both periods can change their spend level. User accounting is binary (active or not); revenue accounting is continuous.

### Three Analyses (from Tribe Capital)

Tribe Capital's PMF framework uses three standardised analyses. We apply all three, adapted to our API partner data:

#### 1. Growth Accounting

Decompose growth into its components to understand **quality of growth**, not just rate.

**For users (developers/API keys):**

| Category | Definition (our context) |
|---|---|
| **New** | Developer whose first API call was this month (`first_month = current_month`) |
| **Retained** | Active last month AND active this month |
| **Resurrected** | Inactive last month, active this month, but not new (`first_month ≠ current_month AND not in last month`) |
| **Churned** | Active last month, inactive this month (shown as negative) |

**For revenue (API spend):**

| Category | Definition |
|---|---|
| **New** | Revenue from partners in their first billing month |
| **Retained** | Revenue carried forward: `min(this_month, last_month)` for partners active both months |
| **Expansion** | `this_month - last_month` for partners spending MORE than last month |
| **Contraction** | `last_month - this_month` for partners spending LESS (but still active) — shown negative |
| **Resurrected** | Revenue from previously churned partners who return |
| **Churned** | Lost revenue from partners who stopped entirely — shown negative |

**Key derived metrics:**

```
Quick Ratio = (New + Resurrected + Expansion) / (Churned + Contraction)
```
- < 1.0 → shrinking. Losing more than gaining.
- 1.0–1.5 → treading water. For every 3 lost, gaining 3–4.5 back.
- 1.5–2.0 → healthy growth.
- > 2.0 → strong expansion. Typical of strong B2B SaaS.

```
Gross Retention = Retained Revenue / Prior Period Revenue
```
- Measures the "floor" — how much revenue survives without any new business.
- B2B SaaS benchmark: >70% is healthy.

```
Net Churn = (Churned + Contraction - Resurrected - Expansion) / Prior Revenue
```
- Negative net churn = expansion exceeds losses. The holy grail.
- `Growth Rate ≈ New Rate - Net Churn`

#### 2. Cohort Analysis

Track cohorts of partners onboarded in the same month. For each cohort, measure at fixed ages (month 1, 2, 3, ...) after onboarding:

**Three cohort metrics:**

| Metric | What it measures | What to look for |
|---|---|---|
| **Cumulative LTV** | Total revenue per partner at fixed months post-onboarding | **Super-linear** (curving up) = partners spend more over time. **Sub-linear** (flattening) = declining engagement. |
| **Revenue Retention %** | Cohort's current spend / cohort's first-month spend | >100% = net expansion. Look for stabilisation (asymptote). |
| **Logo Retention %** | % of cohort partners still active at month X | Look for the curve to flatten — that's your steady-state retention rate. |

**Visualisation (from Tribe Capital):**
- **Line graphs**: Each cohort as a line, x-axis = months since onboarding
- **Fixed-age trends**: Pick a fixed age (e.g. month 6) and plot across cohorts — are newer cohorts retaining better?
- **Heatmaps**: Rows = cohort, columns = age. Reveals three effects:
  - Vertical patterns = age effects (all cohorts behave similarly at month X)
  - Horizontal patterns = cohort effects (a specific cohort is unusually good/bad)
  - Diagonal patterns = calendar effects (seasonality)

**SQL approach** (from the reference gist):
```sql
-- Cumulative LTV per cohort user
cum_amt_per_user = cumulative_revenue / cohort_size_at_onboarding
-- Retention
retained_pctg = active_users_at_age_N / cohort_size_at_onboarding
```

#### 3. Distribution of PMF (Concentration Analysis)

From Tribe Capital: plot CDF of customers vs CDF of revenue on a log scale.

**Adapted for our context:**
- X-axis: cumulative % of partners (sorted by revenue, descending)
- Y-axis: cumulative % of total portfolio revenue

**What it reveals:**
- "80/20" = top 20% of partners generate 80% of revenue → high concentration risk
- "60/40" = more diversified portfolio
- Separation between the customer distribution line and revenue distribution line shows concentration

**Engagement distribution (L28 adaptation):**
- Instead of "days active per month", we use: **days with API calls per 28-day window**
- Median = typical partner engagement level
- Top quintile = power partners (deeply integrated)
- Bottom quintile = at-risk (experimenting or dormant)

---

## Dashboard Structure

### Tab 1: Portfolio Overview
Multi-company view. High-level table of all partners with sortable columns. At a glance: who's growing, who's churning, where are we deploying credits.

### Tab 2+: Company Detail
Click into any company for granular breakdown across three sections:

---

## Section 1: Users & Adoption

**Core metric:** Monthly Active Developers (developers/API keys making at least 1 API call in the month).

**Charts:**
1. **Developer Growth Accounting** — stacked bar chart showing New, Retained, Resurrected above the axis; Churned below. This is the primary chart.
2. **Developer Quick Ratio** — line chart with benchmark lines at 1.0 (flat) and 2.0+ (strong)
3. **Developer Retention Curve** — cohort lines showing % of developers still active at month 1, 2, 3...
4. **Total Active Developers** — simple line showing MAD over time

**Note on "users":** This depends on how the partner integrates. If they use Anthropic Console with workspace members, we see real seat count. If they use raw API keys, we use distinct active API keys as a proxy. The dashboard should flag which measurement is in use per partner.

---

## Section 2: Consumption & Revenue

Token consumption and revenue are the **same underlying activity measured in different units** (Revenue = Tokens × Price per Token). They belong in one section, not two.

**Why they're shown together:** A partner could increase token volume while decreasing revenue (migrating Opus → Haiku), or vice versa. The model mix is the bridge between the two.

**Charts:**
1. **Revenue Growth Accounting** — stacked bar: New, Retained, Expansion, Resurrected above axis; Contraction, Churned below. The core Tribe Capital chart.
2. **Revenue Quick Ratio** — line with 1.0x and 4.0x benchmarks
3. **Gross Retention %** — line showing retained / prior period
4. **Monthly Revenue** — line chart, total and by model
5. **Monthly Tokens** — line chart, total and by model
6. **Model Mix %** — 100% stacked area showing Haiku/Sonnet/Opus proportions over time
7. **Revenue by Model** — stacked area (absolute $) showing which models drive revenue
8. **Cohort LTV Curves** — cumulative revenue per partner at fixed ages post-onboarding. Super-linear = expanding. Sub-linear = declining.

**Token CAGR:**
```
CAGR = (Latest Month / First Month) ^ (12 / months_elapsed) - 1
```
Annualised growth rate. The single best "is this partner scaling?" number.

---

## Section 3: Credit Economics

Credits are an **investment**, not consumption. This section answers: was our bet worth it?

**Metrics:**
- **Credits granted** — total $ deployed to this partner
- **Credits consumed** — how much of the grant they've used
- **Burn rate** — monthly credit consumption, with projected exhaustion date
- **Cumulative revenue** — total $ billed (post-credit or if spend exceeds grant)
- **Payback** — months until cumulative revenue ≥ credits granted
- **Conversion status** — did they hit the credit wall and start paying, or go dark?

**Payback curve chart:** X-axis = months since onboarding, Y-axis = cumulative (revenue × GM − credits). Crosses zero = payback achieved.

**Post-credit behaviour categories:**
- **Converted** — credits exhausted, now paying. Best outcome.
- **Expanding** — still on credits but usage growing. On track.
- **Flat** — using credits at steady rate. Needs nudge.
- **Declining** — usage dropping. Intervention needed.
- **Dormant** — no API calls in 30+ days. At risk.

---

## Portfolio Overview — Top Performers Table

Sortable table showing all partners with key columns:

| Column | What it shows |
|---|---|
| Company | Name + stage |
| Token CAGR | Annualised growth in consumption |
| Monthly Revenue | Latest month billing |
| Revenue Δ MoM | Month-over-month revenue change |
| Credit ROI | Revenue / Credits granted |
| Active Devs | Current month active developers |
| Dev Quick Ratio | (New + Resurrected) / Churned — developer growth quality |
| Rev Quick Ratio | (New + Expansion + Resurrected) / (Contraction + Churned) |
| Gross Retention | Retained revenue / prior period revenue |
| Model Mix | Primary model used (visual indicator) |
| Status | Expanding / Stable / Contracting / Dormant |

Small companies growing fast (high CAGR, low absolute revenue) surface alongside large stable accounts. This is the point — CAGR catches breakout partners early.

**Portfolio-level concentration chart:** CDF of partners vs revenue. Flags if portfolio is over-dependent on one account.

---

## Tiered Metric Importance

### Tier 1 — Job-defining (your performance is measured on these)
1. **Credit Payback** — months until revenue ≥ credits. The ROI on your budget.
2. **Cohort Logo Retention** — of partners onboarded in period X, what % still active? Your portfolio health.
3. **Token/Revenue Growth (CAGR)** — are partners scaling? The primary success signal.

### Tier 2 — Portfolio narrative (tells the story in reviews)
4. **Revenue Quick Ratio** — growth quality. Are you adding more than you're losing?
5. **Gross Retention** — the floor. How much revenue survives without new business?
6. **Revenue Concentration** — top partner as % of total portfolio revenue. Diversification risk.
7. **Cohort LTV Curves** — are partners expanding or declining over time?

### Tier 3 — Operational depth (day-to-day management)
8. **Developer Quick Ratio** — is the partner's team growing or shrinking on Claude?
9. **Model Mix Evolution** — partner moving Haiku → Sonnet → Opus = building more complex features = stickier.
10. **Time-to-Activation** — days from credit grant to first API call. Measures onboarding effectiveness.
11. **Dormancy Tracking** — days since last API call. Early churn warning.
12. **Net Churn** — expansion minus losses. Negative = the holy grail.

---

## References

- [Growth Accounting & LTV SQL (Social Capital)](https://gist.github.com/hsurreal/4062f2639d4bb6fab6fb) — complete SQL implementation of growth accounting, cohort LTV, and retention analysis
- [A Quantitative Approach to Product-Market Fit (Tribe Capital)](https://tribecap.co/essays/a-quantitative-approach-to-product-market-fit) — three standardised analyses: growth accounting, cohort analysis, distribution of PMF
- Framework deliberately excludes unit economics, margins, CAC, profitability — those are addressed separately

---

## Design Notes

- Hex-inspired aesthetic (light/dark theme)
- Plotly interactive charts, self-contained HTML
- Animations: staggered card entry, KPI count-up, scroll-reveal, tab crossfade
- All data is synthetic for demonstration purposes
