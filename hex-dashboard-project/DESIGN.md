# Dashboard Design Guidelines
> Inspired by Hex (hex.tech) — adapted for Anthropic EMEA Startup Partnerships

## Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| Body / UI | IBM Plex Sans | 400, 500 | 13-14px |
| KPI values | IBM Plex Sans | 700 | 24-32px |
| Section headers | IBM Plex Sans | 600 | 11px uppercase, 0.06em tracking |
| Tab labels | IBM Plex Sans | 500 | 13px |
| Table headers | IBM Plex Sans | 600 | 11px uppercase |
| Subtle / meta | IBM Plex Sans | 400 | 11px |

Load from Google Fonts: `IBM+Plex+Sans:wght@400;500;600;700`

## Color Palette

### Light theme (primary — matches Hex app)

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#FFFCFC` | Page background (warm white) |
| `--surface` | `#F8FAFB` | Card backgrounds |
| `--border` | `#E9E5E8` | Borders, dividers |
| `--border-subtle` | `#ECEDF2` | Chart grid lines |
| `--text` | `#14141C` | Primary text (near black) |
| `--text-secondary` | `#43394C` | Body text (purple-grey) |
| `--text-muted` | `#8E8494` | Labels, meta |
| `--accent` | `#472D7B` | Primary purple (Hex brand) |
| `--accent-light` | `rgba(71, 57, 130, 0.07)` | Purple tint for hover/selected |
| `--accent-surface` | `rgba(71, 57, 130, 0.04)` | Subtle purple background |
| `--success` | `#22C55E` | Positive metrics |
| `--warning` | `#EAB308` | Caution metrics |
| `--danger` | `#EF4444` | Negative metrics, churn |

### Chart palette (viridis-inspired, from Hex)

| Index | Hex | Name |
|-------|-----|------|
| 0 | `#472D7B` | Deep violet |
| 1 | `#3B528B` | Blue |
| 2 | `#21918C` | Teal |
| 3 | `#5EC962` | Green |
| 4 | `#ADDC30` | Lime |
| 5 | `#FDE725` | Yellow |

Use indices 0-2 for the three startup partners. Use the full range for sequential/heatmap charts.

### Model colors (for revenue-by-model breakdowns)

| Model | Hex | Rationale |
|-------|-----|-----------|
| Opus | `#472D7B` | Deep violet — premium/complex |
| Sonnet | `#3B528B` | Blue — workhorse |
| Haiku | `#21918C` | Teal — lightweight/fast |

## Layout

### Structure
```
┌─────────────────────────────────────────────┐
│ Header: title + subtitle + date             │
├─────────────────────────────────────────────┤
│ Tabs: Portfolio Overview │ Company A │ ...  │
├─────────────────────────────────────────────┤
│ Content area (padded 32px)                  │
│                                             │
│  ┌─ KPI Row ──────────────────────────────┐ │
│  │ [KPI] [KPI] [KPI] [KPI] [KPI]         │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  Section Header ─────────────────────────── │
│                                             │
│  ┌─────────┐ ┌─────────┐                   │
│  │  Card   │ │  Card   │  (2-col grid)     │
│  │  Chart  │ │  Chart  │                    │
│  └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────┘
```

### Spacing scale
- 4px — tight (within components)
- 8px — compact (between related items)
- 12px — default gap
- 16px — card padding, grid gaps
- 24px — section spacing
- 32px — page padding

### Cards
- Background: `--surface`
- Border: 1px solid `--border`
- Border-radius: 8px
- Padding: 16px
- No box-shadow (Hex is flat, not elevated)
- Hover: no lift effect (data dashboards, not e-commerce)

### KPIs
- Label: 10px uppercase, `--text-muted`, tracking 0.04em
- Value: 24px, weight 700, `--text`
- Subtitle: 11px, `--text-muted`
- Arranged in flex row, equal width, min-width 140px

### Tables
- Header: 11px uppercase, `--text-muted`, weight 600
- Rows: 13px, `--text-secondary`
- Row borders: 1px solid `--border-subtle`
- Row hover: `--accent-surface`
- Alternating row colors: none (Hex doesn't use zebra striping)
- Cell padding: 10px 14px

### Tabs
- Style: text-only with bottom border indicator
- Active: `--text` color, 2px bottom border in `--accent`
- Inactive: `--text-muted`, no border
- Hover: `--text-secondary`
- Sticky at top

## Charts (Plotly config)

### Global layout
```python
layout_defaults = dict(
    font=dict(family="IBM Plex Sans", color="#43394C", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FFFCFC",
    xaxis=dict(gridcolor="#ECEDF2", linecolor="#E9E5E8", zeroline=False),
    yaxis=dict(gridcolor="#ECEDF2", linecolor="#E9E5E8", zeroline=False),
    margin=dict(l=50, r=20, t=40, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        font=dict(size=11)
    ),
    hoverlabel=dict(
        bgcolor="#14141C",
        font_color="#FFFCFC",
        font_size=12,
        font_family="IBM Plex Sans"
    ),
)
```

### Plotly config
```python
plotly_config = dict(
    displayModeBar=False,
    responsive=True,
)
```

### Chart types by use case
| Metric | Chart type | Notes |
|--------|-----------|-------|
| Token consumption over time | Line (area fill) | Stacked by model |
| Revenue by model | Stacked bar | Per company |
| Top performers | Table with sparklines | Sortable |
| Cohort retention | Heatmap | Viridis palette |
| Credit burn | Line with annotation | Projected exhaustion |
| Model mix | Donut / pie | Per company |
| Growth rate comparison | Horizontal bar | Sorted descending |

## Motion

Keep minimal — this is an analytics tool, not a marketing page.

- Tab switch: 150ms crossfade
- Card hover: none (static data display)
- KPI count-up: subtle 600ms ease-out on first view only
- No staggered reveals, no scroll animations
- Plotly built-in transitions only

## Anti-patterns (avoid)

- Dark theme (Hex app is light)
- Gradient backgrounds
- Card elevation / box-shadow on hover
- Badge shimmer effects
- Animated health score gauges
- Radar/spider charts (not a Hex pattern)
- Excessive motion / parallax
- Dense KPI rows (>6 per row)

## File structure
```
hex-dashboard-project/
├── build_dashboard.py     # Generates dashboard.html
├── dashboard.html         # Output (gitignored ideally)
├── DESIGN.md              # This file
├── data/
│   └── *.csv              # Synthetic data
└── serve.py               # Local preview server
```
