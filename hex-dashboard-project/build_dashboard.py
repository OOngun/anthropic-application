"""
Build an interactive HTML dashboard — Three-Tier Progressive Disclosure.
Tier 1: Ecosystem Pulse (pure HTML/CSS)
Tier 2: Partner List (color-coded scoreboard)
Tier 3: Partner Detail (company drill-down tabs)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

OUTPUT_DIR = '/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/data'

startups = pd.read_csv(f'{OUTPUT_DIR}/startups.csv')
monthly_usage = pd.read_csv(f'{OUTPUT_DIR}/monthly_usage.csv')
monthly_usage['month'] = pd.to_datetime(monthly_usage['month'])
credits = pd.read_csv(f'{OUTPUT_DIR}/credit_grants.csv')
unit_economics = pd.read_csv(f'{OUTPUT_DIR}/unit_economics.csv')
unit_economics['month'] = pd.to_datetime(unit_economics['month'])
engagement = pd.read_csv(f'{OUTPUT_DIR}/engagement_depth.csv')
startup_ga = pd.read_csv(f'{OUTPUT_DIR}/startup_growth_accounting.csv')
startup_ga['month'] = pd.to_datetime(startup_ga['month'])

# Dynamic: build COLORS and NAMES from startups CSV
ALL_SIDS = startups['startup_id'].tolist()
_palette = ['#472D7B', '#3B528B', '#21918C', '#5EC962', '#FDE725',
            '#E76F51', '#264653', '#2A9D8F', '#E9C46A', '#F4A261',
            '#606C38', '#283618', '#DDA15E', '#BC6C25', '#0077B6',
            '#023E8A', '#48CAE4', '#90BE6D', '#F94144', '#F3722C',
            '#577590', '#43AA8B', '#F8961E']
COLORS = {sid: _palette[i % len(_palette)] for i, sid in enumerate(ALL_SIDS)}
NAMES = {row['startup_id']: row['startup_name'] for _, row in startups.iterrows()}

# ============================================================
# COMPUTE DEVELOPER GROWTH ACCOUNTING (synthetic decomposition)
# ============================================================

np.random.seed(42)
dev_ga_records = []
for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    prev_devs = 0
    cumulative_ever = 0
    for i, row in u.iterrows():
        month = row['month']
        total = int(row['active_developers'])
        if prev_devs == 0:
            dev_ga_records.append(dict(startup_id=sid, month=month, active_devs=total,
                new_devs=total, retained_devs=0, resurrected_devs=0, churned_devs=0))
            prev_devs = total
            cumulative_ever = total
            continue
        retain_rate = np.clip(np.random.normal(0.75, 0.05), 0.60, 0.90)
        retained = int(min(round(prev_devs * retain_rate), total))
        churned = prev_devs - retained
        remaining = total - retained
        if cumulative_ever > prev_devs and remaining > 0:
            resurrect_pool = cumulative_ever - prev_devs
            resurrected = int(min(round(remaining * np.random.uniform(0.1, 0.3)), resurrect_pool, remaining))
        else:
            resurrected = 0
        new_devs = max(remaining - resurrected, 0)
        dev_ga_records.append(dict(startup_id=sid, month=month, active_devs=total,
            new_devs=new_devs, retained_devs=retained, resurrected_devs=resurrected,
            churned_devs=churned))
        prev_devs = total
        cumulative_ever += new_devs

dev_ga = pd.DataFrame(dev_ga_records)
dev_ga['dev_quick_ratio'] = dev_ga.apply(
    lambda r: min((r['new_devs'] + r['resurrected_devs']) / r['churned_devs'], 10.0)
        if r['churned_devs'] > 0 else np.nan, axis=1)

# Developer retention cohorts (synthetic)
np.random.seed(99)
dev_cohort_records = []
for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    months = u['month'].tolist()
    n_months = len(months)
    for cohort_idx in range(min(n_months, 12)):
        cohort_month = months[cohort_idx]
        cohort_size = max(int(np.random.uniform(2, 8)), 1)
        for age in range(n_months - cohort_idx):
            if age == 0:
                active = cohort_size
            else:
                retain_rate = 0.65 + 0.25 * (1 - np.exp(-age / 6))
                active = int(round(cohort_size * (retain_rate ** age) + np.random.normal(0, 0.3)))
                active = max(0, min(active, cohort_size))
            dev_cohort_records.append(dict(
                startup_id=sid, cohort_month=cohort_month, age=age,
                cohort_size=cohort_size, active_devs=active,
                retention_pct=active / cohort_size * 100 if cohort_size > 0 else 0,
                month=months[cohort_idx + age],
            ))
dev_cohorts = pd.DataFrame(dev_cohort_records)

# ============================================================
# COHORT RETENTION (logo retention by onboarding month)
# ============================================================

cohort_data = []
for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    onboard_month = u.iloc[0]['month']
    for i, row in u.iterrows():
        months_since = (row['month'].year - onboard_month.year) * 12 + (row['month'].month - onboard_month.month)
        is_active = row['total_tokens'] > 0
        first_month_rev = u.iloc[0]['revenue_usd']
        cohort_data.append(dict(
            startup_id=sid, cohort=onboard_month.strftime('%Y-%m'),
            month=row['month'], months_since=months_since,
            active=is_active,
            revenue=row['revenue_usd'],
            first_month_rev=first_month_rev,
            rev_retention=row['revenue_usd'] / first_month_rev if first_month_rev > 0 else 0,
        ))
cohort_df = pd.DataFrame(cohort_data)

# ============================================================
# DESIGN TOKENS
# ============================================================

MODEL_COLORS = {'sonnet': '#3B528B', 'opus': '#472D7B', 'haiku': '#21918C'}
BG = '#FFFCFC'
CARD = '#F8FAFB'
TEXT = '#14141C'
GRID = '#E9E5E8'
MUTED = '#7B7185'
DIM = '#43394C'
ACCENT = '#472D7B'
ACCENT_LIGHT = 'rgba(71, 57, 130, 0.07)'
ACCENT_SURFACE = 'rgba(71, 57, 130, 0.04)'
BORDER_SUBTLE = '#ECEDF2'
SUCCESS = '#16A34A'
WARNING = '#CA8A04'
DANGER = '#DC2626'

# Tier 1 color tokens
GAIN = '#1D9E75'
LOSS = '#D85A30'
CMGR_BLUE = '#3B6BE0'

# ============================================================
# COMPUTE PER-COMPANY METRICS
# ============================================================

company_metrics = []
for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    c = credits[credits['startup_id'] == sid]['amount_usd'].sum()
    ue = unit_economics[unit_economics['startup_id'] == sid]
    ga = startup_ga[startup_ga['startup_id'] == sid].sort_values('month')
    s = startups[startups['startup_id'] == sid].iloc[0]

    latest = u.iloc[-1]
    first = u.iloc[0]
    n_months = len(u) - 1
    total_rev = u['revenue_usd'].sum()
    total_tok = u['total_tokens'].sum()

    # CMGR (Compound Monthly Growth Rate) — trailing 3, 6, 12 months
    def company_cmgr(series, months):
        if len(series) <= months:
            return None
        end = series.iloc[-1]
        start = series.iloc[-(months + 1)]
        return (end / start) ** (1 / months) - 1 if start > 0 else None

    tok_series = u['total_tokens']
    rev_series = u['revenue_usd']
    cmgr3_tok = company_cmgr(tok_series, 3)
    cmgr6_tok = company_cmgr(tok_series, 6)
    cmgr12_tok = company_cmgr(tok_series, 12)
    cmgr3_rev = company_cmgr(rev_series, 3)
    cmgr6_rev = company_cmgr(rev_series, 6)
    cmgr12_rev = company_cmgr(rev_series, 12)

    # Keep CAGR for backward compat but deprioritise
    if first['total_tokens'] > 0 and n_months > 0:
        token_cagr = (latest['total_tokens'] / first['total_tokens']) ** (12 / n_months) - 1
    else:
        token_cagr = 0

    if first['revenue_usd'] > 0 and n_months > 0:
        rev_cagr = (latest['revenue_usd'] / first['revenue_usd']) ** (12 / n_months) - 1
    else:
        rev_cagr = 0

    sonnet_rev = latest['revenue_usd'] * latest['sonnet_pct']
    opus_rev = latest['revenue_usd'] * latest['opus_pct']
    haiku_rev = latest['revenue_usd'] * latest['haiku_pct']
    sonnet_total = (u['revenue_usd'] * u['sonnet_pct']).sum()
    opus_total = (u['revenue_usd'] * u['opus_pct']).sum()
    haiku_total = (u['revenue_usd'] * u['haiku_pct']).sum()
    roi = total_rev / c if c > 0 else 0
    payback = ue[ue['payback_achieved']].iloc[0]['months_since_onboard'] if ue['payback_achieved'].any() else None
    rev_per_dev = latest['revenue_usd'] / latest['active_developers'] if latest['active_developers'] > 0 else 0
    tok_per_dev = latest['total_tokens'] / latest['active_developers'] if latest['active_developers'] > 0 else 0

    if len(u) >= 6:
        recent_3 = u.tail(3)['revenue_usd'].mean()
        prior_3 = u.iloc[-6:-3]['revenue_usd'].mean()
        momentum = (recent_3 / prior_3 - 1) * 100 if prior_3 > 0 else 0
    else:
        momentum = 0

    avg_qr = ga['quick_ratio'].tail(6).mean() if len(ga) > 0 and 'quick_ratio' in ga.columns and not ga['quick_ratio'].isna().all() else 0

    # Latest gross retention for this company
    latest_gross_ret = ga['gross_retention_pct'].iloc[-1] if len(ga) > 0 and 'gross_retention_pct' in ga.columns and not ga['gross_retention_pct'].isna().all() else 0

    # Days since last active — based on whether latest month has revenue
    if latest['revenue_usd'] > 0:
        last_active_days = np.random.choice([1, 2, 3, 5])
    elif len(u) >= 2 and u.iloc[-2]['revenue_usd'] > 0:
        last_active_days = np.random.choice([15, 20, 25])
    else:
        # Find last month with revenue
        active_months = u[u['revenue_usd'] > 0]
        if len(active_months) > 0:
            last_active_month = active_months.iloc[-1]['month']
            days_diff = (u.iloc[-1]['month'] - last_active_month).days
            last_active_days = max(days_diff, 30)
        else:
            last_active_days = 999

    company_metrics.append(dict(
        sid=sid, name=NAMES[sid], vertical=s['vertical'], stage=s['stage'],
        latest_mrr=latest['revenue_usd'], total_rev=total_rev, total_tokens=total_tok,
        token_cagr=token_cagr, rev_cagr=rev_cagr,
        cmgr3=cmgr3_tok, cmgr6=cmgr6_tok, cmgr12=cmgr12_tok,
        cmgr3_rev=cmgr3_rev, cmgr6_rev=cmgr6_rev, cmgr12_rev=cmgr12_rev,
        sonnet_rev=sonnet_rev, opus_rev=opus_rev, haiku_rev=haiku_rev,
        sonnet_total=sonnet_total, opus_total=opus_total, haiku_total=haiku_total,
        credits=c, roi=roi, payback=payback,
        active_devs=int(latest['active_developers']),
        rev_per_dev=rev_per_dev, tok_per_dev=tok_per_dev,
        momentum=momentum, avg_qr=avg_qr,
        latest_latency=latest['avg_latency_ms'],
        latest_error=latest['error_rate'],
        gross_retention=latest_gross_ret,
        last_active_days=last_active_days,
    ))

# Set deterministic last_active_days
company_metrics[0]['last_active_days'] = 2   # MedScribe: very active
company_metrics[1]['last_active_days'] = 5   # Eigen: active
company_metrics[2]['last_active_days'] = 11  # BuilderKit: somewhat dormant

company_metrics.sort(key=lambda x: x['cmgr3'] or 0, reverse=True)

# ============================================================
# CMGR COMPUTATION (Tier 1)
# ============================================================

def cmgr(series, months):
    """Compound Monthly Growth Rate over trailing N months."""
    if len(series) <= months:
        return 0
    end = series.iloc[-1]
    start = series.iloc[-(months + 1)]
    return (end / start) ** (1 / months) - 1 if start > 0 else 0

# Portfolio-level token consumption series
portfolio_tokens = monthly_usage.groupby('month')['total_tokens'].sum().sort_index()
cmgr3 = cmgr(portfolio_tokens, 3)
cmgr6 = cmgr(portfolio_tokens, 6)
cmgr12 = cmgr(portfolio_tokens, 12)

# ============================================================
# TIER 1 DATA: WATERFALL, METRIC CARDS
# ============================================================

# === COMPUTE GA FROM DEVELOPER-LEVEL ACTIVITY DATA ===
# Developer-level granularity gives realistic GA decomposition:
# ~85% retained, 3% new, 20% expansion, 12% churned, 3% contraction
# Matches Tribe Capital's typical SaaS GA patterns.

dev_activity = pd.read_csv(f'{OUTPUT_DIR}/developer_activity.csv')
dev_activity['month'] = pd.to_datetime(dev_activity['month'])
months_sorted = sorted(dev_activity['month'].unique())
first_dev_month = dev_activity.groupby('dev_id')['month'].min().to_dict()

ga_rows = []
for i in range(1, len(months_sorted)):
    prev_m, curr_m = months_sorted[i-1], months_sorted[i]
    prev = dev_activity[dev_activity['month'] == prev_m].set_index('dev_id')['revenue']
    curr = dev_activity[dev_activity['month'] == curr_m].set_index('dev_id')['revenue']
    all_ids = set(prev.index) | set(curr.index)

    new_rev = expansion_rev = resurrected_rev = retained_rev = 0
    churned_rev = contraction_rev = 0

    for did in all_ids:
        p = prev.get(did, 0)
        c = curr.get(did, 0)
        is_new = (first_dev_month.get(did) == curr_m)

        if c > 0 and p > 0:
            retained_rev += min(c, p)
            if c > p: expansion_rev += (c - p)
            elif c < p: contraction_rev += (p - c)
        elif c > 0 and p == 0:
            if is_new: new_rev += c
            else: resurrected_rev += c
        elif c == 0 and p > 0:
            churned_rev += p

    total_rev = new_rev + retained_rev + expansion_rev + resurrected_rev
    ga_rows.append({
        'month': curr_m, 'total_revenue': total_rev,
        'retained_revenue': retained_rev, 'new_revenue': new_rev,
        'expansion_revenue': expansion_rev, 'resurrected_revenue': resurrected_rev,
        'churned_revenue': churned_rev, 'contraction_revenue': contraction_rev,
    })

agg_rev_ga = pd.DataFrame(ga_rows).sort_values('month')
agg_rev_ga['gross_ret'] = agg_rev_ga['retained_revenue'] / agg_rev_ga['total_revenue'].shift(1) * 100

# Per-partner QR and gross retention (from partner-level monthly_usage)
per_partner_qr = {}
per_partner_gret = {}
for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    if len(u) < 2:
        per_partner_qr[sid] = 0
        per_partner_gret[sid] = 0
        continue
    last_rev = u.iloc[-1]['revenue_usd']
    prev_rev = u.iloc[-2]['revenue_usd']
    if last_rev > 0 and prev_rev > 0:
        per_partner_gret[sid] = min(last_rev, prev_rev) / prev_rev * 100
        gains = losses = 0
        for j in range(max(1, len(u)-6), len(u)):
            c = u.iloc[j]['revenue_usd']
            p = u.iloc[j-1]['revenue_usd']
            if c > p: gains += (c - p)
            elif c < p: losses += (p - c)
            if c == 0 and p > 0: losses += p
            if c > 0 and p == 0: gains += c
        per_partner_qr[sid] = gains / losses if losses > 0 else 10.0
    elif last_rev == 0 and prev_rev > 0:
        per_partner_qr[sid] = 0
        per_partner_gret[sid] = 0
    else:
        per_partner_qr[sid] = 0
        per_partner_gret[sid] = 0

for m in company_metrics:
    sid = m['sid']
    if sid in per_partner_qr: m['avg_qr'] = per_partner_qr[sid]
    if sid in per_partner_gret: m['gross_retention'] = per_partner_gret[sid]

# Verify identity
_check = agg_rev_ga.iloc[-1]
_sum = _check['retained_revenue'] + _check['new_revenue'] + _check['expansion_revenue'] + _check['resurrected_revenue']
assert abs(_sum - _check['total_revenue']) < 1.0, f"GA identity broken: {_sum:.0f} != {_check['total_revenue']:.0f}"

# Latest month GA percentages (for waterfall bars)
latest_ga = agg_rev_ga.iloc[-1]
prior_ga = agg_rev_ga.iloc[-2] if len(agg_rev_ga) >= 2 else None
prior_total = prior_ga['total_revenue'] if prior_ga is not None else 1

wf_new_pct = latest_ga['new_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_expansion_pct = latest_ga['expansion_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_resurrected_pct = latest_ga['resurrected_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_contraction_pct = latest_ga['contraction_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_churned_pct = latest_ga['churned_revenue'] / prior_total * 100 if prior_total > 0 else 0
# Net growth now equals sum of components (identity holds)
wf_net_pct = wf_new_pct + wf_expansion_pct + wf_resurrected_pct - wf_contraction_pct - wf_churned_pct

# Compute all-time average GA percentages for comparison
ga_pct_history = pd.DataFrame()
ga_pct_history['month'] = agg_rev_ga['month']
shifted_total = agg_rev_ga['total_revenue'].shift(1)
ga_pct_history['new_pct'] = agg_rev_ga['new_revenue'] / shifted_total * 100
ga_pct_history['expansion_pct'] = agg_rev_ga['expansion_revenue'] / shifted_total * 100
ga_pct_history['resurrected_pct'] = agg_rev_ga['resurrected_revenue'] / shifted_total * 100
ga_pct_history['contraction_pct'] = agg_rev_ga['contraction_revenue'] / shifted_total * 100
ga_pct_history['churned_pct'] = agg_rev_ga['churned_revenue'] / shifted_total * 100
ga_pct_history['net_pct'] = (agg_rev_ga['total_revenue'] - shifted_total) / shifted_total * 100
ga_pct_history = ga_pct_history.dropna()

avg_new_pct = ga_pct_history['new_pct'].mean()
avg_expansion_pct = ga_pct_history['expansion_pct'].mean()
avg_resurrected_pct = ga_pct_history['resurrected_pct'].mean()
avg_contraction_pct = ga_pct_history['contraction_pct'].mean()
avg_churned_pct = ga_pct_history['churned_pct'].mean()
avg_net_pct = ga_pct_history['net_pct'].mean()
n_months_avg = len(ga_pct_history)

# Net API Churn = (Churned + Contraction - Resurrected - Expansion) / Prior Revenue
net_churn = (latest_ga['churned_revenue'] + latest_ga['contraction_revenue'] - latest_ga['resurrected_revenue'] - latest_ga['expansion_revenue']) / prior_total * 100 if prior_total > 0 else 0

# Active partners count
active_partners = len([m for m in company_metrics if m['last_active_days'] < 30])

# Portfolio Quick Ratio (latest month)
gains = latest_ga['new_revenue'] + latest_ga['expansion_revenue'] + latest_ga['resurrected_revenue']
losses = latest_ga['churned_revenue'] + latest_ga['contraction_revenue']
portfolio_qr = gains / losses if losses > 0 else 10.0

# Gross retention (latest)
latest_gross_ret = agg_rev_ga['gross_ret'].dropna().iloc[-1] if agg_rev_ga['gross_ret'].dropna().any() else 0

# ============================================================
# AGGREGATE DEV GA
# ============================================================

agg_dev_ga = dev_ga.groupby('month').agg(
    new_devs=('new_devs', 'sum'),
    retained_devs=('retained_devs', 'sum'),
    resurrected_devs=('resurrected_devs', 'sum'),
    churned_devs=('churned_devs', 'sum'),
    active_devs=('active_devs', 'sum'),
).reset_index().sort_values('month')

agg_dev_qr = dev_ga[dev_ga['dev_quick_ratio'].notna()].groupby('month')['dev_quick_ratio'].mean().reset_index()

# ============================================================
# CHART HELPERS
# ============================================================

def layout(title, h=380):
    return dict(
        title=dict(text=title, font=dict(size=13, color=TEXT, family='IBM Plex Sans'), x=0.01),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor=BG,
        font=dict(family='IBM Plex Sans', color=DIM, size=12),
        height=h, margin=dict(l=55, r=20, t=40, b=40),
        xaxis=dict(gridcolor=BORDER_SUBTLE, linecolor=GRID, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=BORDER_SUBTLE, linecolor=GRID, showgrid=True, zeroline=False),
        legend=dict(bgcolor='rgba(0,0,0,0)', orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, font=dict(size=11)),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=TEXT, font_color=BG, font_size=12, font_family='IBM Plex Sans'),
    )

PLOTLY_CONFIG = dict(displaylogo=False, modeBarButtonsToRemove=['lasso2d','select2d'])

_chart_counter = [0]
def to_div(fig, chart_id=None):
    if chart_id is None:
        _chart_counter[0] += 1
        chart_id = f'chart-{_chart_counter[0]}'
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id, config=PLOTLY_CONFIG)

def kpi(label, value, sub='', color=TEXT):
    return f'<div class="kpi"><div class="kpi-l">{label}</div><div class="kpi-v" style="color:{color}">{value}</div><div class="kpi-s">{sub}</div></div>'

def fmt_pct(v):
    return f'{v*100:,.0f}%' if abs(v) >= 0.01 else f'{v*100:,.1f}%'

model_fills = {'Sonnet': 'rgba(59,82,139,0.6)', 'Opus': 'rgba(71,45,123,0.6)', 'Haiku': 'rgba(33,145,140,0.6)'}

# ============================================================
# PER-STARTUP CHARTS (Tier 3)
# ============================================================

startup_charts = {}

for sid in ALL_SIDS:
    charts = {}
    d_usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')

    # Compute per-company GA from monthly_usage (not CSV) so all 23 partners have data
    _company_ga_rows = []
    _rev_vals = d_usage['revenue_usd'].values
    _months_vals = d_usage['month'].values
    for _j in range(1, len(_rev_vals)):
        _p, _c = _rev_vals[_j-1], _rev_vals[_j]
        _ret = min(_c, _p) if _c > 0 and _p > 0 else 0
        _exp = (_c - _p) if _c > _p and _p > 0 else 0
        _contr = (_p - _c) if _p > _c and _c > 0 else 0
        _new = _c if _c > 0 and _p == 0 and _j == 0 else 0
        _res = _c if _c > 0 and _p == 0 and _j > 0 else 0
        _churn = _p if _p > 0 and _c == 0 else 0
        _qr = (_exp + _new + _res) / (_contr + _churn) if (_contr + _churn) > 0 else 10.0
        _gret = _ret / _p * 100 if _p > 0 else 0
        _company_ga_rows.append({
            'month': _months_vals[_j],
            'new_revenue': _new, 'expansion_revenue': _exp,
            'resurrected_revenue': _res, 'retained_revenue': _ret,
            'churned_revenue': _churn, 'contraction_revenue': _contr,
            'total_revenue': _ret + _new + _exp + _res,
            'quick_ratio': _qr, 'gross_retention_pct': _gret,
        })
    d_ga = pd.DataFrame(_company_ga_rows) if _company_ga_rows else pd.DataFrame(
        columns=['month','new_revenue','expansion_revenue','resurrected_revenue',
                 'retained_revenue','churned_revenue','contraction_revenue',
                 'total_revenue','quick_ratio','gross_retention_pct'])

    # Revenue
    f = go.Figure()
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['revenue_usd'], mode='lines+markers',
        line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False,
        hovertemplate='$%{y:,.0f}<extra></extra>'))
    f.update_layout(**layout('Monthly API Revenue'))
    f.update_yaxes(tickprefix='$', tickformat=',')
    charts['revenue'] = to_div(f)

    # Token consumption
    f = go.Figure()
    tok_millions = d_usage['total_tokens'] / 1e6
    f.add_trace(go.Scatter(x=d_usage['month'], y=tok_millions, mode='lines+markers',
        line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False,
        hovertemplate='%{y:,.0f}M tokens<extra></extra>'))
    f.update_layout(**layout('Monthly Tokens (millions)'))
    f.update_yaxes(ticksuffix='M', tickformat=',')
    charts['tokens'] = to_div(f)

    # Revenue by model over time
    f = go.Figure()
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['revenue_usd'] * d_usage['sonnet_pct'], name='Sonnet',
        stackgroup='one', line=dict(color=MODEL_COLORS['sonnet'], width=0), fillcolor=model_fills['Sonnet'],
        hovertemplate='$%{y:,.0f}<extra></extra>'))
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['revenue_usd'] * d_usage['opus_pct'], name='Opus',
        stackgroup='one', line=dict(color=MODEL_COLORS['opus'], width=0), fillcolor=model_fills['Opus'],
        hovertemplate='$%{y:,.0f}<extra></extra>'))
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['revenue_usd'] * d_usage['haiku_pct'], name='Haiku',
        stackgroup='one', line=dict(color=MODEL_COLORS['haiku'], width=0), fillcolor=model_fills['Haiku'],
        hovertemplate='$%{y:,.0f}<extra></extra>'))
    f.update_layout(**layout('Revenue by Model'))
    f.update_yaxes(tickprefix='$', tickformat=',')
    charts['rev_by_model'] = to_div(f)

    # Model mix %
    f = go.Figure()
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['sonnet_pct'] * 100, name='Sonnet',
        stackgroup='one', line=dict(color=MODEL_COLORS['sonnet'], width=0), fillcolor=model_fills['Sonnet']))
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['opus_pct'] * 100, name='Opus',
        stackgroup='one', line=dict(color=MODEL_COLORS['opus'], width=0), fillcolor=model_fills['Opus']))
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['haiku_pct'] * 100, name='Haiku',
        stackgroup='one', line=dict(color=MODEL_COLORS['haiku'], width=0), fillcolor=model_fills['Haiku']))
    f.update_layout(**layout('Model Mix %', h=300))
    f.update_yaxes(ticksuffix='%', range=[0, 100])
    charts['model_mix'] = to_div(f)

    # Growth Accounting (revenue)
    f = go.Figure()
    f.add_trace(go.Bar(x=d_ga['month'], y=d_ga['new_revenue'], name='New', marker_color=SUCCESS))
    f.add_trace(go.Bar(x=d_ga['month'], y=d_ga['expansion_revenue'], name='Expansion', marker_color=MODEL_COLORS['sonnet']))
    f.add_trace(go.Bar(x=d_ga['month'], y=d_ga['resurrected_revenue'], name='Resurrected', marker_color='#5EC962'))
    f.add_trace(go.Bar(x=d_ga['month'], y=-d_ga['churned_revenue'], name='Churned', marker_color=DANGER))
    f.add_trace(go.Bar(x=d_ga['month'], y=-d_ga['contraction_revenue'], name='Contraction', marker_color=WARNING))
    f.update_layout(**layout('Spend Growth Accounting'), barmode='relative')
    f.update_yaxes(tickprefix='$', tickformat=',')
    charts['growth_acct'] = to_div(f)

    # Developer Growth Accounting (per-startup)
    d_dev_ga = dev_ga[dev_ga['startup_id'] == sid].sort_values('month')
    f = go.Figure()
    f.add_trace(go.Bar(x=d_dev_ga['month'], y=d_dev_ga['retained_devs'], name='Retained', marker_color='#3B528B'))
    f.add_trace(go.Bar(x=d_dev_ga['month'], y=d_dev_ga['new_devs'], name='New', marker_color=SUCCESS))
    f.add_trace(go.Bar(x=d_dev_ga['month'], y=d_dev_ga['resurrected_devs'], name='Resurrected', marker_color='#5EC962'))
    f.add_trace(go.Bar(x=d_dev_ga['month'], y=-d_dev_ga['churned_devs'], name='Churned', marker_color=DANGER))
    f.update_layout(**layout('Developer Growth Accounting'), barmode='relative')
    charts['dev_ga'] = to_div(f)

    # Developer Quick Ratio (per-startup)
    d_dev_qr = d_dev_ga.dropna(subset=['dev_quick_ratio'])
    f = go.Figure()
    f.add_trace(go.Scatter(x=d_dev_qr['month'], y=d_dev_qr['dev_quick_ratio'],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False))
    f.add_hline(y=2, line_dash="dash", line_color=SUCCESS, annotation_text="2.0x", annotation_position="top right", annotation_font_color=SUCCESS)
    f.add_hline(y=1, line_dash="dash", line_color=DANGER, annotation_text="1.0x", annotation_position="bottom right", annotation_font_color=DANGER)
    f.update_layout(**layout('Developer Quick Ratio', h=300))
    max_qr = d_dev_qr['dev_quick_ratio'].max() if len(d_dev_qr) > 0 else 5
    f.update_yaxes(range=[0, min(max_qr * 1.2, 8)])
    charts['dev_qr'] = to_div(f)

    # Developer Retention curve (per-startup)
    dc_company = dev_cohorts[dev_cohorts['startup_id'] == sid]
    if len(dc_company) > 0:
        avg_ret = dc_company.groupby('age')['retention_pct'].mean().reset_index()
        f = go.Figure()
        f.add_trace(go.Scatter(x=avg_ret['age'], y=avg_ret['retention_pct'],
            mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=4),
            showlegend=False, hovertemplate='Month %{x}: %{y:.0f}%<extra></extra>'))
        f.add_hline(y=50, line_dash="dash", line_color=WARNING)
        f.update_layout(**layout('Developer Cohort Retention', h=300))
        f.update_yaxes(ticksuffix='%', range=[0, 105])
        f.update_xaxes(title_text='Months since cohort start')
        charts['dev_retention'] = to_div(f)

    # Cohort LTV for this company (simple cumulative line)
    cd_s = cohort_df[cohort_df['startup_id'] == sid].sort_values('months_since')
    if len(cd_s) > 0:
        cum_rev = cd_s['revenue'].cumsum()
        f = go.Figure()
        f.add_trace(go.Scatter(x=cd_s['months_since'], y=cum_rev,
            mode='lines', line=dict(color=COLORS[sid], width=2.5), showlegend=False,
            hovertemplate='Month %{x}: $%{y:,.0f}<extra></extra>'))
        f.update_layout(**layout('Cumulative LTV'))
        f.update_yaxes(tickprefix='$', tickformat=',')
        f.update_xaxes(title_text='Months since onboarding')
        charts['ltv_curve'] = to_div(f)

    # === LTV HEATMAP (Tribe Capital style: red-to-blue, cohort sizes) ===
    d_dev = dev_activity[dev_activity['startup_id'] == sid].copy()
    if len(d_dev) > 5:
        first_dev_m = d_dev.groupby('dev_id')['month'].min().reset_index()
        first_dev_m.columns = ['dev_id', 'first_month']
        d_dev = d_dev.merge(first_dev_m, on='dev_id')
        d_dev['age'] = ((d_dev['month'] - d_dev['first_month']).dt.days / 30.44).round().astype(int)

        cohort_sizes_local = d_dev.groupby('first_month')['dev_id'].nunique().reset_index()
        cohort_sizes_local.columns = ['first_month', 'cohort_size']

        # Cumulative LTV per dev per cohort at each age
        cohort_agg = d_dev.groupby(['first_month', 'age']).agg(
            active=('dev_id', 'nunique'), rev=('revenue', 'sum')
        ).reset_index()
        cohort_agg = cohort_agg.merge(cohort_sizes_local, on='first_month')
        cohort_agg['cum_rev'] = cohort_agg.groupby('first_month')['rev'].cumsum()
        cohort_agg['cum_ltv'] = cohort_agg['cum_rev'] / cohort_agg['cohort_size']
        cohort_agg['retention'] = cohort_agg['active'] / cohort_agg['cohort_size'] * 100

        # Build heatmap matrix for LTV
        cohorts_sorted = sorted(cohort_agg['first_month'].unique())
        max_age = int(cohort_agg['age'].max())
        ltv_matrix = []
        ret_matrix = []
        cohort_labels = []
        cohort_size_vals = []

        for fm in cohorts_sorted:
            c = cohort_agg[cohort_agg['first_month'] == fm].set_index('age')
            cs = cohort_sizes_local[cohort_sizes_local['first_month'] == fm]['cohort_size'].iloc[0]
            ltv_row = []
            ret_row = []
            for a in range(max_age + 1):
                if a in c.index:
                    ltv_row.append(round(c.loc[a, 'cum_ltv'], 0))
                    ret_row.append(round(c.loc[a, 'retention'], 1))
                else:
                    ltv_row.append(None)
                    ret_row.append(None)
            ltv_matrix.append(ltv_row)
            ret_matrix.append(ret_row)
            cohort_labels.append(fm.strftime('%Y-%m'))
            cohort_size_vals.append(cs)

        # LTV Heatmap
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig_ltv_hm = make_subplots(rows=1, cols=2, column_widths=[0.12, 0.88],
            shared_yaxes=True, horizontal_spacing=0.02)

        # Cohort size bars (left)
        fig_ltv_hm.add_trace(go.Bar(
            y=cohort_labels, x=cohort_size_vals, orientation='h',
            marker_color='#94a3b8', showlegend=False,
            hovertemplate='%{y}: %{x} devs<extra></extra>'
        ), row=1, col=1)

        # Text annotations for heatmap cells
        text_matrix = []
        for row in ltv_matrix:
            text_row = []
            for v in row:
                if v is None:
                    text_row.append('')
                elif v >= 1000:
                    text_row.append(f'{v/1000:.1f}k')
                else:
                    text_row.append(f'{v:.0f}')
            text_matrix.append(text_row)

        # LTV heatmap (right) — red to blue
        fig_ltv_hm.add_trace(go.Heatmap(
            z=ltv_matrix, x=list(range(max_age + 1)), y=cohort_labels,
            text=text_matrix, texttemplate='%{text}', textfont=dict(size=9),
            colorscale=[[0, '#DC2626'], [0.25, '#F87171'], [0.5, '#FAFAFA'],
                        [0.75, '#60A5FA'], [1, '#1D4ED8']],
            showscale=True, colorbar=dict(title='LTV', tickprefix='$', len=0.8),
            hovertemplate='Cohort %{y}<br>Period %{x}<br>LTV: $%{z:,.0f}<extra></extra>',
            zmin=0
        ), row=1, col=2)

        fig_ltv_hm.update_layout(
            height=max(300, len(cohorts_sorted) * 28 + 80),
            margin=dict(t=40, b=40, l=10, r=10),
            paper_bgcolor='white', plot_bgcolor='white',
            title=dict(text='LTV by Cohort', font=dict(size=14)),
            font=dict(family='Inter, sans-serif', size=11)
        )
        fig_ltv_hm.update_xaxes(title_text='cohort size', row=1, col=1, showticklabels=False)
        fig_ltv_hm.update_xaxes(title_text='period', row=1, col=2)
        fig_ltv_hm.update_yaxes(autorange='reversed', row=1, col=1)
        charts['ltv_heatmap'] = to_div(fig_ltv_hm, f'ltv-hm-{sid}')

        # Retention Heatmap (same structure, green-to-red)
        ret_text = []
        for row in ret_matrix:
            ret_text.append([f'{v:.0f}%' if v is not None else '' for v in row])

        fig_ret_hm = make_subplots(rows=1, cols=2, column_widths=[0.12, 0.88],
            shared_yaxes=True, horizontal_spacing=0.02)

        fig_ret_hm.add_trace(go.Bar(
            y=cohort_labels, x=cohort_size_vals, orientation='h',
            marker_color='#94a3b8', showlegend=False
        ), row=1, col=1)

        fig_ret_hm.add_trace(go.Heatmap(
            z=ret_matrix, x=list(range(max_age + 1)), y=cohort_labels,
            text=ret_text, texttemplate='%{text}', textfont=dict(size=9),
            colorscale=[[0, '#DC2626'], [0.5, '#FBBF24'], [1, '#16A34A']],
            showscale=True, colorbar=dict(title='Ret %', ticksuffix='%', len=0.8),
            hovertemplate='Cohort %{y}<br>Period %{x}<br>Retention: %{z:.0f}%<extra></extra>',
            zmin=0, zmax=100
        ), row=1, col=2)

        fig_ret_hm.update_layout(
            height=max(300, len(cohorts_sorted) * 28 + 80),
            margin=dict(t=40, b=40, l=10, r=10),
            paper_bgcolor='white', plot_bgcolor='white',
            title=dict(text='Developer Retention by Cohort', font=dict(size=14)),
            font=dict(family='Inter, sans-serif', size=11)
        )
        fig_ret_hm.update_xaxes(title_text='cohort size', row=1, col=1, showticklabels=False)
        fig_ret_hm.update_xaxes(title_text='period', row=1, col=2)
        fig_ret_hm.update_yaxes(autorange='reversed', row=1, col=1)
        charts['retention_heatmap'] = to_div(fig_ret_hm, f'ret-hm-{sid}')

    # LTV Heatmap (per-company, single row — show as heatmap with cohort months)
    ltv_vals = cd_s['revenue'].cumsum().values.tolist() if len(cd_s) > 0 else []
    n_m = len(ltv_vals)
    # Text annotations
    ltv_text = []
    for v in ltv_vals:
        if v >= 1000:
            ltv_text.append(f'{v/1000:.1f}k')
        else:
            ltv_text.append(f'{v:.0f}')

    f = go.Figure(data=go.Heatmap(
        z=[ltv_vals], x=[f'M{i}' for i in range(n_m)], y=[NAMES[sid]],
        colorscale=[[0, '#d73027'], [0.25, '#f46d43'], [0.5, '#ffffbf'], [0.75, '#4575b4'], [1, '#313695']],
        hovertemplate='Month %{x}: $%{z:,.0f}<extra></extra>',
        colorbar=dict(title='LTV ($)', tickprefix='$', tickformat=','),
        text=[ltv_text], texttemplate='%{text}', textfont=dict(size=10),
    ))
    f.update_layout(**layout('Cumulative LTV Heatmap', h=160))
    charts['ltv_heatmap'] = to_div(f)

    # Revenue retention
    if len(cd_s) > 0:
        f = go.Figure()
        f.add_trace(go.Scatter(x=cd_s['months_since'], y=cd_s['rev_retention'],
            mode='lines', line=dict(color=COLORS[sid], width=2.5), showlegend=False,
            hovertemplate='Month %{x}: %{y:.1f}x<extra></extra>'))
        f.add_hline(y=1, line_dash="dash", line_color=MUTED, annotation_text="1x baseline",
            annotation_position="top right", annotation_font_color=MUTED)
        f.update_layout(**layout('Revenue Retention vs First Month', h=300))
        f.update_yaxes(ticksuffix='x')
        f.update_xaxes(title_text='Months since onboarding')
        charts['rev_retention'] = to_div(f)

    # API calls + devs dual axis
    f = go.Figure()
    f.add_trace(go.Bar(x=d_usage['month'], y=d_usage['api_calls'], name='API Calls',
        marker_color=COLORS[sid], opacity=0.4))
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['active_developers'], name='Active Devs',
        mode='lines+markers', line=dict(color='#5EC962', width=2.5), marker=dict(size=5), yaxis='y2'))
    dl = layout('API Calls & Active Developers')
    dl['yaxis2'] = dict(overlaying='y', side='right',
        showgrid=False, zeroline=False, title='Developers',
        titlefont=dict(color='#5EC962'), tickfont=dict(color='#5EC962'))
    dl['yaxis']['title'] = 'API Calls'
    f.update_layout(**dl)
    charts['devs_calls'] = to_div(f)

    # L28 Engagement
    d_eng = engagement[(engagement['startup_id'] == sid) & (engagement['snapshot'] == 'latest') & (engagement['days_active_l28'] > 0)]
    if len(d_eng) > 0:
        f = go.Figure()
        f.add_trace(go.Bar(x=d_eng['days_active_l28'], y=d_eng['user_pct'],
            marker_color=COLORS[sid], opacity=0.8,
            hovertemplate='%{x}d: %{y:.1f}%<extra></extra>'))
        f.update_layout(**layout('API Usage Depth (L28 days active)'))
        f.update_xaxes(title_text='Days active / 28', dtick=2)
        f.update_yaxes(ticksuffix='%')
        charts['engagement'] = to_div(f)

    # Latency + Error rate
    f = go.Figure()
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['avg_latency_ms'], name='Avg Latency (ms)',
        mode='lines+markers', line=dict(color=MODEL_COLORS['haiku'], width=2), marker=dict(size=4)))
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['error_rate'] * 100, name='Error Rate (%)',
        mode='lines+markers', line=dict(color=DANGER, width=2), marker=dict(size=4), yaxis='y2'))
    ll = layout('Latency & Error Rate')
    ll['yaxis']['title'] = 'ms'
    ll['yaxis2'] = dict(overlaying='y', side='right',
        showgrid=False, zeroline=False, title='Error %',
        ticksuffix='%', titlefont=dict(color=DANGER), tickfont=dict(color=DANGER))
    f.update_layout(**ll)
    charts['latency'] = to_div(f)

    # Spend Quick Ratio (per-company)
    f = go.Figure()
    f.add_trace(go.Scatter(x=d_ga['month'], y=d_ga['quick_ratio'],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False))
    f.add_hline(y=4, line_dash="dash", line_color=SUCCESS, annotation_text="4.0x Strong", annotation_position="top right", annotation_font_color=SUCCESS)
    f.add_hline(y=1, line_dash="dash", line_color=DANGER, annotation_text="1.0x Flat", annotation_position="bottom right", annotation_font_color=DANGER)
    f.update_layout(**layout('Spend Quick Ratio', h=300))
    f.update_yaxes(range=[0, 12])
    charts['spend_qr'] = to_div(f)

    # Gross retention (per-company)
    if 'gross_retention_pct' in d_ga.columns:
        f = go.Figure()
        f.add_trace(go.Scatter(x=d_ga['month'], y=d_ga['gross_retention_pct'],
            mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False,
            hovertemplate='%{y:.1f}%<extra></extra>'))
        f.add_hline(y=70, line_dash="dash", line_color=WARNING, annotation_text="70% Benchmark",
            annotation_position="bottom right", annotation_font_color=WARNING)
        f.update_layout(**layout('Gross Revenue Retention', h=300))
        f.update_yaxes(ticksuffix='%', range=[0, 105])
        charts['gross_ret'] = to_div(f)

    startup_charts[sid] = charts

# ============================================================
# TIER 1: ECOSYSTEM PULSE (pure HTML/CSS)
# ============================================================

# Waterfall bar max for scaling
wf_max = max(abs(wf_new_pct), abs(wf_expansion_pct), abs(wf_resurrected_pct), abs(wf_contraction_pct), abs(wf_churned_pct), abs(wf_net_pct), 1)

def wf_bar(label, pct, avg_pct, color, is_loss=False):
    width = abs(pct) / wf_max * 100
    avg_width = abs(avg_pct) / wf_max * 100
    sign = '-' if is_loss else '+'
    # Delta: for gains, higher is better; for losses, lower is better
    if is_loss:
        delta = avg_pct - pct  # positive = improving (less loss)
    else:
        delta = pct - avg_pct  # positive = improving (more gain)
    delta_color = SUCCESS if delta > 0.5 else DANGER if delta < -0.5 else MUTED
    delta_arrow = '↑' if delta > 0.5 else '↓' if delta < -0.5 else '→'
    return f'''<div class="waterfall-row">
        <span class="wf-label">{label}</span>
        <div class="waterfall-bar">
            <div class="wf-track">
                <div class="wf-fill" style="width:{width:.1f}%;background:{color}"></div>
                <div class="wf-avg-marker" style="left:{avg_width:.1f}%" title="Avg: {sign}{abs(avg_pct):.1f}%"></div>
            </div>
        </div>
        <span class="wf-value" style="color:{color}">{sign}{abs(pct):.1f}%</span>
        <span class="wf-delta" style="color:{delta_color}" title="vs {n_months_avg}-month avg ({sign}{abs(avg_pct):.1f}%)">{delta_arrow}</span>
    </div>'''

# ============================================================
# COMBINED GA + CMGR CHART (Plotly — replaces static CMGR bars)
# ============================================================
# Revenue Growth Accounting stacked bars + CMGR trailing lines on secondary axis

fig_ga_cmgr = go.Figure()

# GA bars — gains above axis, losses below
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['retained_revenue'], name='Retained',
    marker_color='#94a3b8', opacity=0.5, hovertemplate='Retained: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['new_revenue'], name='New',
    marker_color=GAIN, hovertemplate='New: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['expansion_revenue'], name='Expansion',
    marker_color='#34d399', hovertemplate='Expansion: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['resurrected_revenue'], name='Resurrected',
    marker_color='#6ee7b7', hovertemplate='Resurrected: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=-agg_rev_ga['contraction_revenue'], name='Contraction',
    marker_color='#fb923c', hovertemplate='Contraction: -$%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=-agg_rev_ga['churned_revenue'], name='Churned',
    marker_color=LOSS, hovertemplate='Churned: -$%{y:,.0f}<extra></extra>'))

# CMGR trailing lines on secondary y-axis
# Compute rolling CMGR at each month
months_list = portfolio_tokens.index.tolist()
cmgr3_series, cmgr6_series, cmgr12_series = [], [], []
cmgr_months = []
for i in range(len(months_list)):
    m = months_list[i]
    sub = portfolio_tokens.iloc[:i+1]
    c3 = cmgr(sub, 3) if len(sub) > 6 else None   # skip first 6 months
    c6 = cmgr(sub, 6) if len(sub) > 9 else None   # skip first 9 months
    c12 = cmgr(sub, 12) if len(sub) > 12 else None
    cmgr_months.append(m)
    cmgr3_series.append(c3)
    cmgr6_series.append(c6)
    cmgr12_series.append(c12)

cmgr_df = pd.DataFrame({'month': cmgr_months, 'cmgr3': cmgr3_series, 'cmgr6': cmgr6_series, 'cmgr12': cmgr12_series})

for col, name, color, dash in [
    ('cmgr3', 'CMGR-3', '#3B6BE0', 'solid'),
    ('cmgr6', 'CMGR-6', '#6366f1', 'dash'),
    ('cmgr12', 'CMGR-12', '#a78bfa', 'dot'),
]:
    valid = cmgr_df.dropna(subset=[col])
    if len(valid) > 0:
        fig_ga_cmgr.add_trace(go.Scatter(
            x=valid['month'], y=valid[col] * 100, name=name,
            mode='lines+markers', line=dict(color=color, width=3, dash=dash),
            marker=dict(size=5),
            yaxis='y2',
            hovertemplate=f'{name}: %{{y:.1f}}%<extra></extra>'))

# Add prominent zero line
fig_ga_cmgr.add_hline(y=0, line=dict(color=DANGER, width=2, dash='solid'), opacity=0.6)

ga_cmgr_layout = layout('Growth Accounting + CMGR', h=400)
ga_cmgr_layout['barmode'] = 'relative'
ga_cmgr_layout['yaxis']['tickprefix'] = '$'
ga_cmgr_layout['yaxis']['tickformat'] = ','
ga_cmgr_layout['yaxis']['title'] = 'Revenue'
ga_cmgr_layout['yaxis']['zeroline'] = True
ga_cmgr_layout['yaxis']['zerolinecolor'] = DANGER
ga_cmgr_layout['yaxis']['zerolinewidth'] = 2
# Compute sensible y2 range from actual CMGR values
all_cmgr_vals = [v for v in cmgr3_series + cmgr6_series + cmgr12_series if v is not None]
cmgr_min_pct = min(all_cmgr_vals) * 100 if all_cmgr_vals else 0
cmgr_max_pct = max(all_cmgr_vals) * 100 if all_cmgr_vals else 100
cmgr_padding = max((cmgr_max_pct - cmgr_min_pct) * 0.15, 5)

ga_cmgr_layout['yaxis2'] = dict(
    overlaying='y', side='right', showgrid=False, zeroline=True,
    zerolinecolor='rgba(59,107,224,0.2)',
    title='CMGR %', ticksuffix='%',
    range=[cmgr_min_pct - cmgr_padding, cmgr_max_pct + cmgr_padding],
    titlefont=dict(color='#3B6BE0', size=11),
    tickfont=dict(color='#3B6BE0', size=10))
ga_cmgr_layout['legend'] = dict(
    bgcolor='rgba(0,0,0,0)', orientation='h', yanchor='top', y=-0.18,
    xanchor='center', x=0.5, font=dict(size=10),
    traceorder='normal')
ga_cmgr_layout['margin'] = dict(t=40, b=90, l=60, r=60)
# Cap y2 axis to remove early outlier distortion
stable_cmgr = [v for v in cmgr3_series + cmgr6_series + cmgr12_series if v is not None and abs(v) < 1.0]
if stable_cmgr:
    y2_max = max(stable_cmgr) * 100
    y2_min = min(min(stable_cmgr) * 100, 0)
    y2_pad = max((y2_max - y2_min) * 0.15, 3)
    ga_cmgr_layout['yaxis2']['range'] = [y2_min - y2_pad, y2_max + y2_pad]
fig_ga_cmgr.update_layout(**ga_cmgr_layout)

ga_cmgr_div = to_div(fig_ga_cmgr, 'pulse-ga-cmgr')

# Deceleration note for inline display
cmgr_note_html = ''
if cmgr3 < cmgr12 and cmgr12 > 0:
    cmgr_note_html = f'<div class="cmgr-note decel">CMGR3 ({cmgr3*100:.1f}%) trails CMGR12 ({cmgr12*100:.1f}%) — growth has <strong>decelerated</strong></div>'
elif cmgr3 > cmgr12 and cmgr12 > 0:
    cmgr_note_html = f'<div class="cmgr-note accel">CMGR3 ({cmgr3*100:.1f}%) leads CMGR12 ({cmgr12*100:.1f}%) — growth is <strong>accelerating</strong></div>'

# Net churn display
net_churn_display = f'{net_churn:.1f}%'
net_churn_note = 'Negative = growing' if net_churn < 0 else 'Positive = shrinking'

tier1_html = f'''
<div class="pulse-block">
    <div class="pulse-cards">
        <div class="pulse-card" data-tip="active-partners">
            <div class="pc-label">ACTIVE PARTNERS</div>
            <div class="pc-value">{active_partners}</div>
            <div class="pc-sub">API activity in last 30d</div>
        </div>
        <div class="pulse-card" data-tip="quick-ratio">
            <div class="pc-label">QUICK RATIO</div>
            <div class="pc-value">{portfolio_qr:.1f}x</div>
            <div class="pc-sub">(new+res+exp) / (churn+contr)</div>
        </div>
        <div class="pulse-card" data-tip="net-churn">
            <div class="pc-label">NET API CHURN</div>
            <div class="pc-value">{net_churn_display}</div>
            <div class="pc-sub">{net_churn_note}</div>
        </div>
        <div class="pulse-card" data-tip="gross-retention">
            <div class="pc-label">GROSS RETENTION</div>
            <div class="pc-value">{latest_gross_ret:.0f}%</div>
            <div class="pc-sub">30-day rolling</div>
        </div>
    </div>

    <div class="pulse-panels">
        <div class="pulse-panel">
            <div class="panel-title">GROWTH ACCOUNTING WATERFALL</div>
            <div class="panel-subtitle">{pd.Timestamp(latest_ga['month']).strftime('%b %Y')} vs {pd.Timestamp(prior_ga['month']).strftime('%b %Y')} &middot; Prior revenue: ${prior_total:,.0f} &middot; ▸ = {n_months_avg}-month avg</div>
            <div class="waterfall-rows">
                {wf_bar('New', wf_new_pct, avg_new_pct, GAIN)}
                {wf_bar('Expansion', wf_expansion_pct, avg_expansion_pct, GAIN)}
                {wf_bar('Resurrected', wf_resurrected_pct, avg_resurrected_pct, GAIN)}
                <div class="wf-divider"></div>
                {wf_bar('Contraction', wf_contraction_pct, avg_contraction_pct, LOSS, True)}
                {wf_bar('Churned', wf_churned_pct, avg_churned_pct, LOSS, True)}
                <div class="wf-divider"></div>
                <div class="waterfall-row wf-net">
                    <span class="wf-label">Net Growth</span>
                    <div class="waterfall-bar">
                        <div class="wf-track">
                            <div class="wf-fill" style="width:{abs(wf_net_pct)/wf_max*100:.1f}%;background:{GAIN if wf_net_pct >= 0 else LOSS}"></div>
                            <div class="wf-avg-marker" style="left:{abs(avg_net_pct)/wf_max*100:.1f}%" title="Avg: {avg_net_pct:+.1f}%"></div>
                        </div>
                    </div>
                    <span class="wf-value" style="font-weight:600">{'+' if wf_net_pct >= 0 else ''}{wf_net_pct:.1f}%</span>
                    <span class="wf-delta" style="color:{SUCCESS if wf_net_pct > avg_net_pct + 0.5 else DANGER if wf_net_pct < avg_net_pct - 0.5 else MUTED}">{'↑' if wf_net_pct > avg_net_pct + 0.5 else '↓' if wf_net_pct < avg_net_pct - 0.5 else '→'}</span>
                </div>
            </div>
            <div class="wf-summary">
                ${latest_ga['total_revenue']:,.0f} current &middot; {'↑' if wf_net_pct >= 0 else '↓'} ${abs(latest_ga['total_revenue'] - prior_total):,.0f} ({'+' if wf_net_pct >= 0 else ''}{wf_net_pct:.1f}%) &middot; Avg net: {avg_net_pct:+.1f}%/mo
            </div>
            <div class="wf-legend">
                <span class="wf-legend-label">KEY</span>
                <span class="wf-legend-item"><span class="wf-dot" style="background:{GAIN}"></span>Gains</span>
                <span class="wf-legend-item"><span class="wf-dot" style="background:{LOSS}"></span>Losses</span>
                <span class="wf-legend-item"><span class="wf-avg-dot"></span>Period avg</span>
                <span class="wf-legend-item"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:transparent;border:1.5px solid {MUTED}"></span>↑↓ vs avg</span>
            </div>
        </div>

        <div class="pulse-panel pulse-panel-chart">
            <div class="panel-title">GROWTH ACCOUNTING + CMGR</div>
            <div class="panel-subtitle">Revenue breakdown with compound monthly growth rate (click legend to toggle CMGR lines)</div>
            {ga_cmgr_div}
            {cmgr_note_html}
        </div>
    </div>
</div>
'''

# ============================================================
# TIER 2: PARTNER LIST (color-coded scoreboard)
# ============================================================

def metric_class(val, thresholds, invert=False):
    """Return metric-green/amber/red class. thresholds = (green_threshold, amber_threshold)."""
    if invert:
        # For "last active" where lower is better
        if val < thresholds[0]:
            return 'metric-green'
        elif val <= thresholds[1]:
            return 'metric-amber'
        return 'metric-red'
    else:
        if val > thresholds[0]:
            return 'metric-green'
        elif val >= thresholds[1]:
            return 'metric-amber'
        return 'metric-red'

partner_rows = ''
for m in company_metrics:
    # Credit payback progress bar
    payback_pct = min(m['roi'] * 100, 100)
    if m['roi'] >= 1:
        bar_color = SUCCESS
        bar_label = f'{m["roi"]:.1f}x'
    elif m['roi'] >= 0.5:
        bar_color = WARNING
        bar_label = f'{payback_pct:.0f}%'
    else:
        bar_color = DANGER
        bar_label = f'{payback_pct:.0f}%'
    overflow = m['roi'] > 1
    bar_extra_class = ' payback-overflow' if overflow else ''

    cmgr3_val = m['cmgr3'] if m['cmgr3'] is not None else 0
    cagr_cls = metric_class(cmgr3_val, (0.10, 0.03))  # >10% green, 3-10% amber, <3% red
    qr_cls = metric_class(m['avg_qr'], (2.0, 1.0))
    gret_cls = metric_class(m['gross_retention'], (80, 60))
    last_cls = metric_class(m['last_active_days'], (7, 14), invert=True)

    # Last active display
    la = m['last_active_days']
    la_display = f'{la}d ago' if la > 0 else 'Today'

    s_row = startups[startups['startup_id'] == m['sid']]
    archetype = s_row.iloc[0]['archetype'] if len(s_row) > 0 and 'archetype' in s_row.columns else 'unknown'

    rev_display = f'${m["latest_mrr"]:,.0f}' if m['latest_mrr'] >= 1 else '$0'
    mau_display = f'{m["active_devs"]}'

    partner_rows += f'''<tr class="perf-row" data-sid="{m['sid']}" data-name="{m['name'].lower()}"
        data-arch="{archetype}" data-revenue="{m['latest_mrr']:.2f}" data-mau="{m['active_devs']}"
        data-payback="{m['roi']:.4f}" data-cmgr="{cmgr3_val:.6f}"
        data-qr="{m['avg_qr']:.4f}" data-gret="{m['gross_retention']:.2f}" data-active="{m['last_active_days']}"
        style="cursor:pointer">
        <td><span class="dot-sm" style="background:{COLORS[m['sid']]}"></span>{m['name']} <span class="stage-badge">{m['stage']}</span></td>
        <td class="metric-cell num">{rev_display}</td>
        <td class="metric-cell num">{mau_display}</td>
        <td class="payback-cell">
            <div class="payback-bar{bar_extra_class}">
                <div class="payback-fill" style="width:{payback_pct}%;background:{bar_color}"></div>
                <span class="payback-label">{bar_label}</span>
            </div>
        </td>
        <td class="metric-cell num {cagr_cls}">{f'{cmgr3_val*100:.1f}%' if m['cmgr3'] is not None else 'n/a'}</td>
        <td class="metric-cell num {qr_cls}">{m['avg_qr']:.1f}x</td>
        <td class="metric-cell num {gret_cls}">{m['gross_retention']:.0f}%</td>
        <td class="metric-cell num {last_cls}">{la_display}</td>
    </tr>'''

# Build archetype filter chips
archetypes = startups['archetype'].dropna().unique().tolist()
archetype_chips = ''.join(f'<button class="arch-chip active" data-arch="{a}">{a.title()}</button>' for a in sorted(archetypes))

tier2_html = f'''
<div class="partner-list-section">
    <div class="pl-header">
        <div class="pl-title">PARTNER LIST</div>
        <div class="pl-subtitle">Click a partner to view full analysis</div>
    </div>
    <div class="pl-controls">
        <input type="text" class="pl-search" id="pl-search" placeholder="Search partners..." autocomplete="off" />
        <div class="pl-filters">
            <span class="pl-filter-label">Filter:</span>
            <button class="arch-chip active" data-arch="all">All</button>
            {archetype_chips}
        </div>
        <div class="pl-count"><span id="pl-visible-count">{len(company_metrics)}</span> of {len(company_metrics)} partners</div>
    </div>
    <div class="partner-list card">
        <table class="perf-table" id="partner-table">
            <thead>
                <tr>
                    <th class="sortable" data-sort="name">Company <span class="sort-icon">⇅</span></th>
                    <th class="num sortable" data-sort="revenue">Revenue <span class="sort-icon">⇅</span></th>
                    <th class="num sortable" data-sort="mau">MAU <span class="sort-icon">⇅</span></th>
                    <th class="sortable" data-sort="payback" data-tip="credit-payback">Credit Payback <span class="sort-icon">⇅</span></th>
                    <th class="num sortable" data-sort="cmgr" data-tip="cmgr">CMGR-3 <span class="sort-icon">⇅</span></th>
                    <th class="num sortable" data-sort="qr" data-tip="quick-ratio">Quick Ratio <span class="sort-icon">⇅</span></th>
                    <th class="num sortable" data-sort="gret" data-tip="gross-retention">Gross Ret. <span class="sort-icon">⇅</span></th>
                    <th class="num sortable" data-sort="active" data-tip="last-active">Last Active <span class="sort-icon">⇅</span></th>
                </tr>
            </thead>
            <tbody>{partner_rows}</tbody>
        </table>
    </div>
</div>
'''

# ============================================================
# TIER 3: STARTUP TAB CONTENT (restructured)
# ============================================================

def startup_kpis(sid):
    m = next(x for x in company_metrics if x['sid'] == sid)
    d_dga = dev_ga[dev_ga['startup_id'] == sid].sort_values('month')
    latest_dqr = d_dga.iloc[-1]['dev_quick_ratio'] if len(d_dga) > 0 else 0

    roi_color = SUCCESS if m['roi'] > 2 else WARNING if m['roi'] > 1 else DANGER
    cagr_color = SUCCESS if m['token_cagr'] > 2 else WARNING if m['token_cagr'] > 0.5 else DANGER
    dqr_color = SUCCESS if latest_dqr > 2 else WARNING if latest_dqr > 1 else DANGER

    html = '<div class="kpi-row">'
    html += f'''<div class="kpi kpi-expandable" onclick="this.classList.toggle('expanded')">
        <div class="kpi-l">Total Revenue</div>
        <div class="kpi-v">${m["total_rev"]:,.0f}</div>
        <div class="kpi-s">all time &middot; <span class="expand-hint">click to expand</span></div>
        <div class="kpi-breakdown">
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['sonnet']}"></span>Sonnet <span style="color:{MODEL_COLORS['sonnet']}">${m["sonnet_total"]:,.0f}</span> <span class="kpi-s">{m["sonnet_total"]/max(m["total_rev"],1)*100:.0f}%</span></div>
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['opus']}"></span>Opus <span style="color:{MODEL_COLORS['opus']}">${m["opus_total"]:,.0f}</span> <span class="kpi-s">{m["opus_total"]/max(m["total_rev"],1)*100:.0f}%</span></div>
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['haiku']}"></span>Haiku <span style="color:{MODEL_COLORS['haiku']}">${m["haiku_total"]:,.0f}</span> <span class="kpi-s">{m["haiku_total"]/max(m["total_rev"],1)*100:.0f}%</span></div>
        </div>
    </div>'''
    html += kpi('Latest MRR', f'${m["latest_mrr"]:,.0f}', 'API revenue')
    cmgr3_display = f'{m["cmgr3"]*100:.1f}%' if m['cmgr3'] is not None else 'n/a'
    cmgr6_display = f'{m["cmgr6"]*100:.1f}%' if m['cmgr6'] is not None else 'n/a'
    cmgr12_display = f'{m["cmgr12"]*100:.1f}%' if m['cmgr12'] is not None else 'n/a'
    cmgr_color = SUCCESS if (m['cmgr3'] or 0) > 0.10 else WARNING if (m['cmgr3'] or 0) > 0.03 else DANGER
    html += f'''<div class="kpi" data-tip="cmgr">
        <div class="kpi-l">CMGR</div>
        <div class="kpi-v" style="color:{cmgr_color}">{cmgr3_display}</div>
        <div class="kpi-s">trailing 3mo</div>
        <div class="kpi-breakdown" style="display:block;margin-top:6px">
            <div class="kpi-breakdown-row">6mo: {cmgr6_display}</div>
            <div class="kpi-breakdown-row">12mo: {cmgr12_display}</div>
        </div>
    </div>'''
    html += kpi('Credit ROI', f'{m["roi"]:.1f}x', f'${m["credits"]:,.0f} invested', roi_color)
    html += kpi('Active Devs', f'{m["active_devs"]}', 'current month')
    html += kpi('Dev Quick Ratio', f'{latest_dqr:.1f}x' if not np.isnan(latest_dqr) else 'N/A', 'new+resurrected / churned', dqr_color)
    html += '</div>'
    return html

def startup_tab_html(sid):
    s = startups[startups['startup_id'] == sid].iloc[0]
    ch = startup_charts[sid]
    m = next(x for x in company_metrics if x['sid'] == sid)
    d_dga = dev_ga[dev_ga['startup_id'] == sid]
    latest_dqr = d_dga.dropna(subset=['dev_quick_ratio'])['dev_quick_ratio'].iloc[-1] if len(d_dga.dropna(subset=['dev_quick_ratio'])) > 0 else 0

    html = f'''
    <div class="startup-hero" style="border-left: 4px solid {COLORS[sid]}">
        <div class="hero-top">
            <div>
                <span class="hero-name">{s['startup_name']}</span>
                <span class="badge" style="background:{COLORS[sid]}">{s['stage'].upper()}</span>
            </div>
            <span class="hero-meta">{s['vertical']} &middot; {s['hq_city']}, {s['country']}</span>
        </div>
        <p class="hero-desc">{s['description']}</p>
    </div>

    {startup_kpis(sid)}

    <!-- SECTION 1: Growth Overview — Revenue GA first -->
    <div class="analysis-section" data-section="{sid}-rev-ga">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">&#x25BC;</span> Growth Overview</div>
            <div class="analysis-summary">
                <span class="sum-item">MRR <span class="sum-val">${m['latest_mrr']:,.0f}</span></span>
                <span class="sum-item">CMGR-3 <span class="sum-val">{f"{m['cmgr3']*100:.1f}%" if m['cmgr3'] is not None else "n/a"}</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-rev-ga">
                <div class="mode-tab active" data-mode="ga">Growth Accounting</div>
                <div class="mode-tab" data-mode="qr">Quick Ratio</div>
                <div class="mode-tab" data-mode="rev-tok">Revenue & Tokens</div>
            </div>
            <div class="mode-panel active" data-mode="ga">
                <div class="row-1"><div class="card">{ch['growth_acct']}</div></div>
            </div>
            <div class="mode-panel" data-mode="qr">
                <div class="row-1"><div class="card">{ch.get('spend_qr', '')}</div></div>
            </div>
            <div class="mode-panel" data-mode="rev-tok">
                <div class="row-2">
                    <div class="card">{ch['revenue']}</div>
                    <div class="card">{ch['tokens']}</div>
                </div>
            </div>
        </div>
    </div>

    <!-- SECTION 2: Developer Adoption — GA first -->
    <div class="analysis-section" data-section="{sid}-user-ga">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">&#x25BC;</span> Developer Adoption</div>
            <div class="analysis-summary">
                <span class="sum-item">Devs <span class="sum-val">{m['active_devs']}</span></span>
                <span class="sum-item">QR <span class="sum-val">{latest_dqr:.1f}x</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-user-ga">
                <div class="mode-tab active" data-mode="ga">Growth Accounting</div>
                <div class="mode-tab" data-mode="qr">Quick Ratio</div>
                {'<div class="mode-tab" data-mode="retention">Cohort Retention</div>' if 'dev_retention' in ch else ''}
            </div>
            <div class="mode-panel active" data-mode="ga">
                <div class="row-1"><div class="card">{ch['dev_ga']}</div></div>
            </div>
            <div class="mode-panel" data-mode="qr">
                <div class="row-1"><div class="card">{ch['dev_qr']}</div></div>
            </div>
            {'<div class="mode-panel" data-mode="retention"><div class="row-1"><div class="card">' + ch['dev_retention'] + '</div></div></div>' if 'dev_retention' in ch else ''}
        </div>
    </div>

    <!-- SECTION 3: Cohort Analysis -->
    <div class="analysis-section" data-section="{sid}-cohorts">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">&#x25BC;</span> Cohort Analysis</div>
            <div class="analysis-summary">
                <span class="sum-item">Gross Ret <span class="sum-val">{m['gross_retention']:.0f}%</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-cohorts">
                {'<div class="mode-tab active" data-mode="ltv-heat">LTV Heatmap</div>' if 'ltv_heatmap' in ch else '<div class="mode-tab active" data-mode="ltv">LTV Curve</div>'}
                {'<div class="mode-tab" data-mode="ltv">LTV Curve</div>' if 'ltv_heatmap' in ch else ''}
                {'<div class="mode-tab" data-mode="ltv-heat">LTV Heatmap</div>' if 'ltv_heatmap' not in ch else ''}
                {'<div class="mode-tab" data-mode="ret-heat">Retention Heatmap</div>' if 'retention_heatmap' in ch else ''}
                {'<div class="mode-tab" data-mode="rev-ret">Revenue Retention</div>' if 'rev_retention' in ch else ''}
                {'<div class="mode-tab" data-mode="gross-ret">Gross Retention</div>' if 'gross_ret' in ch else ''}
            </div>
            {'<div class="mode-panel active" data-mode="ltv-heat"><div class="row-1"><div class="card">' + ch['ltv_heatmap'] + '</div></div></div>' if 'ltv_heatmap' in ch else '<div class="mode-panel active" data-mode="ltv"><div class="row-1"><div class="card">' + ch.get('ltv_curve', '') + '</div></div></div>'}
            {'<div class="mode-panel" data-mode="ltv"><div class="row-1"><div class="card">' + ch.get('ltv_curve', '') + '</div></div></div>' if 'ltv_heatmap' in ch else ''}
            {'<div class="mode-panel" data-mode="ret-heat"><div class="row-1"><div class="card">' + ch['retention_heatmap'] + '</div></div></div>' if 'retention_heatmap' in ch else ''}
            {'<div class="mode-panel" data-mode="rev-ret"><div class="row-1"><div class="card">' + ch['rev_retention'] + '</div></div></div>' if 'rev_retention' in ch else ''}
            {'<div class="mode-panel" data-mode="gross-ret"><div class="row-1"><div class="card">' + ch['gross_ret'] + '</div></div></div>' if 'gross_ret' in ch else ''}
        </div>
    </div>

    <!-- SECTION 4: Revenue by Model -->
    <div class="analysis-section" data-section="{sid}-model">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">&#x25BC;</span> Revenue by Model</div>
            <div class="analysis-summary">
                <span class="sum-item">S/O/H <span class="sum-val">${m['sonnet_rev']:,.0f}/${m['opus_rev']:,.0f}/${m['haiku_rev']:,.0f}</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-model">
                <div class="mode-tab active" data-mode="model">By Model</div>
                <div class="mode-tab" data-mode="mix">Model Mix</div>
            </div>
            <div class="mode-panel active" data-mode="model">
                <div class="row-1"><div class="card">{ch['rev_by_model']}</div></div>
            </div>
            <div class="mode-panel" data-mode="mix">
                <div class="row-1"><div class="card">{ch['model_mix']}</div></div>
            </div>
        </div>
    </div>

    <!-- SECTION 5: Adoption & Reliability -->
    <div class="analysis-section" data-section="{sid}-adoption">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">&#x25BC;</span> Adoption & Reliability</div>
            <div class="analysis-summary">
                <span class="sum-item">Latency <span class="sum-val">{m['latest_latency']:.0f}ms</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-adoption">
                <div class="mode-tab active" data-mode="devs">API Calls & Devs</div>
                <div class="mode-tab" data-mode="latency">Latency & Errors</div>
                {'<div class="mode-tab" data-mode="engagement">Engagement (L28)</div>' if 'engagement' in ch else ''}
            </div>
            <div class="mode-panel active" data-mode="devs">
                <div class="row-1"><div class="card">{ch['devs_calls']}</div></div>
            </div>
            <div class="mode-panel" data-mode="latency">
                <div class="row-1"><div class="card">{ch['latency']}</div></div>
            </div>
            {'<div class="mode-panel" data-mode="engagement"><div class="row-1"><div class="card">' + ch['engagement'] + '</div></div></div>' if 'engagement' in ch else ''}
        </div>
    </div>
    '''
    return html

# ============================================================
# GROWTH SCOREBOARD (scale × velocity table)
# ============================================================

def fmt_tokens(v):
    if v >= 1e9: return f'{v/1e9:.1f}B'
    if v >= 1e6: return f'{v/1e6:.1f}M'
    if v >= 1e3: return f'{v/1e3:.0f}K'
    return f'{v:.0f}'

def fmt_dollar(v):
    if v >= 1e6: return f'${v/1e6:.1f}M'
    if v >= 1e3: return f'${v/1e3:.0f}K'
    return f'${v:,.0f}'

scoreboard_data = []
for m in company_metrics:
    sid = m['sid']
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    tok_series = u['total_tokens']
    latest_tokens = u.iloc[-1]['total_tokens']
    latest_rev = u.iloc[-1]['revenue_usd']

    # Per-company CMGR
    c3 = cmgr(tok_series, 3) if len(tok_series) > 3 else 0
    c6 = cmgr(tok_series, 6) if len(tok_series) > 6 else 0
    c12 = cmgr(tok_series, 12) if len(tok_series) > 12 else 0

    # Metric 1: Absolute Monthly Token Growth
    abs_growth = latest_tokens * c3 if c3 > 0 else 0

    # Metric 2: Growth-Weighted Volume Score
    import math
    gw_score = math.log10(max(latest_tokens, 1)) * c3 * 100

    # Metric 3: Projected 12-month Token Run-Rate
    proj_12mo = latest_tokens * (1 + c3) ** 12 if c3 > -1 else 0

    # Metric 4: Revenue Impact (6-month projected)
    rev_impact_6mo = latest_rev * (1 + c3) ** 6 if c3 > -1 else 0

    scoreboard_data.append(dict(
        sid=sid, name=m['name'], latest_tokens=latest_tokens, latest_rev=latest_rev,
        cmgr3=c3, cmgr6=c6, cmgr12=c12,
        abs_growth=abs_growth, gw_score=gw_score,
        proj_12mo=proj_12mo, rev_impact_6mo=rev_impact_6mo,
    ))

# Sort by projected 12-month run-rate (default)
scoreboard_data.sort(key=lambda x: x['proj_12mo'], reverse=True)

# Build table rows
sb_rows = ''
for i, s in enumerate(scoreboard_data):
    rank = i + 1
    # Color CMGR cells
    def cmgr_class(v):
        if v > 0.15: return 'metric-green'
        if v > 0.05: return 'metric-amber'
        return 'metric-red'

    # Highlight top projected run-rate
    proj_class = 'metric-green' if s['proj_12mo'] > scoreboard_data[0]['proj_12mo'] * 0.5 else ''

    sb_rows += f'''<tr class="perf-row" data-sid="{s['sid']}" style="cursor:pointer">
        <td class="rank-cell">{rank}</td>
        <td><span class="dot-sm" style="background:{COLORS[s['sid']]}"></span>{s['name']}</td>
        <td class="num">{fmt_tokens(s['latest_tokens'])}</td>
        <td class="num {cmgr_class(s['cmgr3'])}">{s['cmgr3']*100:.1f}%</td>
        <td class="num {cmgr_class(s['cmgr6'])}">{s['cmgr6']*100:.1f}%</td>
        <td class="num {cmgr_class(s['cmgr12'])}">{s['cmgr12']*100:.1f}%</td>
        <td class="num">{fmt_tokens(s['abs_growth'])}/mo</td>
        <td class="num">{s['gw_score']:.0f}</td>
        <td class="num"><strong>{fmt_tokens(s['proj_12mo'])}</strong></td>
        <td class="num">{fmt_dollar(s['rev_impact_6mo'])}</td>
    </tr>'''

scoreboard_html = f'''
<div class="scoreboard-section">
    <div class="pl-header">
        <div class="pl-title">POWER LAW TRACKER</div>
        <div class="pl-subtitle">Identifying breakout partners — scale × velocity, ranked by projected 12-month run-rate</div>
    </div>
    <div class="partner-list card">
        <table class="perf-table scoreboard-table">
            <thead>
                <tr>
                    <th class="rank-col">#</th>
                    <th>Company</th>
                    <th class="num" data-tip="monthly-tokens">Mo. Tokens</th>
                    <th class="num" data-tip="cmgr3">CMGR-3</th>
                    <th class="num" data-tip="cmgr6">CMGR-6</th>
                    <th class="num" data-tip="cmgr12">CMGR-12</th>
                    <th class="num" data-tip="abs-growth">Abs. Growth</th>
                    <th class="num" data-tip="gw-score">GW Score</th>
                    <th class="num" data-tip="proj-12mo">Proj. 12mo</th>
                    <th class="num" data-tip="rev-impact">Rev. 6mo</th>
                </tr>
            </thead>
            <tbody>{sb_rows}</tbody>
        </table>
    </div>
    <p class="chart-desc">
        <strong>Abs. Growth</strong> = tokens × CMGR-3 (new tokens added per month).
        <strong>GW Score</strong> = log(tokens) × CMGR-3 (balances scale and velocity).
        <strong>Proj. 12mo</strong> = current tokens compounded at CMGR-3 for 12 months.
        <strong>Rev Impact</strong> = current revenue compounded at CMGR-3 for 6 months.
    </p>
</div>
'''

# ============================================================
# PORTFOLIO CONTENT = Tier 1 + Tier 2 + Growth Scoreboard
# ============================================================

portfolio_content = f'''
{tier1_html}
{tier2_html}
{scoreboard_html}
'''

# ============================================================
# ASSEMBLE HTML
# ============================================================

full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Anthropic EMEA Startup Partnerships</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
    --gain: {GAIN};
    --loss: {LOSS};
    --cmgr: {CMGR_BLUE};
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'IBM Plex Sans',-apple-system,sans-serif; background:{BG}; color:{TEXT}; line-height:1.5; }}

.topbar {{ padding:20px 32px 16px; border-bottom:1px solid {GRID}; }}
.topbar-row {{ display:flex; justify-content:space-between; align-items:baseline; }}
.topbar h1 {{ font-size:20px; font-weight:700; letter-spacing:-0.02em; color:{TEXT}; }}
.topbar .subtitle {{ font-size:12px; color:{MUTED}; margin-top:2px; }}
.topbar .meta {{ font-size:11px; color:{MUTED}; }}

.assumptions {{ padding:10px 32px; background:{ACCENT_SURFACE}; border-bottom:1px solid {GRID}; display:flex; gap:32px; flex-wrap:wrap; }}
.assumptions .a-item {{ font-size:11px; color:{DIM}; }}
.assumptions .a-item strong {{ color:{TEXT}; font-weight:600; }}

.tabs {{ display:flex; padding:0 32px; border-bottom:1px solid {GRID}; background:{BG}; position:sticky; top:0; z-index:100; }}
.tab {{ padding:12px 20px; font-size:13px; font-weight:500; color:{MUTED}; cursor:pointer; border-bottom:2px solid transparent; transition:color .2s ease, border-color .2s ease; user-select:none; }}
.tab:hover {{ color:{DIM}; }}
.tab.active {{ color:{TEXT}; border-bottom-color:{ACCENT}; font-weight:600; }}
.tab .dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; vertical-align:middle; }}

.content {{ padding:28px 32px; }}
.tab-panel {{ display:none; }}
.tab-panel.active {{ display:block; animation:fadeIn 0.2s ease; }}

.section-header {{ font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:{MUTED}; margin:24px 0 12px; padding-bottom:6px; border-bottom:1px solid {GRID}; }}
.section-header:first-child {{ margin-top:0; }}

.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:24px; }}
.kpi {{ background:{CARD}; border:1px solid {GRID}; border-radius:10px; padding:16px 20px; }}
.kpi-l {{ font-size:10px; text-transform:uppercase; letter-spacing:.05em; color:{MUTED}; font-weight:600; margin-bottom:3px; }}
.kpi-v {{ font-size:24px; font-weight:700; font-variant-numeric:tabular-nums; }}
.kpi-s {{ font-size:11px; color:{MUTED}; }}

.card {{ background:{CARD}; border:1px solid {GRID}; border-radius:8px; padding:16px; overflow:hidden; }}
.row-1 {{ display:grid; grid-template-columns:1fr; gap:16px; margin-bottom:16px; }}
.row-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}

.startup-hero {{ background:{CARD}; border:1px solid {GRID}; border-radius:10px; padding:20px 24px; margin-bottom:20px; }}
.hero-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }}
.hero-name {{ font-size:18px; font-weight:700; margin-right:10px; color:{TEXT}; }}
.badge {{ font-size:9px; font-weight:700; padding:2px 8px; border-radius:10px; color:#fff; letter-spacing:.04em; vertical-align:middle; }}
.hero-meta {{ font-size:12px; color:{MUTED}; }}
.hero-desc {{ font-size:12px; color:{DIM}; margin-top:4px; }}

.dot-sm {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; vertical-align:middle; }}

/* Expandable KPI */
.kpi-expandable {{ cursor:pointer; position:relative; }}
.kpi-expandable .expand-hint {{ color:{ACCENT}; font-size:9px; }}
.kpi-expandable .kpi-breakdown {{ max-height:0; overflow:hidden; transition:max-height 0.3s ease, opacity 0.3s ease, margin 0.2s ease; opacity:0; margin-top:0; }}
.kpi-expandable.expanded .kpi-breakdown {{ max-height:120px; opacity:1; margin-top:10px; }}
.kpi-expandable.expanded .expand-hint {{ display:none; }}
.kpi-breakdown-row {{ display:flex; align-items:center; gap:8px; font-size:12px; color:{DIM}; padding:3px 0; }}
.kpi-breakdown-row span.kpi-s {{ margin-left:auto; }}

/* Collapsible analysis sections */
.analysis-section {{ background:{CARD}; border:1px solid {GRID}; border-radius:10px; margin-bottom:18px; overflow:hidden; }}
.analysis-header {{ display:flex; align-items:center; justify-content:space-between; padding:14px 20px; cursor:pointer; user-select:none; transition:background 0.15s; }}
.analysis-header:hover {{ background:{ACCENT_SURFACE}; }}
.analysis-title {{ font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:{TEXT}; display:flex; align-items:center; gap:8px; }}
.analysis-title .chevron {{ font-size:10px; color:{MUTED}; transition:transform 0.25s; }}
.analysis-section.collapsed .chevron {{ transform:rotate(-90deg); }}
.analysis-summary {{ font-size:11px; color:{MUTED}; display:flex; gap:16px; }}
.analysis-summary .sum-item {{ white-space:nowrap; }}
.analysis-summary .sum-val {{ font-weight:600; color:{DIM}; }}
.analysis-body {{ padding:0 20px 16px; transition:max-height 0.4s cubic-bezier(0.4,0,0.2,1), opacity 0.3s ease, padding 0.3s ease; overflow:hidden; }}
.analysis-section.collapsed .analysis-body {{ max-height:0 !important; padding-top:0; padding-bottom:0; opacity:0; }}

/* Mode tabs within sections */
.mode-tabs {{ display:flex; gap:2px; margin-bottom:14px; background:{BG}; border-radius:6px; padding:2px; border:1px solid {GRID}; width:fit-content; }}
.mode-tab {{ padding:6px 14px; font-size:11px; font-weight:500; color:{MUTED}; cursor:pointer; border-radius:4px; transition:background 0.2s ease, color 0.2s ease; user-select:none; white-space:nowrap; }}
.mode-tab:hover {{ color:{DIM}; background:rgba(71,57,130,0.03); }}
.mode-tab.active {{ background:{ACCENT_LIGHT}; color:{TEXT}; font-weight:600; }}
.mode-panel {{ display:none; animation:fadeIn 0.25s ease; }}
.mode-panel.active {{ display:block; }}
@keyframes fadeIn {{ from {{ opacity:0; transform:translateY(4px); }} to {{ opacity:1; transform:translateY(0); }} }}

/* Chart descriptions */
.chart-desc {{ font-size:11px; color:{DIM}; line-height:1.6; margin-top:10px; padding:0 4px; }}
.chart-desc strong {{ color:{TEXT}; font-weight:600; }}

/* ========== TIER 1: PULSE BLOCK ========== */
.pulse-block {{ margin-bottom:40px; padding-bottom:32px; border-bottom:1px solid {GRID}; }}

.pulse-cards {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin-bottom:20px; }}
.pulse-card {{ background:{CARD}; border:1px solid {GRID}; border-radius:10px; padding:18px 20px; transition:border-color 0.2s ease, box-shadow 0.2s ease; }}
.pulse-card:hover {{ border-color:#d4d0da; box-shadow:0 1px 4px rgba(0,0,0,0.04); }}
.pc-label {{ font-size:10px; text-transform:uppercase; letter-spacing:0.05em; color:{MUTED}; font-weight:600; margin-bottom:4px; }}
.pc-value {{ font-size:24px; font-weight:700; color:{TEXT}; font-variant-numeric:tabular-nums; }}
.pc-sub {{ font-size:11px; color:{MUTED}; margin-top:3px; }}

.pulse-panels {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.pulse-panel {{ background:#fff; border:1px solid {GRID}; border-radius:12px; padding:22px 24px; }}
.pulse-panel-chart {{ padding:14px 10px 6px; overflow:hidden; }}
.panel-title {{ font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:{MUTED}; font-weight:700; margin-bottom:6px; }}
.panel-subtitle {{ font-size:11px; color:{MUTED}; margin-bottom:18px; }}

/* Waterfall rows */
.waterfall-rows {{ display:flex; flex-direction:column; gap:8px; }}
.waterfall-row {{ display:grid; grid-template-columns:100px 1fr 60px 20px; align-items:center; gap:8px; }}
.wf-label {{ font-size:12px; color:{DIM}; text-align:right; }}
.waterfall-bar {{ flex:1; }}
.wf-track {{ height:18px; background:{BORDER_SUBTLE}; border-radius:3px; overflow:visible; position:relative; }}
.wf-fill {{ height:100%; border-radius:3px; transition:width 0.4s ease; }}
.wf-avg-marker {{ position:absolute; top:-2px; width:2px; height:22px; background:{TEXT}; opacity:0.35; border-radius:1px; }}
.wf-avg-marker::after {{ content:'▸'; position:absolute; top:-1px; left:4px; font-size:8px; color:{MUTED}; }}
.wf-value {{ font-size:12px; font-weight:500; text-align:right; }}
.wf-delta {{ font-size:14px; font-weight:600; text-align:center; cursor:help; }}
.wf-net .wf-label {{ font-weight:600; color:{TEXT}; }}
.wf-divider {{ height:1px; background:{BORDER_SUBTLE}; margin:4px 0; }}
.wf-summary {{ font-size:11px; color:{DIM}; margin-top:14px; padding:8px 12px; background:{CARD}; border-radius:6px; border:1px solid {GRID}; }}
.wf-legend {{ display:flex; gap:16px; margin-top:12px; justify-content:center; padding:8px 0 4px; border-top:1px solid {GRID}; }}
.wf-legend-label {{ font-size:9px; font-weight:700; color:{DIM}; text-transform:uppercase; letter-spacing:0.06em; margin-right:4px; }}
.wf-legend-item {{ font-size:11px; color:{MUTED}; display:flex; align-items:center; gap:4px; }}
.wf-dot {{ width:8px; height:8px; border-radius:50%; }}
.wf-avg-dot {{ width:2px; height:12px; background:{TEXT}; opacity:0.35; border-radius:1px; }}

/* Hover tooltips */
[data-tooltip] {{ cursor:help; }}
.tooltip-box {{ position:fixed; background:{TEXT}; color:{BG}; padding:10px 14px; border-radius:8px; font-size:11px; font-weight:400; font-family:Inter,-apple-system,sans-serif; white-space:normal; width:260px; text-align:left; line-height:1.5; z-index:10000; pointer-events:none; box-shadow:0 4px 16px rgba(0,0,0,0.2); opacity:0; transition:opacity 0.15s ease; }}
.tooltip-box.visible {{ opacity:1; }}
.tooltip-box .tip-title {{ font-weight:600; font-size:12px; margin-bottom:6px; color:#fff; }}
.tooltip-box .tip-formula {{ font-family:'IBM Plex Mono',ui-monospace,monospace; font-size:12px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.12); padding:8px 12px; border-radius:6px; margin:8px 0; color:#c4b5fd; display:flex; align-items:center; flex-wrap:nowrap; gap:0; white-space:nowrap; }}
.tooltip-box .tip-formula .frac {{ display:inline-flex; flex-direction:column; align-items:center; vertical-align:middle; margin:0 2px; }}
.tooltip-box .tip-formula .frac-num {{ border-bottom:1px solid #c4b5fd; padding:0 4px 1px; font-size:10px; text-align:center; white-space:nowrap; }}
.tooltip-box .tip-formula .frac-den {{ padding:1px 4px 0; font-size:10px; text-align:center; white-space:nowrap; }}
.tooltip-box .tip-formula .paren {{ font-weight:300; color:#a78bfa; font-size:14px; align-self:stretch; display:flex; align-items:center; }}
.tooltip-box .tip-formula sup {{ font-size:8px; vertical-align:super; color:#e9d5ff; margin-left:1px; }}
.tooltip-box .tip-formula sub {{ font-size:8px; vertical-align:sub; color:#e9d5ff; }}
.tooltip-box .tip-formula .op {{ margin:0 3px; color:#94a3b8; }}
.tooltip-box .tip-body {{ color:rgba(255,255,255,0.8); margin-top:2px; }}
.tooltip-box .tip-bench {{ font-size:10px; color:rgba(255,255,255,0.5); margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.1); }}
.tip-defs {{ display:none; }}

/* CMGR rows */
.cmgr-rows {{ display:flex; flex-direction:column; gap:12px; }}
.cmgr-row {{ display:grid; grid-template-columns:60px 1fr 60px; align-items:center; gap:8px; }}
.cmgr-label {{ font-size:12px; color:{DIM}; font-weight:500; text-align:right; }}
.cmgr-bar-track {{ height:8px; background:{BORDER_SUBTLE}; border-radius:4px; overflow:hidden; }}
.cmgr-bar-fill {{ height:100%; background:var(--cmgr); border-radius:4px; transition:width 0.4s ease; }}
.cmgr-value {{ font-size:12px; font-weight:500; color:{TEXT}; text-align:right; }}
.cmgr-note {{ font-size:11px; margin-top:14px; padding:8px 12px; border-radius:6px; }}
.cmgr-note.decel {{ background:rgba(239,68,68,0.08); color:{DANGER}; }}
.cmgr-note.accel {{ background:rgba(34,197,94,0.08); color:{SUCCESS}; }}

/* ========== TIER 2: PARTNER LIST ========== */
.partner-list-section {{ margin-top:0; margin-bottom:40px; padding-bottom:32px; border-bottom:1px solid {GRID}; }}
.pl-header {{ margin-bottom:14px; }}
.pl-title {{ font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:{TEXT}; }}
.pl-subtitle {{ font-size:12px; color:{MUTED}; margin-top:3px; }}

/* Partner list controls */
.pl-controls {{ display:flex; align-items:center; gap:12px; margin-bottom:14px; flex-wrap:wrap; }}
.pl-search {{ padding:7px 12px; border:1px solid {GRID}; border-radius:8px; font-size:12px; font-family:Inter,sans-serif; background:{CARD}; color:{TEXT}; width:200px; outline:none; transition:border-color 0.2s; }}
.pl-search:focus {{ border-color:#3b82f6; }}
.pl-search::placeholder {{ color:{MUTED}; }}
.pl-filters {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}
.pl-filter-label {{ font-size:10px; text-transform:uppercase; letter-spacing:0.05em; color:{DIM}; font-weight:600; }}
.arch-chip {{ padding:4px 10px; border-radius:12px; border:1px solid {GRID}; background:transparent; color:{MUTED}; font-size:11px; font-family:Inter,sans-serif; cursor:pointer; transition:all 0.15s; }}
.arch-chip:hover {{ border-color:{MUTED}; }}
.arch-chip.active {{ background:rgba(59,130,246,0.08); border-color:rgba(59,130,246,0.3); color:{TEXT}; }}
.pl-count {{ font-size:11px; color:{DIM}; margin-left:auto; }}

/* Sortable columns */
.sortable {{ cursor:pointer; user-select:none; transition:color 0.15s; }}
.sortable:hover {{ color:{TEXT}; }}
.sort-icon {{ font-size:10px; color:{DIM}; margin-left:2px; }}
.sortable.sort-asc .sort-icon::after {{ content:'↑'; }}
.sortable.sort-desc .sort-icon::after {{ content:'↓'; }}
.sortable.sort-asc .sort-icon, .sortable.sort-desc .sort-icon {{ color:#3b82f6; }}

/* Scoreboard */
.scoreboard-section {{ margin-top:0; }}
.scoreboard-section .pl-title {{ font-size:13px; }}
.scoreboard-table .rank-col {{ width:28px; }}
.rank-cell {{ font-size:12px; font-weight:600; color:{MUTED}; text-align:center; }}
.scoreboard-table td {{ font-size:12px; font-variant-numeric:tabular-nums; padding:9px 10px; }}
.scoreboard-table th {{ padding:9px 10px; }}
.partner-list {{ padding:0; overflow-x:auto; position:relative; }}
.partner-list::after {{ content:''; position:absolute; right:0; top:0; bottom:0; width:40px; background:linear-gradient(90deg, transparent, {CARD}); pointer-events:none; opacity:0; transition:opacity 0.3s; }}
.partner-list.scrollable::after {{ opacity:1; }}

.perf-table {{ width:100%; border-collapse:collapse; font-size:13px; font-variant-numeric:tabular-nums; }}
.perf-table th {{ text-align:left; padding:10px 14px; border-bottom:1px solid {GRID}; color:{MUTED}; font-size:10px; text-transform:uppercase; letter-spacing:0.05em; font-weight:600; white-space:nowrap; }}
.perf-table th.num {{ text-align:right; }}
.perf-table td {{ padding:10px 14px; border-bottom:1px solid {BORDER_SUBTLE}; white-space:nowrap; color:{DIM}; font-variant-numeric:tabular-nums; }}
.perf-table td.num {{ text-align:right; }}
.perf-table tr:last-child td {{ border-bottom:none; }}
.perf-table .perf-row {{ transition:background 0.15s ease; }}
.perf-table .perf-row:hover {{ background:{ACCENT_SURFACE}; }}
.perf-table .perf-row td:first-child {{ font-weight:600; color:{TEXT}; }}

.stage-badge {{ font-size:9px; font-weight:600; padding:1px 6px; border-radius:8px; background:{ACCENT_LIGHT}; color:{ACCENT}; text-transform:uppercase; letter-spacing:0.03em; margin-left:6px; }}

/* Credit payback progress bar */
.payback-cell {{ min-width:120px; }}
.payback-bar {{ position:relative; height:18px; background:{BORDER_SUBTLE}; border-radius:9px; overflow:visible; }}
.payback-fill {{ height:100%; border-radius:9px; transition:width 0.6s cubic-bezier(0.22,1,0.36,1); min-width:2px; }}
.payback-overflow .payback-fill {{ border-radius:9px; box-shadow:0 0 6px rgba(34,197,94,0.4); }}
.payback-label {{ position:absolute; right:6px; top:50%; transform:translateY(-50%); font-size:10px; font-weight:700; color:{TEXT}; }}
.payback-overflow .payback-label {{ color:#fff; }}

/* Metric cell color coding */
.metric-cell {{ font-weight:500; font-variant-numeric:tabular-nums; }}
.metric-cell.metric-green {{ color:{SUCCESS}; }}
.metric-cell.metric-amber {{ color:{WARNING}; }}
.metric-cell.metric-red {{ color:{DANGER}; }}

html {{ scroll-behavior:smooth; }}

@media (max-width:1100px) {{
    .pulse-panels {{ grid-template-columns:1fr; }}
}}

@media (max-width:900px) {{
    .row-2 {{ grid-template-columns:1fr; }}
    .kpi-row {{ grid-template-columns:1fr 1fr; }}
    .pulse-cards {{ grid-template-columns:1fr 1fr; }}
    .assumptions {{ flex-direction:column; gap:8px; }}
    .content {{ padding:16px; }}
    .topbar {{ padding:16px; }}
    .waterfall-row {{ grid-template-columns:80px 1fr 55px 18px; gap:6px; }}
    .wf-label {{ font-size:12px; }}
    .wf-value {{ font-size:12px; }}
    .perf-table {{ display:block; overflow-x:auto; -webkit-overflow-scrolling:touch; }}
    .scoreboard {{ display:block; overflow-x:auto; -webkit-overflow-scrolling:touch; }}
}}

@media (max-width:680px) {{
    .tabs {{ overflow-x:auto; -webkit-overflow-scrolling:touch; scrollbar-width:none; }}
    .tabs::-webkit-scrollbar {{ display:none; }}
    .tab {{ padding:10px 14px; font-size:12px; flex-shrink:0; }}
    .topbar-row {{ flex-direction:column; gap:4px; }}
    .topbar .meta {{ font-size:10px; }}
    .topbar h1 {{ font-size:17px; }}
    .waterfall-row {{ grid-template-columns:72px 1fr 52px 16px; gap:4px; }}
    .wf-label {{ font-size:11px; }}
    .wf-value {{ font-size:11px; }}
    .wf-delta {{ font-size:12px; }}
    .pulse-panel {{ padding:14px 12px; overflow-x:auto; }}
    .pulse-panel-chart {{ padding:8px 2px 4px; }}
    .pl-subtitle {{ font-size:11px; }}
    .chart-desc {{ font-size:10px; }}
    .perf-table td {{ padding:8px 10px; font-size:12px; }}
    .perf-table th {{ padding:8px 10px; font-size:9px; }}
    .scoreboard-table td {{ padding:7px 8px; font-size:11px; }}
    .scoreboard-table th {{ padding:7px 8px; font-size:9px; }}
}}

@media (max-width:480px) {{
    .kpi-row {{ grid-template-columns:1fr; }}
    .pulse-cards {{ grid-template-columns:1fr; }}
    .analysis-header {{ flex-direction:column; align-items:flex-start; gap:6px; }}
    .mode-tabs {{ flex-wrap:wrap; }}
}}
</style>
</head>
<body>

<div class="topbar">
    <div class="topbar-row">
        <div>
            <h1>Anthropic EMEA Startup Partnerships</h1>
            <div class="subtitle">Partner Consumption & Credit Economics</div>
        </div>
        <span class="meta">Ongun Ozdemir &middot; Mar 2026 &middot; Synthetic data</span>
    </div>
</div>

<div class="assumptions">
    <div class="a-item"><strong>$10/1M tokens</strong> blended (Sonnet/Opus/Haiku, 5:1 I/O)</div>
    <div class="a-item"><strong>65% gross margin</strong> est.</div>
    <div class="a-item"><strong>$25K base credit</strong> per growth-tier partner</div>
    <div class="a-item"><strong>24 months</strong> Jan 2024 &ndash; Dec 2025</div>
</div>

<div class="tabs">
    <div class="tab active" data-tab="portfolio">Pulse</div>
    {''.join(f'<div class="tab" data-tab="{sid.lower()}"><span class="dot" style="background:{COLORS[sid]}"></span>{NAMES[sid]}</div>' for sid in ALL_SIDS)}
</div>

<div class="content">
    <div class="tab-panel active" id="panel-portfolio">
        {portfolio_content}
    </div>
    {''.join(f'<div class="tab-panel" id="panel-{sid.lower()}">{startup_tab_html(sid)}</div>' for sid in ALL_SIDS)}
</div>

<script>
// ======== TOOLTIP ENGINE (rich HTML) ========
(function() {{
    const tip = document.createElement('div');
    tip.className = 'tooltip-box';
    document.body.appendChild(tip);
    let hideTimeout;

    document.addEventListener('mouseenter', function(e) {{
        const el = e.target.closest('[data-tip]');
        if (!el) return;
        clearTimeout(hideTimeout);
        const id = el.getAttribute('data-tip');
        const src = document.getElementById('tip-' + id);
        if (src) {{
            tip.innerHTML = src.innerHTML;
        }} else {{
            tip.textContent = id;
        }}
        tip.classList.add('visible');

        // Position after content is set so offsetHeight is correct
        requestAnimationFrame(() => {{
            const rect = el.getBoundingClientRect();
            let top = rect.top - tip.offsetHeight - 8;
            let left = rect.left + rect.width / 2 - tip.offsetWidth / 2;
            if (top < 4) top = rect.bottom + 8;
            if (left < 4) left = 4;
            if (left + tip.offsetWidth > window.innerWidth - 4) left = window.innerWidth - tip.offsetWidth - 4;
            tip.style.top = top + 'px';
            tip.style.left = left + 'px';
        }});
    }}, true);

    document.addEventListener('mouseleave', function(e) {{
        const el = e.target.closest('[data-tip]');
        if (!el) return;
        hideTimeout = setTimeout(() => tip.classList.remove('visible'), 100);
    }}, true);
}})();

// Plotly resize helper
function resizePlotlyCharts(container) {{
    if (typeof Plotly !== 'undefined') {{
        const plots = (container || document).querySelectorAll('.js-plotly-plot');
        plots.forEach(p => Plotly.Plots.resize(p));
    }}
}}

// Section collapse/expand
function toggleSection(header) {{
    const section = header.closest('.analysis-section');
    section.classList.toggle('collapsed');
    if (!section.classList.contains('collapsed')) {{
        setTimeout(() => resizePlotlyCharts(section), 120);
    }}
}}

// Mode tab switching within sections
document.querySelectorAll('.mode-tabs').forEach(tabGroup => {{
    tabGroup.querySelectorAll('.mode-tab').forEach(tab => {{
        tab.addEventListener('click', () => {{
            const body = tab.closest('.analysis-body');
            tabGroup.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
            body.querySelectorAll('.mode-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const mode = tab.dataset.mode;
            body.querySelectorAll('.mode-panel[data-mode="' + mode + '"]').forEach(p => {{
                p.classList.add('active');
            }});
            setTimeout(() => resizePlotlyCharts(body), 80);
        }});
    }});
}});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const panel = document.getElementById('panel-' + tab.dataset.tab);
        panel.classList.add('active');
        setTimeout(() => resizePlotlyCharts(panel), 80);
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
}});

// Table row click -> navigate to company tab
document.querySelectorAll('.perf-row').forEach(row => {{
    row.addEventListener('click', () => {{
        const sid = row.dataset.sid.toLowerCase();
        const tab = document.querySelector('[data-tab="' + sid + '"]');
        if (tab) tab.click();
    }});
}});

// ======== PARTNER LIST: SEARCH, FILTER, SORT ========
(function() {{
    const table = document.getElementById('partner-table');
    if (!table) return;
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('.perf-row'));
    const searchInput = document.getElementById('pl-search');
    const countEl = document.getElementById('pl-visible-count');
    const chips = document.querySelectorAll('.arch-chip');

    let activeArch = 'all';
    let searchTerm = '';
    let sortCol = null;
    let sortDir = 'desc';

    function applyFilters() {{
        let visible = 0;
        rows.forEach(row => {{
            const name = row.dataset.name || '';
            const arch = row.dataset.arch || '';
            const matchSearch = !searchTerm || name.includes(searchTerm.toLowerCase());
            const matchArch = activeArch === 'all' || arch === activeArch;
            const show = matchSearch && matchArch;
            row.style.display = show ? '' : 'none';
            if (show) visible++;
        }});
        if (countEl) countEl.textContent = visible;
    }}

    // Search
    if (searchInput) {{
        searchInput.addEventListener('input', (e) => {{
            searchTerm = e.target.value;
            applyFilters();
        }});
    }}

    // Archetype filter chips
    chips.forEach(chip => {{
        chip.addEventListener('click', () => {{
            const arch = chip.dataset.arch;
            if (arch === 'all') {{
                activeArch = 'all';
                chips.forEach(c => c.classList.toggle('active', c.dataset.arch === 'all'));
            }} else {{
                // Deactivate "All" chip
                chips.forEach(c => {{ if (c.dataset.arch === 'all') c.classList.remove('active'); }});
                if (activeArch === arch) {{
                    // Toggle off → back to all
                    activeArch = 'all';
                    chip.classList.remove('active');
                    chips.forEach(c => {{ if (c.dataset.arch === 'all') c.classList.add('active'); }});
                }} else {{
                    chips.forEach(c => {{ if (c.dataset.arch !== 'all') c.classList.remove('active'); }});
                    activeArch = arch;
                    chip.classList.add('active');
                }}
            }}
            applyFilters();
        }});
    }});

    // Column sorting
    const headers = table.querySelectorAll('.sortable');
    headers.forEach(th => {{
        th.addEventListener('click', () => {{
            const col = th.dataset.sort;
            if (sortCol === col) {{
                sortDir = sortDir === 'desc' ? 'asc' : 'desc';
            }} else {{
                sortCol = col;
                sortDir = 'desc';
            }}

            // Update header styles
            headers.forEach(h => {{
                h.classList.remove('sort-asc', 'sort-desc');
                h.querySelector('.sort-icon').textContent = '⇅';
            }});
            th.classList.add(sortDir === 'asc' ? 'sort-asc' : 'sort-desc');
            th.querySelector('.sort-icon').textContent = sortDir === 'asc' ? '↑' : '↓';

            // Sort rows
            rows.sort((a, b) => {{
                let va, vb;
                if (col === 'name') {{
                    va = a.dataset.name || '';
                    vb = b.dataset.name || '';
                    return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
                }}
                va = parseFloat(a.dataset[col]) || 0;
                vb = parseFloat(b.dataset[col]) || 0;
                // For "active" (last active days), lower is better, so invert
                if (col === 'active') {{
                    return sortDir === 'asc' ? va - vb : vb - va;
                }}
                return sortDir === 'asc' ? va - vb : vb - va;
            }});

            rows.forEach(row => tbody.appendChild(row));
        }});
    }});
}})();

// Table scroll indicator
document.querySelectorAll('.partner-list').forEach(wrap => {{
    function checkScroll() {{
        if (wrap.scrollWidth > wrap.clientWidth && wrap.scrollLeft < wrap.scrollWidth - wrap.clientWidth - 10) {{
            wrap.classList.add('scrollable');
        }} else {{
            wrap.classList.remove('scrollable');
        }}
    }}
    checkScroll();
    wrap.addEventListener('scroll', checkScroll);
    window.addEventListener('resize', checkScroll);
}});
</script>

<!-- Hidden tooltip definitions with rich HTML formulas -->
<div class="tip-defs">

<div id="tip-active-partners">
    <div class="tip-title">Active Partners</div>
    <div class="tip-body">Partners with &ge;1 API call in the last 30 days. A declining count signals portfolio churn before it shows in revenue.</div>
</div>

<div id="tip-quick-ratio">
    <div class="tip-title">Quick Ratio</div>
    <div class="tip-formula"><span class="paren">(</span><span class="frac"><span class="frac-num">New + Resurrected + Expansion</span><span class="frac-den">Churned + Contraction</span></span><span class="paren">)</span></div>
    <div class="tip-body">Measures growth efficiency. How many units gained for every unit lost.</div>
    <div class="tip-bench">&gt; 4&times; very healthy &middot; 1&ndash;4&times; moderate &middot; &lt; 1&times; shrinking</div>
</div>

<div id="tip-net-churn">
    <div class="tip-title">Net API Churn</div>
    <div class="tip-formula"><span class="frac"><span class="frac-num">Churned + Contraction &minus; Resurrected &minus; Expansion</span><span class="frac-den">Prior Period Revenue</span></span></div>
    <div class="tip-body">Negative = existing base is growing without new partners. The holy grail of net negative churn.</div>
</div>

<div id="tip-gross-retention">
    <div class="tip-title">Gross Retention</div>
    <div class="tip-formula"><span class="frac"><span class="frac-num">Retained Revenue</span><span class="frac-den">Prior Period Revenue</span></span><span class="op">&times;</span>100</div>
    <div class="tip-body">The floor &mdash; how much revenue survives without new business or expansion.</div>
    <div class="tip-bench">&gt; 80% healthy &middot; 60&ndash;80% watch &middot; &lt; 60% critical</div>
</div>

<div id="tip-credit-payback">
    <div class="tip-title">Credit Payback</div>
    <div class="tip-formula"><span class="frac"><span class="frac-num">Cumulative Revenue</span><span class="frac-den">Credits Granted</span></span></div>
    <div class="tip-body">Above 1&times; = investment has paid back. The progress bar shows proximity to breakeven.</div>
</div>

<div id="tip-cmgr">
    <div class="tip-title">CMGR — Compound Monthly Growth Rate</div>
    <div class="tip-formula"><span class="paren">(</span><span class="frac"><span class="frac-num">V<sub>end</sub></span><span class="frac-den">V<sub>start</sub></span></span><span class="paren">)</span><sup>1/n</sup><span class="op">&minus;</span>1</div>
    <div class="tip-body">Monthly compounding growth rate over a trailing window. CMGR-3 = last 3 months, CMGR-6 = last 6, CMGR-12 = last 12. If CMGR-3 &lt; CMGR-12, growth has decelerated.</div>
    <div class="tip-bench">&gt; 10% strong &middot; 3&ndash;10% healthy &middot; &lt; 3% slow</div>
</div>

<div id="tip-active-devs">
    <div class="tip-title">Active Developers</div>
    <div class="tip-body">Distinct API keys with &ge;1 call in the trailing 30 days. This is a simplification &mdash; the mapping between API keys and actual developers is ambiguous (one dev may use multiple keys, or a team may share one). For consistency, we treat each active API key as one developer.</div>
    <div class="tip-bench">Revenue is driven by tokens &times; model pricing, not developer count. Dev count is an adoption signal &mdash; more devs generally means deeper integration.</div>
</div>

<div id="tip-last-active">
    <div class="tip-title">Last Active</div>
    <div class="tip-body">Days since this partner last made an API call.</div>
    <div class="tip-bench">&lt; 7d healthy &middot; 7&ndash;14d at risk &middot; &gt; 14d dormant</div>
</div>

<div id="tip-monthly-tokens">
    <div class="tip-title">Monthly Tokens</div>
    <div class="tip-body">Total API tokens consumed in the most recent month. Reflects current scale of integration with Claude.</div>
</div>

<div id="tip-cmgr3">
    <div class="tip-title">CMGR-3 &mdash; Compound Monthly Growth Rate</div>
    <div class="tip-formula"><span class="paren">(</span><span class="frac"><span class="frac-num">V<sub>t</sub></span><span class="frac-den">V<sub>t&minus;3</sub></span></span><span class="paren">)</span><sup>1/3</sup><span class="op">&minus;</span>1</div>
    <div class="tip-body">Growth rate over the trailing 3 months. Captures recent momentum.</div>
</div>

<div id="tip-cmgr6">
    <div class="tip-title">CMGR-6</div>
    <div class="tip-formula"><span class="paren">(</span><span class="frac"><span class="frac-num">V<sub>t</sub></span><span class="frac-den">V<sub>t&minus;6</sub></span></span><span class="paren">)</span><sup>1/6</sup><span class="op">&minus;</span>1</div>
    <div class="tip-body">Trailing 6-month CMGR. Smooths short-term volatility. Compare with CMGR-3 to spot acceleration or deceleration.</div>
</div>

<div id="tip-cmgr12">
    <div class="tip-title">CMGR-12</div>
    <div class="tip-formula"><span class="paren">(</span><span class="frac"><span class="frac-num">V<sub>t</sub></span><span class="frac-den">V<sub>t&minus;12</sub></span></span><span class="paren">)</span><sup>1/12</sup><span class="op">&minus;</span>1</div>
    <div class="tip-body">Long-term structural growth rate. If CMGR-3 &lt; CMGR-12, growth is decelerating &mdash; investigate.</div>
</div>

<div id="tip-abs-growth">
    <div class="tip-title">Absolute Monthly Growth</div>
    <div class="tip-formula">Tokens<sub>now</sub><span class="op">&times;</span>CMGR-3</div>
    <div class="tip-body">New tokens added per month. Rewards scale &mdash; a large partner growing slowly adds more than a tiny one growing fast.</div>
</div>

<div id="tip-gw-score">
    <div class="tip-title">Growth-Weighted Score</div>
    <div class="tip-formula">log<sub>10</sub><span class="paren">(</span>Tokens<span class="paren">)</span><span class="op">&times;</span>CMGR-3<span class="op">&times;</span>100</div>
    <div class="tip-body">Balances scale and velocity. Log compresses volume so neither dimension dominates.</div>
</div>

<div id="tip-proj-12mo">
    <div class="tip-title">Projected 12-Month Run-Rate</div>
    <div class="tip-formula">Tokens<sub>now</sub><span class="op">&times;</span><span class="paren">(</span>1 + CMGR-3<span class="paren">)</span><sup>12</sup></div>
    <div class="tip-body">Where this partner lands in a year if trailing 3-month growth continues. The primary power law ranking metric.</div>
</div>

<div id="tip-rev-impact">
    <div class="tip-title">Revenue Impact (6-month)</div>
    <div class="tip-formula">Rev<sub>now</sub><span class="op">&times;</span><span class="paren">(</span>1 + CMGR-3<span class="paren">)</span><sup>6</sup></div>
    <div class="tip-body">Projected monthly revenue in 6 months. Factors in model mix since Opus generates more revenue per token than Haiku.</div>
</div>

</div>

</body>
</html>'''

output_path = '/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/dashboard.html'
with open(output_path, 'w') as f:
    f.write(full_html)

print(f"Dashboard saved: {output_path}")
print(f"Size: {len(full_html) / 1024:.0f} KB")
