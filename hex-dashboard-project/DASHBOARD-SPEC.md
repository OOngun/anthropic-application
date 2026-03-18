# Dashboard Specification — Anthropic EMEA Startup Partnerships

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

## Dashboard Structure

### Tab 1: Portfolio Overview
Multi-company view. High-level table of all partners with sortable columns. At a glance: who's growing, who's churning, where are we deploying credits.

### Tab 2+: Company Detail
Click into any company for granular breakdown across three sections:

---

## Section 1: Users & Adoption

Adapted from Social Capital's growth accounting framework for user growth.

**Core metric:** Monthly Active Developers (developers/API keys making at least 1 API call in the month).

**Growth accounting decomposition:**
- **New** — developers who made their first API call this month
- **Retained** — active last month and active this month
- **Resurrected** — inactive for 1+ months, now active again
- **Churned** — active last month, inactive this month

**Quick Ratio (Developers):**
```
Quick Ratio = (New + Resurrected) / Churned
```
- < 1.0 → shrinking (losing more devs than gaining)
- 1.0–1.5 → for every 3 users lost, gaining 3–4.5 back. Treading water.
- 1.5–2.0 → healthy growth
- > 2.0 → strong expansion

**Retention curve:** Cohort-based. Of developers who started in month X, what % are still active in X+1, X+2, etc.

**Note on "users":** This depends on how the partner integrates. If they use Anthropic Console with workspace members, we see real seat count. If they use raw API keys, we use distinct active API keys as a proxy. The dashboard should flag which measurement is in use per partner.

---

## Section 2: Consumption & Revenue

Token consumption and revenue are the **same underlying activity measured in different units** (Revenue = Tokens × Price per Token). They belong in one section, not two.

**Why they're shown together:** A partner could increase token volume while decreasing revenue (migrating Opus → Haiku), or vice versa. The model mix is the bridge between the two.

**Growth accounting decomposition (applied to monthly spend):**
- **New revenue** — from partners in their first billing month
- **Expansion** — existing partners spending more than last month
- **Contraction** — existing partners spending less than last month
- **Churned revenue** — partners who stopped spending entirely
- **Resurrected revenue** — previously churned partners who started spending again

**Quick Ratio (Revenue):**
```
Quick Ratio = (New + Expansion + Resurrected) / (Contraction + Churned)
```

**Model mix breakdown:**
- Tokens by model (Haiku / Sonnet / Opus) — volume signal
- Revenue by model — value signal (same tokens, different prices)
- Model migration over time — are they moving up or down the model ladder?

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

**Payback curve chart:** X-axis = months since onboarding, Y-axis = cumulative (revenue − credits). Crosses zero = payback achieved.

**Post-credit behavior categories:**
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
| Dev Growth | MoM change in active developers |
| Model Mix | Primary model used (visual indicator) |
| Status | Expanding / Stable / Contracting / Dormant |

Small companies growing fast (high CAGR, low absolute revenue) surface alongside large stable accounts. This is the point — CAGR catches breakout partners early.

---

## Tiered Metric Importance

### Tier 1 — Job-defining (your performance is measured on these)
1. **Credit Payback** — months until revenue ≥ credits. The ROI on your budget.
2. **Cohort Logo Retention** — of partners onboarded in period X, what % still active? Your portfolio health.
3. **Token/Revenue Growth (CAGR)** — are partners scaling? The primary success signal.

### Tier 2 — Portfolio narrative (tells the story in reviews)
4. **Net Revenue Retention (spend-based)** — same partner's spend now vs 12 months ago. >100% = expansion.
5. **Quick Ratio (consumption)** — new + expansion + resurrected / contraction + churned. Growth quality.
6. **Revenue Concentration** — top partner as % of total portfolio revenue. Diversification risk.

### Tier 3 — Operational depth (day-to-day management)
7. **Model Mix Evolution** — partner moving Haiku → Sonnet → Opus = building more complex features = stickier.
8. **Time-to-Activation** — days from credit grant to first API call. Measures onboarding effectiveness.
9. **Dormancy Tracking** — days since last API call. Early churn warning.

---

## Design Notes

- Dark theme, Hex-inspired aesthetic
- Plotly interactive charts, self-contained HTML
- Animations: staggered card entry, KPI count-up, scroll-reveal, tab crossfade
- All data is synthetic for demonstration purposes
