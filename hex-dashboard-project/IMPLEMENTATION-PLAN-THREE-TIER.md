# Implementation Plan: Three-Tier Progressive Disclosure

## Summary

Restructure the dashboard from its current flat layout (Pulse tab with collapsible sections + company tabs) into a three-tier progressive disclosure model:

- **Tier 1: Ecosystem Pulse** — 10-second health check, no per-partner breakdowns
- **Tier 2: Partner List** — scoreboard and navigation layer, one row per company
- **Tier 3: Partner Detail** — full drill-down per company

The core discipline: **nothing moves up a level unless it changes a decision at that level.**

---

## Phase 1: Data Foundation

### 1a. Add CMGR computation
Currently missing entirely (flagged as critical gap in TC critique).

```python
def cmgr(series, months):
    """Compound Monthly Growth Rate over trailing N months."""
    end = series.iloc[-1]
    start = series.iloc[-(months + 1)]
    return (end / start) ** (1 / months) - 1 if start > 0 else 0
```

Compute for portfolio-level token consumption:
- `cmgr3` — trailing 3-month
- `cmgr6` — trailing 6-month
- `cmgr12` — trailing 12-month

Also compute per-partner CMGR3 for the partner list.

### 1b. Compute latest-month GA percentages
For the waterfall bars in Tier 1. Take the latest month from `agg_rev_ga` and express each component as % of prior month total.

### 1c. Compute Net Churn
```
net_churn = (churned + contraction - resurrected - expansion) / prior_revenue
```
Portfolio-level and per-partner.

### 1d. Generate additional synthetic partners
Add 5-7 more synthetic partners to stress-test the Partner List layout:

| Partner | Profile | Purpose |
|---|---|---|
| SynthCo Alpha | High volume, steady growth, month 18 | Healthy baseline |
| SynthCo Beta | Low volume, explosive CAGR, month 4 | Breakout detection |
| SynthCo Gamma | Dormant — last active 35 days ago | Dormancy signal |
| SynthCo Delta | Collapsing QR (was 3.0, now 0.7) | Intervention signal |
| SynthCo Epsilon | Brand new, month 1, just got credits | New partner |
| SynthCo Zeta | High volume but Haiku-only, flat growth | Volume without depth |
| SynthCo Eta | Low volume but 100% Opus, high strategic | Strategic value |

This makes the partner list meaningful (8-10 rows) and the concentration CDF viable.

**Files:** Update `data/generate_data.py` or add generation logic to `build_dashboard.py`.

---

## Phase 2: Tier 1 — Ecosystem Pulse

### 2a. Strip current Pulse tab to Tier 1 only

**Remove from Pulse tab:**
- All 4 collapsible analysis sections (Growth Accounting — Users, Growth Accounting — Revenue, Cohort Analysis, Distribution of PMF)
- These analyses move to Tier 3 (partner detail)

**Keep in Pulse tab:**
- Nothing — rebuild from scratch using `pulse.html` design language

### 2b. Build Tier 1 content (pure HTML/CSS, no Plotly)

**Metric cards row** (4 cards, CSS grid):

| Card | Value | Delta | Sub |
|---|---|---|---|
| Active Partners | N | ↑ +X this month | — |
| Quick Ratio | X.Xx | ↑ from Y.Yx | (new+res+exp) / (churn+contr) |
| Net API Churn | −X.X% | — | Negative = growing |
| Gross Retention | XX% | — | 30-day rolling |

**Two-panel grid:**

Left panel — **Growth Accounting Waterfall** (pure HTML/CSS bars):
- Gains: New (+XX%), Expansion (+XX%), Resurrected (+XX%) — teal
- Divider
- Losses: Contraction (−XX%), Churned (−XX%) — coral
- Divider
- Net growth (+XX%) — neutral bold
- Legend: gains dot / losses dot

Right panel — **CMGR Trailing Windows**:
- CMGR3 bar + value
- CMGR6 bar + value
- CMGR12 bar + value
- Interpretive note with deceleration callout if CMGR3 < CMGR12

