# Pulse UI Integration Plan

## The Problem

The current Pulse (formerly "All Companies") tab is hard to digest. It's a wall of Plotly charts inside collapsible sections — functional but dense. An analyst opening this at 9am on Monday wants to know "is everything okay?" in 10 seconds, not scroll through 4 collapsible sections with 15+ mode tabs.

The standalone `pulse.html` mockup solves this — it's immediately readable because it uses flat bars, large numbers, and deliberate whitespace instead of interactive charts. The question is how to integrate that design language into the existing dashboard without losing the analytical depth.

## Proposed Structure: Pulse = Summary + Deep Sections

The Pulse tab becomes two layers:

### Layer 1: The Pulse (top of page, always visible)
A pure HTML/CSS summary block — no Plotly, no charting library. Matches the `pulse.html` design language exactly. This is the "10-second glance" view.

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  PULSE                                                   │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Active   │ │ Quick    │ │ Net API  │ │ Gross    │   │
│  │ Partners │ │ Ratio    │ │ Churn    │ │ Retention│   │
│  │ 3        │ │ 1.0×     │ │ −1.2%   │ │ 93%      │   │
│  │ ↑ +0     │ │ from 0.8×│ │ growing  │ │ 30-day   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                          │
│  ┌─────────────────────┐ ┌─────────────────────────┐    │
│  │ GROWTH ACCOUNTING   │ │ MONTHLY CMGR            │    │
│  │ ─── API TOKENS ──── │ │ ─── TRAILING WINDOWS── │    │
│  │                     │ │                         │    │
│  │ New        ████ +62%│ │ CMGR3  ██── 34%        │    │
│  │ Expansion  ██── +18%│ │ CMGR6  ███─ 41%        │    │
│  │ Resurrected █─── +8%│ │ CMGR12 ████ 58%        │    │
│  │ ─────────────────── │ │                         │    │
│  │ Contraction ███ -24%│ │ CMGR3 < CMGR12:        │    │
│  │ Churned     ██─ -12%│ │ growth decelerated     │    │
│  │ ─────────────────── │ │                         │    │
│  │ Net growth  ████+52%│ │                         │    │
│  └─────────────────────┘ └─────────────────────────┘    │
│                                                          │
│  TOP PERFORMERS TABLE                                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Company  │ Payback │ CAGR │ MRR │ ...           │   │
│  │──────────│─────────│──────│─────│───────────────│   │
│  │ MedScribe│ ████4.1x│1586%│ $27K│               │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- Metric cards: CSS grid, secondary background, no borders, 8px radius. Same pattern as `pulse.html`.
- Growth accounting waterfall: pure HTML/CSS horizontal bars. No Plotly. Teal for gains, coral for losses. Each row = label + bar + percentage. Immediately scannable.
- CMGR panel: three thin bars (8px height) with trailing window labels. Blue colour ramp. Deceleration callout in danger red when CMGR3 < CMGR12.
- Top Performers table: stays as-is (already works well).
- Total Revenue / Credits Deployed KPIs: fold into the metric cards row (replace or augment the four cards).

### Layer 2: Deep-dive sections (below the Pulse block)
The existing collapsible analysis sections remain, but pushed below the Pulse summary. They become the "I saw something in the Pulse, now I want to understand why" layer.

**Changes to existing sections:**
- Remove the KPI cards row at the top (now in the Pulse block)
- Remove the Top Performers table from the section flow (now in the Pulse block)
- Sections start collapsed by default (analyst expands only if something in the Pulse looks off)
- Section order: Growth Accounting — Users → Growth Accounting — Revenue → Cohort Analysis

This creates a clear hierarchy: **Pulse = what happened, Sections = why it happened.**

## Metric Cards — What to Show

The four cards in `pulse.html` are designed for a 150-partner portfolio. With our 3-partner demo, adjust:

| Card | 150-partner version | 3-partner demo version |
|---|---|---|
| Active partners | 147 ↑ +12 | 3 partners · 69 devs |
| Quick ratio | 2.4× ↑ from 1.9× | 1.0× (dev QR, latest month) |
| Net API churn | −1.2% | Compute from growth accounting |
| Gross retention | 91%, 30-day | 93% (from revenue GA) |

## Growth Accounting Waterfall — Data Source

Currently computed in `agg_rev_ga` (portfolio-level revenue growth accounting). The waterfall bars show the latest month's decomposition as percentages of prior month:

```python
latest = agg_rev_ga.iloc[-1]
prior = agg_rev_ga.iloc[-2]['total_revenue']
new_pct = latest['new_revenue'] / prior * 100
expansion_pct = latest['expansion_revenue'] / prior * 100
# ... etc
net_growth = new_pct + expansion_pct + resurrected_pct - churned_pct - contraction_pct
```

## CMGR — New Computation Needed

Currently missing entirely (flagged as critical in the TC critique). Needs:

```python
def cmgr(series, months):
    """Compound Monthly Growth Rate over trailing N months."""
    if len(series) < months + 1:
        return 0
    end = series.iloc[-1]
    start = series.iloc[-(months + 1)]
    if start <= 0:
        return 0
    return (end / start) ** (1 / months) - 1
```

Apply to total portfolio token consumption (or revenue):
- CMGR3 = trailing 3-month compound growth
- CMGR6 = trailing 6-month
- CMGR12 = trailing 12-month

Deceleration signal: `cmgr3 < cmgr12` → flag in danger red.

## LTV Heatmap — Style Update

Current: purple gradient, company names as rows.

Target (from the shared image):
- Red-to-blue colour scale (red = low LTV, blue = high LTV), capped at a sensible max
- Cohort size bars on the left Y-axis (grey horizontal bars showing cohort size)
- Cell values displayed as text annotations (e.g. "0.5k", "2.1k")
- Period numbers on X-axis (0, 1, 2, ... N)
- Cohort month labels on Y-axis

Implementation:
```python
fig.update_layout(...)
# Change colorscale from purple to red-blue:
colorscale = [[0, '#D83030'], [0.5, '#FFFFFF'], [1, '#1D4ED8']]
# Add text annotations for cell values
# Add cohort size subplot on the left
```

This matches the Tribe Capital heatmap style exactly — the image shows their actual chart format.

## Implementation Order

1. **Compute CMGR** — add `cmgr()` function and compute CMGR3/6/12 for portfolio
2. **Compute latest-month GA percentages** — for the waterfall bars
3. **Build the Pulse HTML block** — pure HTML/CSS, matching `pulse.html` design
4. **Insert Pulse block** at top of portfolio content, before the collapsible sections
5. **Move KPI cards and table into the Pulse block** — remove duplicates from below
6. **Set sections to collapsed by default** — add `collapsed` class
7. **Update LTV heatmap** — red-to-blue scale, cohort size bars, cell annotations
8. **QA pass** — verify data flows from Python → Pulse HTML correctly

## What NOT to Change

- Company detail tabs stay as-is (they're deep-dive views, not Pulse)
- Collapsible sections stay (they're the analytical depth layer)
- Plotly charts within sections stay (they need interactivity for drill-down)
- Mode tabs within sections stay (multiple views of same data is correct)

## Files Affected

- `build_dashboard.py` — new CMGR computation, Pulse HTML block, LTV heatmap restyle
- `dashboard.html` — rebuilt output
- No new files needed (pulse.html was a standalone mockup, the real implementation goes into build_dashboard.py)