**Design specs** (from `pulse.html`):
- Metric cards: secondary background, no border, 8px radius
- Panels: white background, 0.5px border, 12px radius
- Bar heights: waterfall 18px, CMGR 8px
- Typography: values 22px/500, labels 11px uppercase, body 12px
- Colors: teal gains (#1D9E75), coral losses (#D85A30), blue CMGR (#3B6BE0)
- No Plotly, no gradients, no shadows

### 2c. Data flow

All Tier 1 values are computed in Python and injected as f-string variables into the HTML template. No JavaScript computation needed — everything is static at render time.

---

## Phase 3: Tier 2 — Partner List

### 3a. Build the partner list view

Sits below the Tier 1 Pulse block, within the same tab. This is the "who needs attention?" scoreboard.

**Table columns:**

| Column | Source | Color coding |
|---|---|---|
| Company | startup name + stage badge | — |
| Credit Payback | progress bar (existing) | Green >1x, Amber 0.5-1x, Red <0.5x |
| Token CAGR | annualised growth | Green >200%, Amber 50-200%, Red <50% |
| Quick Ratio | dev QR latest month | Green >2.0, Amber 1.0-2.0, Red <1.0 |
| Gross Retention | % retained | Green >80%, Amber 60-80%, Red <60% |
| Last Active | days since last API call | Green <7d, Amber 7-14d, Red >14d |

**Interaction:** Clicking a row navigates to that partner's detail tab (existing behaviour).

**Color coding implementation:** Conditional CSS classes on `<td>` elements:
```html
<td class="metric-cell metric-green">2.4×</td>
<td class="metric-cell metric-red">0.7×</td>
```

### 3b. Section header
Small label above the table: "PARTNER LIST" with a subtitle: "Click a partner to view full analysis"

### 3c. Responsive
Table scrolls horizontally on mobile with the existing scroll-fade indicator.

---

## Phase 4: Tier 3 — Partner Detail

### 4a. Restructure company detail tabs

Each company tab becomes a full analytical drill-down. Sections in this order:

**1. Summary** (always open)
- Hero card (name, stage, vertical, location)
- KPI cards: Total Revenue (expandable by model), Latest MRR, Token CAGR, Credit ROI, Active Devs, Dev Quick Ratio

**2. ▼ Growth Overview**
Pure HTML/CSS waterfall (same design as Tier 1 but for this partner only) + this partner's CMGR3/6/12.

Modes: `Waterfall` | `Growth Accounting` | `Revenue & Tokens`
- Waterfall: HTML/CSS bars for this partner's latest month GA decomposition
- Growth Accounting: Plotly stacked bar (existing `growth_acct` chart)
- Revenue & Tokens: dual line charts (existing)

**3. ▼ Developer Adoption**
Modes: `Quick Ratio` | `Growth Accounting` | `Cohort Retention`
- Quick Ratio: per-partner line (existing)
- GA: developer stacked bar (existing)
- Cohort Retention: developer retention curve (existing)

**4. ▼ Cohort Analysis**
Modes: `LTV Curve` | `LTV Heatmap` | `Revenue Retention`
- LTV: cumulative revenue curve for this partner
- Heatmap: red-to-blue with cohort sizes (new style from TC image)
- Revenue Retention: this partner's spend vs first month

**5. ▼ Revenue by Model**
Modes: `By Model` | `Model Mix`
- Stacked area and 100% area (existing)

**6. ▼ Adoption & Reliability**
Modes: `API Calls & Devs` | `Latency & Errors` | `Engagement (L28)`
- Existing charts

### 4b. Rename section headers
Per the TC critique:
- "Growth Accounting — Users" → "Developer Adoption"
- "Growth Accounting — Revenue" → "Growth Overview"
- Keep "Cohort Analysis" (it's accurate at Tier 3)

### 4c. LTV heatmap restyle
Update to match TC's original chart format:
- Red-to-blue color scale (red = low, white = mid, blue = high)
- Cell value annotations (e.g. "0.5k", "2.1k")
- Cohort size bars on left Y-axis (grey horizontal bars)
- Cap color scale at sensible maximum

---

## Phase 5: Cleanup

### 5a. Remove orphaned code
- Portfolio-level cohort charts (LTV, retention, heatmaps) — these no longer render at Tier 1
- `fig_concentration` — archived, remove computation
- `fig_devs` (Active Developers standalone chart) — replaced by MAU in Tier 1 and dev GA in Tier 3
- Old collapsible section HTML generation for portfolio content

### 5b. Update spec documents
- Update `DASHBOARD-SPEC.md` with three-tier model
- Archive `DASHBOARD-PROPOSAL-V2.md` (superseded)
- Update `CRITIQUE-TC-ADAPTATION.md` with resolution notes

### 5c. Update CSS
- Clean up unused styles from the old collapsible portfolio sections
- Ensure `pulse.html` design tokens (CSS variables) are integrated into `build_dashboard.py`

---

## Phase 6: QA

### 6a. Data consistency
- Tier 1 metric cards match Tier 2 partner list aggregates
- Per-partner QR in list matches per-partner QR in detail
- CMGR values are mathematically correct
- Waterfall percentages sum to net growth

### 6b. Visual audit
- Color coding thresholds render correctly
- Responsive at 600px, 900px, 1400px
- Dark mode works (if using CSS variables)

### 6c. Navigation
- Clicking partner list row → correct detail tab
- Back to Pulse tab → returns to Tier 1 + Tier 2 view
- All mode tabs in Tier 3 switch correctly

---

## Implementation Order

| Step | What | Effort | Dependencies |
|---|---|---|---|
| 1a | CMGR computation | 15 min | None |
| 1b | GA percentages | 10 min | None |
| 1c | Net Churn | 5 min | None |
| 1d | Additional synthetic partners | 45 min | None |
| 2a | Strip Pulse tab | 15 min | None |
| 2b | Build Tier 1 HTML/CSS | 30 min | 1a, 1b, 1c |
| 3a | Build Partner List | 30 min | 1d |
| 3b | Color-coded cells | 15 min | 3a |
| 4a | Restructure detail tabs | 30 min | None |
| 4b | Rename sections | 5 min | 4a |
| 4c | LTV heatmap restyle | 20 min | None |
| 5a | Remove orphaned code | 15 min | 2a, 4a |
| 5b | Update docs | 15 min | All above |
| 6  | QA | 20 min | All above |

**Total estimated: ~4.5 hours**

---

## Branch Strategy

- Current work preserved at `feat/tc-restructure-v1-snapshot`
- Implementation on `feat/three-tier-restructure`
- PR to `main` when complete

---

## What Stays Unchanged

- `pulse.html` standalone mockup (reference only)
- Company detail tab structure (Tier 3 is close to right, just reorder + rename)
- Credit payback progress bars in partner list
- Revenue/Tokens toggle
- Chart descriptions below graphs
- Plotly charts in Tier 3 (interactive depth belongs here)
