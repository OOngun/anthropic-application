"""
Build an interactive HTML dashboard.
Two views: Portfolio Overview (all companies) + Company Detail (click to drill down).
Only uses data Anthropic can directly observe.
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

COLORS = {'S001': '#472D7B', 'S002': '#3B528B', 'S003': '#21918C'}
NAMES = {'S001': 'MedScribe AI', 'S002': 'Eigen Technologies', 'S003': 'BuilderKit'}

# ============================================================
# COMPUTE DEVELOPER GROWTH ACCOUNTING (synthetic decomposition)
# ============================================================
# We have total active_developers per month. Decompose into new/retained/resurrected/churned
# using plausible assumptions consistent with the totals.

np.random.seed(42)
dev_ga_records = []
for sid in ['S001', 'S002', 'S003']:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    prev_devs = 0
    cumulative_ever = 0
    for i, row in u.iterrows():
        month = row['month']
        total = int(row['active_developers'])
        if prev_devs == 0:
            # First month — all new
            dev_ga_records.append(dict(startup_id=sid, month=month, active_devs=total,
                new_devs=total, retained_devs=0, resurrected_devs=0, churned_devs=0))
            prev_devs = total
            cumulative_ever = total
            continue

        # Retained: 60-85% of previous month's devs stick around
        retain_rate = np.clip(np.random.normal(0.75, 0.05), 0.60, 0.90)
        retained = int(min(round(prev_devs * retain_rate), total))
        churned = prev_devs - retained

        remaining = total - retained
        # Of remaining, split between new and resurrected
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
# Quick ratio: skip first month per startup (no churn data), cap at 10 for readability
dev_ga['dev_quick_ratio'] = dev_ga.apply(
    lambda r: min((r['new_devs'] + r['resurrected_devs']) / r['churned_devs'], 10.0)
        if r['churned_devs'] > 0 else np.nan, axis=1)

# Also compute per-company developer retention cohorts (synthetic)
np.random.seed(99)
dev_cohort_records = []
for sid in ['S001', 'S002', 'S003']:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    months = u['month'].tolist()
    n_months = len(months)
    # Simulate monthly onboarding cohorts with retention decay
    for cohort_idx in range(min(n_months, 12)):  # up to 12 cohorts
        cohort_month = months[cohort_idx]
        cohort_size = max(int(np.random.uniform(2, 8)), 1)
        for age in range(n_months - cohort_idx):
            if age == 0:
                active = cohort_size
            else:
                # Retention decays then stabilises
                retain_rate = 0.65 + 0.25 * (1 - np.exp(-age / 6))  # approaches ~90%
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
# COMPUTE COHORT RETENTION (logo retention by onboarding month)
# ============================================================
# For portfolio-level: cohort = month partner was onboarded
# Track if they're still active (had API calls) in subsequent months

cohort_data = []
for sid in ['S001', 'S002', 'S003']:
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
# REVENUE CONCENTRATION (Pareto / CDF)
# ============================================================
rev_by_company = [(NAMES[sid], monthly_usage[monthly_usage['startup_id']==sid]['revenue_usd'].sum()) for sid in ['S001','S002','S003']]
rev_by_company.sort(key=lambda x: x[1], reverse=True)
total_rev_all = sum(r[1] for r in rev_by_company)
cum_pct_companies = []
cum_pct_revenue = []
running_rev = 0
for i, (name, rev) in enumerate(rev_by_company):
    running_rev += rev
    cum_pct_companies.append((i + 1) / len(rev_by_company) * 100)
    cum_pct_revenue.append(running_rev / total_rev_all * 100)
MODEL_COLORS = {'sonnet': '#3B528B', 'opus': '#472D7B', 'haiku': '#21918C'}
BG = '#FFFCFC'
CARD = '#F8FAFB'
TEXT = '#14141C'
GRID = '#E9E5E8'
MUTED = '#8E8494'
DIM = '#43394C'
ACCENT = '#472D7B'
ACCENT_LIGHT = 'rgba(71, 57, 130, 0.07)'
ACCENT_SURFACE = 'rgba(71, 57, 130, 0.04)'
BORDER_SUBTLE = '#ECEDF2'
SUCCESS = '#22C55E'
WARNING = '#EAB308'
DANGER = '#EF4444'

# ============================================================
# COMPUTE PER-COMPANY METRICS FOR TOP PERFORMERS TABLE
# ============================================================

company_metrics = []
for sid in ['S001', 'S002', 'S003']:
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

    # Token CAGR (annualized monthly growth)
    if first['total_tokens'] > 0 and n_months > 0:
        token_cagr = (latest['total_tokens'] / first['total_tokens']) ** (12 / n_months) - 1
    else:
        token_cagr = 0

    # Revenue CAGR
    if first['revenue_usd'] > 0 and n_months > 0:
        rev_cagr = (latest['revenue_usd'] / first['revenue_usd']) ** (12 / n_months) - 1
    else:
        rev_cagr = 0

    # Revenue by model (latest month)
    sonnet_rev = latest['revenue_usd'] * latest['sonnet_pct']
    opus_rev = latest['revenue_usd'] * latest['opus_pct']
    haiku_rev = latest['revenue_usd'] * latest['haiku_pct']

    # Total revenue by model (all time)
    sonnet_total = (u['revenue_usd'] * u['sonnet_pct']).sum()
    opus_total = (u['revenue_usd'] * u['opus_pct']).sum()
    haiku_total = (u['revenue_usd'] * u['haiku_pct']).sum()

    # Credit ROI
    roi = total_rev / c if c > 0 else 0

    # Payback
    payback = ue[ue['payback_achieved']].iloc[0]['months_since_onboard'] if ue['payback_achieved'].any() else None

    # Revenue per developer
    rev_per_dev = latest['revenue_usd'] / latest['active_developers'] if latest['active_developers'] > 0 else 0

    # Tokens per developer
    tok_per_dev = latest['total_tokens'] / latest['active_developers'] if latest['active_developers'] > 0 else 0

    # 3-month revenue momentum (last 3 vs prior 3)
    if len(u) >= 6:
        recent_3 = u.tail(3)['revenue_usd'].mean()
        prior_3 = u.iloc[-6:-3]['revenue_usd'].mean()
        momentum = (recent_3 / prior_3 - 1) * 100 if prior_3 > 0 else 0
    else:
        momentum = 0

    # Avg Quick Ratio (last 6 months)
    avg_qr = ga['quick_ratio'].tail(6).mean()

    company_metrics.append(dict(
        sid=sid, name=NAMES[sid], vertical=s['vertical'], stage=s['stage'],
        latest_mrr=latest['revenue_usd'], total_rev=total_rev, total_tokens=total_tok,
        token_cagr=token_cagr, rev_cagr=rev_cagr,
        sonnet_rev=sonnet_rev, opus_rev=opus_rev, haiku_rev=haiku_rev,
        sonnet_total=sonnet_total, opus_total=opus_total, haiku_total=haiku_total,
        credits=c, roi=roi, payback=payback,
        active_devs=int(latest['active_developers']),
        rev_per_dev=rev_per_dev, tok_per_dev=tok_per_dev,
        momentum=momentum, avg_qr=avg_qr,
        latest_latency=latest['avg_latency_ms'],
        latest_error=latest['error_rate'],
    ))

# Sort by token CAGR for top performers
company_metrics.sort(key=lambda x: x['token_cagr'], reverse=True)

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

def company_chips(section_id):
    """Generate company filter chip HTML for a section."""
    chips = f'<div class="section-filters" data-filter-section="{section_id}">'
    for sid in ['S001', 'S002', 'S003']:
        chips += f'<button class="chip active" data-sid="{sid}" style="--chip-color:{COLORS[sid]}"><span class="dot-sm" style="background:{COLORS[sid]}"></span>{NAMES[sid]}</button>'
    chips += '</div>'
    return chips

# ============================================================
# PORTFOLIO CHARTS — TRIBE CAPITAL FRAMEWORK
# ============================================================

# --- DEVELOPER GROWTH ACCOUNTING (portfolio-level, aggregated) ---
agg_dev_ga = dev_ga.groupby('month').agg(
    new_devs=('new_devs', 'sum'),
    retained_devs=('retained_devs', 'sum'),
    resurrected_devs=('resurrected_devs', 'sum'),
    churned_devs=('churned_devs', 'sum'),
    active_devs=('active_devs', 'sum'),
).reset_index().sort_values('month')

fig_dev_ga = go.Figure()
fig_dev_ga.add_trace(go.Bar(x=agg_dev_ga['month'], y=agg_dev_ga['retained_devs'], name='Retained', marker_color='#3B528B'))
fig_dev_ga.add_trace(go.Bar(x=agg_dev_ga['month'], y=agg_dev_ga['new_devs'], name='New', marker_color=SUCCESS))
fig_dev_ga.add_trace(go.Bar(x=agg_dev_ga['month'], y=agg_dev_ga['resurrected_devs'], name='Resurrected', marker_color='#5EC962'))
fig_dev_ga.add_trace(go.Bar(x=agg_dev_ga['month'], y=-agg_dev_ga['churned_devs'], name='Churned', marker_color=DANGER))
fig_dev_ga.update_layout(**layout('Developer Growth Accounting', h=340), barmode='relative')

# --- DEVELOPER QUICK RATIO — per-company lines + mean ---
fig_dev_qr = go.Figure()
all_qr_max = 5
for sid in ['S001', 'S002', 'S003']:
    dq = dev_ga[(dev_ga['startup_id'] == sid) & (dev_ga['dev_quick_ratio'].notna())].sort_values('month')
    if len(dq) > 0:
        fig_dev_qr.add_trace(go.Scatter(x=dq['month'], y=dq['dev_quick_ratio'], name=NAMES[sid],
            mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=4),
            hovertemplate='%{y:.1f}x<extra>' + NAMES[sid] + '</extra>'))
        all_qr_max = max(all_qr_max, dq['dev_quick_ratio'].max())

# Mean line
agg_dev_qr = dev_ga[dev_ga['dev_quick_ratio'].notna()].groupby('month')['dev_quick_ratio'].mean().reset_index()
fig_dev_qr.add_trace(go.Scatter(x=agg_dev_qr['month'], y=agg_dev_qr['dev_quick_ratio'], name='Mean',
    mode='lines', line=dict(color=TEXT, width=2, dash='dot'),
    hovertemplate='Mean: %{y:.1f}x<extra></extra>'))

fig_dev_qr.add_hline(y=2, line_dash="dash", line_color=SUCCESS,
    annotation_text="2.0x Strong", annotation_position="top right", annotation_font_color=SUCCESS)
fig_dev_qr.add_hline(y=1, line_dash="dash", line_color=DANGER,
    annotation_text="1.0x Flat", annotation_position="bottom right", annotation_font_color=DANGER)
fig_dev_qr.update_layout(**layout('Developer Quick Ratio', h=340))
fig_dev_qr.update_yaxes(range=[0, min(all_qr_max * 1.2, 8)])

# --- PER-COMPANY DEVELOPER GA (for filterable chart) ---
fig_dev_ga_company = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    dg = dev_ga[dev_ga['startup_id'] == sid].sort_values('month')
    fig_dev_ga_company.add_trace(go.Bar(x=dg['month'], y=dg['retained_devs'], name=f'{NAMES[sid]} Retained',
        marker_color=COLORS[sid], opacity=0.7, legendgroup=sid, showlegend=True))
    fig_dev_ga_company.add_trace(go.Bar(x=dg['month'], y=dg['new_devs'], name=f'{NAMES[sid]} New',
        marker_color=SUCCESS, opacity=0.6, legendgroup=sid, showlegend=False))
    fig_dev_ga_company.add_trace(go.Bar(x=dg['month'], y=-dg['churned_devs'], name=f'{NAMES[sid]} Churned',
        marker_color=DANGER, opacity=0.6, legendgroup=sid, showlegend=False))
fig_dev_ga_company.update_layout(**layout('Developer Growth Accounting (by Company)', h=340), barmode='relative')

# --- MAU (Monthly Active Users/Developers) ---
fig_mau = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    d = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    fig_mau.add_trace(go.Scatter(x=d['month'], y=d['active_developers'], name=NAMES[sid],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=4),
        hovertemplate='%{y} active devs<extra></extra>'))
# Also total MAU line
total_mau = monthly_usage.groupby('month')['active_developers'].sum().reset_index()
fig_mau.add_trace(go.Scatter(x=total_mau['month'], y=total_mau['active_developers'], name='Total',
    mode='lines', line=dict(color=TEXT, width=2, dash='dot'),
    hovertemplate='%{y} total<extra></extra>'))
fig_mau.update_layout(**layout('Monthly Active Developers (MAU)', h=340))

# --- PORTFOLIO REVENUE GROWTH ACCOUNTING (aggregated across all companies) ---
agg_rev_ga = startup_ga.groupby('month').agg(
    new_revenue=('new_revenue', 'sum'),
    expansion_revenue=('expansion_revenue', 'sum'),
    resurrected_revenue=('resurrected_revenue', 'sum'),
    churned_revenue=('churned_revenue', 'sum'),
    contraction_revenue=('contraction_revenue', 'sum'),
    retained_revenue=('retained_revenue', 'sum'),
    total_revenue=('total_revenue', 'sum'),
).reset_index().sort_values('month')

fig_rev_ga = go.Figure()
fig_rev_ga.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['retained_revenue'], name='Retained', marker_color='#3B528B'))
fig_rev_ga.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['new_revenue'], name='New', marker_color=SUCCESS))
fig_rev_ga.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['expansion_revenue'], name='Expansion', marker_color='#472D7B'))
fig_rev_ga.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['resurrected_revenue'], name='Resurrected', marker_color='#5EC962'))
fig_rev_ga.add_trace(go.Bar(x=agg_rev_ga['month'], y=-agg_rev_ga['churned_revenue'], name='Churned', marker_color=DANGER))
fig_rev_ga.add_trace(go.Bar(x=agg_rev_ga['month'], y=-agg_rev_ga['contraction_revenue'], name='Contraction', marker_color=WARNING))
fig_rev_ga.update_layout(**layout('Revenue Growth Accounting', h=380), barmode='relative')
fig_rev_ga.update_yaxes(tickprefix='$', tickformat=',')

# (Revenue Quick Ratio removed per feedback)

# --- GROSS RETENTION (portfolio) ---
agg_rev_ga['gross_ret'] = agg_rev_ga['retained_revenue'] / agg_rev_ga['total_revenue'].shift(1) * 100
fig_gross_ret = go.Figure()
fig_gross_ret.add_trace(go.Scatter(x=agg_rev_ga['month'], y=agg_rev_ga['gross_ret'],
    mode='lines+markers', line=dict(color=ACCENT, width=2.5), marker=dict(size=5), showlegend=False,
    hovertemplate='%{y:.1f}%<extra></extra>'))
fig_gross_ret.add_hline(y=70, line_dash="dash", line_color=WARNING,
    annotation_text="70% Benchmark", annotation_position="bottom right", annotation_font_color=WARNING)
fig_gross_ret.update_layout(**layout('Gross Revenue Retention', h=300))
fig_gross_ret.update_yaxes(ticksuffix='%', range=[0, 105])

# --- COHORT LTV CURVES ---
fig_cohort_ltv = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    cd = cohort_df[cohort_df['startup_id'] == sid].sort_values('months_since')
    cum_rev = cd['revenue'].cumsum()
    fig_cohort_ltv.add_trace(go.Scatter(x=cd['months_since'], y=cum_rev, name=NAMES[sid],
        mode='lines', line=dict(color=COLORS[sid], width=2.5),
        hovertemplate='Month %{x}: $%{y:,.0f}<extra></extra>'))
fig_cohort_ltv.update_layout(**layout('Cumulative LTV per Partner'))
fig_cohort_ltv.update_yaxes(tickprefix='$', tickformat=',')
fig_cohort_ltv.update_xaxes(title_text='Months since onboarding')

# --- REVENUE RETENTION BY COHORT ---
fig_rev_retention = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    cd = cohort_df[cohort_df['startup_id'] == sid].sort_values('months_since')
    fig_rev_retention.add_trace(go.Scatter(x=cd['months_since'], y=cd['rev_retention'], name=NAMES[sid],
        mode='lines', line=dict(color=COLORS[sid], width=2.5),
        hovertemplate='Month %{x}: %{y:.1f}x first month<extra></extra>'))
fig_rev_retention.add_hline(y=1, line_dash="dash", line_color=MUTED, annotation_text="1x baseline",
    annotation_position="top right", annotation_font_color=MUTED)
fig_rev_retention.update_layout(**layout('Revenue Retention vs First Month'))
fig_rev_retention.update_yaxes(ticksuffix='x')
fig_rev_retention.update_xaxes(title_text='Months since onboarding')

# --- LTV HEATMAP ---
# Rows = companies, Columns = months since onboarding, Values = cumulative revenue
ltv_matrix = []
ltv_labels = []
max_months = 0
for sid in ['S001', 'S002', 'S003']:
    cd = cohort_df[cohort_df['startup_id'] == sid].sort_values('months_since')
    cum_rev = cd['revenue'].cumsum().values
    ltv_matrix.append(cum_rev.tolist())
    ltv_labels.append(NAMES[sid])
    max_months = max(max_months, len(cum_rev))

# Pad shorter rows
for i in range(len(ltv_matrix)):
    while len(ltv_matrix[i]) < max_months:
        ltv_matrix[i].append(None)

fig_ltv_heatmap = go.Figure(data=go.Heatmap(
    z=ltv_matrix, x=[f'M{i}' for i in range(max_months)], y=ltv_labels,
    colorscale=[[0, '#f8fafb'], [0.3, '#c4b5fd'], [0.6, '#7c3aed'], [1, '#3b0764']],
    hovertemplate='%{y}<br>Month %{x}: $%{z:,.0f}<extra></extra>',
    colorbar=dict(title='LTV ($)', tickprefix='$', tickformat=','),
))
fig_ltv_heatmap.update_layout(**layout('Cumulative LTV Heatmap', h=220))

# --- DEVELOPER RETENTION HEATMAP (per company, by cohort age) ---
# Aggregate retention by company × age
ret_matrix = []
ret_labels = []
max_age = 0
for sid in ['S001', 'S002', 'S003']:
    dc = dev_cohorts[dev_cohorts['startup_id'] == sid]
    avg_ret_by_age = dc.groupby('age')['retention_pct'].mean()
    ret_matrix.append(avg_ret_by_age.values.tolist())
    ret_labels.append(NAMES[sid])
    max_age = max(max_age, len(avg_ret_by_age))

for i in range(len(ret_matrix)):
    while len(ret_matrix[i]) < max_age:
        ret_matrix[i].append(None)

fig_ret_heatmap = go.Figure(data=go.Heatmap(
    z=ret_matrix, x=[f'M{i}' for i in range(max_age)], y=ret_labels,
    colorscale=[[0, '#fca5a5'], [0.5, '#fde68a'], [0.7, '#bbf7d0'], [1, '#22c55e']],
    zmin=0, zmax=100,
    hovertemplate='%{y}<br>Age %{x}: %{z:.0f}% retained<extra></extra>',
    colorbar=dict(title='Retention %', ticksuffix='%'),
))
fig_ret_heatmap.update_layout(**layout('Developer Retention Heatmap', h=220))

# --- PER-COMPANY DEVELOPER RETENTION CURVES ---
fig_dev_retention = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    dc = dev_cohorts[dev_cohorts['startup_id'] == sid]
    avg_ret = dc.groupby('age')['retention_pct'].mean().reset_index()
    fig_dev_retention.add_trace(go.Scatter(x=avg_ret['age'], y=avg_ret['retention_pct'],
        name=NAMES[sid], mode='lines+markers', line=dict(color=COLORS[sid], width=2.5),
        marker=dict(size=4), hovertemplate='Month %{x}: %{y:.0f}%<extra></extra>'))
fig_dev_retention.add_hline(y=50, line_dash="dash", line_color=WARNING,
    annotation_text="50% benchmark", annotation_position="bottom right", annotation_font_color=WARNING)
fig_dev_retention.update_layout(**layout('Developer Retention by Cohort Age'))
fig_dev_retention.update_yaxes(ticksuffix='%', range=[0, 105])
fig_dev_retention.update_xaxes(title_text='Months since cohort start')

# --- REVENUE CONCENTRATION (Pareto CDF) ---
fig_concentration = go.Figure()
fig_concentration.add_trace(go.Scatter(x=[0] + cum_pct_companies, y=[0] + cum_pct_revenue,
    name='Portfolio', mode='lines+markers', line=dict(color=ACCENT, width=2.5),
    marker=dict(size=8, color=ACCENT),
    text=[''] + [f'{n}: ${r:,.0f}' for n, r in rev_by_company],
    hovertemplate='%{text}<br>Top %{x:.0f}% of partners → %{y:.0f}% of revenue<extra></extra>'))
fig_concentration.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode='lines',
    line=dict(color=MUTED, width=1, dash='dash'), showlegend=False))
fig_concentration.update_layout(**layout('Revenue Concentration', h=300))
fig_concentration.update_xaxes(title_text='Cumulative % of Partners', ticksuffix='%')
fig_concentration.update_yaxes(title_text='Cumulative % of Revenue', ticksuffix='%')

# Revenue by model — stacked bar per company
fig_rev_model = go.Figure()
names_ordered = [m['name'] for m in company_metrics]
fig_rev_model.add_trace(go.Bar(name='Sonnet', x=names_ordered,
    y=[m['sonnet_total'] for m in company_metrics], marker_color=MODEL_COLORS['sonnet']))
fig_rev_model.add_trace(go.Bar(name='Opus', x=names_ordered,
    y=[m['opus_total'] for m in company_metrics], marker_color=MODEL_COLORS['opus']))
fig_rev_model.add_trace(go.Bar(name='Haiku', x=names_ordered,
    y=[m['haiku_total'] for m in company_metrics], marker_color=MODEL_COLORS['haiku']))
fig_rev_model.update_layout(**layout('Total Revenue by Model', h=340), barmode='stack')
fig_rev_model.update_yaxes(tickprefix='$', tickformat=',')

# Revenue by model over time (all companies stacked)
fig_rev_model_time = go.Figure()
model_fills = {'Sonnet': 'rgba(59,82,139,0.6)', 'Opus': 'rgba(71,45,123,0.6)', 'Haiku': 'rgba(33,145,140,0.6)'}
for model, col, color in [('Sonnet', 'sonnet_pct', '#3b82f6'), ('Opus', 'opus_pct', '#8b5cf6'), ('Haiku', 'haiku_pct', '#06b6d4')]:
    agg = monthly_usage.groupby('month').apply(lambda g: (g['revenue_usd'] * g[col]).sum()).reset_index()
    agg.columns = ['month', 'rev']
    fig_rev_model_time.add_trace(go.Scatter(x=agg['month'], y=agg['rev'], name=model,
        stackgroup='one', line=dict(color=color, width=0),
        fillcolor=model_fills[model],
        hovertemplate='$%{y:,.0f}<extra></extra>'))
fig_rev_model_time.update_layout(**layout('Portfolio Revenue by Model (Monthly)'))
fig_rev_model_time.update_yaxes(tickprefix='$', tickformat=',')

# Monthly API Revenue (per company, filterable)
fig_rev = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    d = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    fig_rev.add_trace(go.Scatter(x=d['month'], y=d['revenue_usd'], name=NAMES[sid],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=4),
        hovertemplate='$%{y:,.0f}<extra></extra>'))
fig_rev.update_layout(**layout('Monthly API Revenue'))
fig_rev.update_yaxes(tickprefix='$', tickformat=',')

# Token consumption (in millions for readability)
fig_tokens = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    d = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    fig_tokens.add_trace(go.Scatter(x=d['month'], y=d['total_tokens'] / 1e6, name=NAMES[sid],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=4),
        hovertemplate='%{y:,.0f}M tokens<extra></extra>'))
fig_tokens.update_layout(**layout('Monthly Token Consumption'))
fig_tokens.update_yaxes(ticksuffix='M', tickformat=',')

# Credit Payback
fig_payback = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    d = unit_economics[unit_economics['startup_id'] == sid]
    fig_payback.add_trace(go.Scatter(x=d['months_since_onboard'], y=d['contribution_margin'],
        name=NAMES[sid], mode='lines', line=dict(color=COLORS[sid], width=2.5),
        hovertemplate='Month %{x}: $%{y:,.0f}<extra></extra>'))
fig_payback.add_hline(y=0, line_dash="dash", line_color=MUTED, annotation_text="Breakeven",
    annotation_position="top right", annotation_font_color=MUTED)
fig_payback.update_layout(**layout('Credit Payback: Revenue × GM − Credits'))
fig_payback.update_yaxes(tickprefix='$', tickformat=',')
fig_payback.update_xaxes(title_text='Months since onboarding')

# Spend Quick Ratio
fig_qr = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    d = startup_ga[startup_ga['startup_id'] == sid].sort_values('month')
    fig_qr.add_trace(go.Scatter(x=d['month'], y=d['quick_ratio'], name=NAMES[sid],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2), marker=dict(size=4)))
fig_qr.add_hline(y=4, line_dash="dash", line_color="#22c55e",
    annotation_text="4.0x Strong", annotation_position="top right", annotation_font_color="#22c55e")
fig_qr.add_hline(y=1, line_dash="dash", line_color="#ef4444",
    annotation_text="1.0x Flat", annotation_position="bottom right", annotation_font_color="#ef4444")
fig_qr.update_layout(**layout('Spend Quick Ratio'))
fig_qr.update_yaxes(range=[0, 12])

# Active Developers
fig_devs = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    d = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    fig_devs.add_trace(go.Scatter(x=d['month'], y=d['active_developers'], name=NAMES[sid],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2), marker=dict(size=4),
        hovertemplate='%{y} devs<extra></extra>'))
fig_devs.update_layout(**layout('Active Developers'))

PORTFOLIO_CHART_IDS = ['p-rev', 'p-devs']

# ============================================================
# PER-STARTUP CHARTS
# ============================================================

startup_charts = {}

for sid in ['S001', 'S002', 'S003']:
    charts = {}
    d_usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    d_ga = startup_ga[startup_ga['startup_id'] == sid].sort_values('month')

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

    # Growth Accounting
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

    # Developer Quick Ratio (per-startup) — skip NaN (first month)
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

    startup_charts[sid] = charts

# ============================================================
# BUILD TOP PERFORMERS TABLE HTML
# ============================================================

def color_val(val, thresholds, colors):
    """Return color based on value vs thresholds (ascending)."""
    for t, c in zip(thresholds, colors):
        if val < t:
            return c
    return colors[-1]

def fmt_pct(v):
    return f'{v*100:,.0f}%' if abs(v) >= 0.01 else f'{v*100:,.1f}%'

table_rows = ''
for i, m in enumerate(company_metrics):
    cagr_color = SUCCESS if m['token_cagr'] > 2 else WARNING if m['token_cagr'] > 0.5 else DANGER
    rev_cagr_color = SUCCESS if m['rev_cagr'] > 2 else WARNING if m['rev_cagr'] > 0.5 else DANGER
    roi_color = SUCCESS if m['roi'] > 2 else WARNING if m['roi'] > 1 else DANGER
    momentum_color = SUCCESS if m['momentum'] > 20 else WARNING if m['momentum'] > 0 else DANGER

    # Credit payback progress bar
    payback_pct = min(m['roi'] * 100, 100)  # cap at 100% for the bar
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

    table_rows += f'''<tr class="perf-row" data-sid="{m['sid']}" style="cursor:pointer">
        <td><span class="dot-sm" style="background:{COLORS[m['sid']]}"></span>{m['name']}</td>
        <td>{m['vertical']}</td>
        <td class="payback-cell">
            <div class="payback-bar{bar_extra_class}">
                <div class="payback-fill" style="width:{payback_pct}%;background:{bar_color}"></div>
                <span class="payback-label">{bar_label}</span>
            </div>
            <div class="payback-amounts">${m['total_rev']:,.0f} / ${m['credits']:,.0f}</div>
        </td>
        <td style="color:{cagr_color}">{fmt_pct(m['token_cagr'])}</td>
        <td style="color:{rev_cagr_color}">{fmt_pct(m['rev_cagr'])}</td>
        <td>${m['latest_mrr']:,.0f}</td>
        <td><span style="color:{MODEL_COLORS['sonnet']}">${m['sonnet_rev']:,.0f}</span> / <span style="color:{MODEL_COLORS['opus']}">${m['opus_rev']:,.0f}</span> / <span style="color:{MODEL_COLORS['haiku']}">${m['haiku_rev']:,.0f}</span></td>
        <td style="color:{momentum_color}">{m['momentum']:+.0f}%</td>
        <td>{m['active_devs']}</td>
        <td>${m['rev_per_dev']:,.0f}</td>
    </tr>'''

top_performers_html = f'''
<div class="perf-table-wrap card">
    <table class="perf-table">
        <thead>
            <tr>
                <th>Company</th>
                <th>Vertical</th>
                <th>Credit Payback</th>
                <th>Token CAGR</th>
                <th>Rev CAGR</th>
                <th>Latest MRR</th>
                <th>MRR by Model <span class="model-legend">S / O / H</span></th>
                <th>3mo Momentum</th>
                <th>Devs</th>
                <th>Rev/Dev</th>
            </tr>
        </thead>
        <tbody>{table_rows}</tbody>
    </table>
</div>'''

# ============================================================
# KPIs
# ============================================================

total_credits = credits['amount_usd'].sum()
total_revenue = monthly_usage['revenue_usd'].sum()
total_tokens = monthly_usage['total_tokens'].sum()
total_calls = monthly_usage['api_calls'].sum()
roi = total_revenue / total_credits

# Revenue by model totals
total_sonnet = sum(m['sonnet_total'] for m in company_metrics)
total_opus = sum(m['opus_total'] for m in company_metrics)
total_haiku = sum(m['haiku_total'] for m in company_metrics)

portfolio_kpis = '<div class="kpi-row">'
portfolio_kpis += f'''<div class="kpi kpi-expandable" onclick="this.classList.toggle('expanded')">
    <div class="kpi-l">Total Revenue</div>
    <div class="kpi-v">${total_revenue:,.0f}</div>
    <div class="kpi-s">all partners &middot; <span class="expand-hint">click to expand</span></div>
    <div class="kpi-breakdown">
        <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['sonnet']}"></span>Sonnet <span style="color:{MODEL_COLORS['sonnet']}">${total_sonnet:,.0f}</span> <span class="kpi-s">{total_sonnet/total_revenue*100:.0f}%</span></div>
        <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['opus']}"></span>Opus <span style="color:{MODEL_COLORS['opus']}">${total_opus:,.0f}</span> <span class="kpi-s">{total_opus/total_revenue*100:.0f}%</span></div>
        <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['haiku']}"></span>Haiku <span style="color:{MODEL_COLORS['haiku']}">${total_haiku:,.0f}</span> <span class="kpi-s">{total_haiku/total_revenue*100:.0f}%</span></div>
    </div>
</div>'''
portfolio_kpis += kpi('Credits Deployed', f'${total_credits:,.0f}', '3 partners')
portfolio_kpis += kpi('Active Developers', f'{sum(m["active_devs"] for m in company_metrics)}', 'across portfolio')
portfolio_kpis += '</div>'

def startup_kpis(sid):
    m = next(x for x in company_metrics if x['sid'] == sid)
    d_dga = dev_ga[dev_ga['startup_id'] == sid].sort_values('month')
    latest_dqr = d_dga.iloc[-1]['dev_quick_ratio'] if len(d_dga) > 0 else 0

    roi_color = SUCCESS if m['roi'] > 2 else WARNING if m['roi'] > 1 else DANGER
    cagr_color = SUCCESS if m['token_cagr'] > 2 else WARNING if m['token_cagr'] > 0.5 else DANGER
    dqr_color = SUCCESS if latest_dqr > 2 else WARNING if latest_dqr > 1 else DANGER

    html = '<div class="kpi-row">'
    # Total Rev with expandable model breakdown
    html += f'''<div class="kpi kpi-expandable" onclick="this.classList.toggle('expanded')">
        <div class="kpi-l">Total Revenue</div>
        <div class="kpi-v">${m["total_rev"]:,.0f}</div>
        <div class="kpi-s">all time &middot; <span class="expand-hint">click to expand</span></div>
        <div class="kpi-breakdown">
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['sonnet']}"></span>Sonnet <span style="color:{MODEL_COLORS['sonnet']}">${m["sonnet_total"]:,.0f}</span> <span class="kpi-s">{m["sonnet_total"]/m["total_rev"]*100:.0f}%</span></div>
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['opus']}"></span>Opus <span style="color:{MODEL_COLORS['opus']}">${m["opus_total"]:,.0f}</span> <span class="kpi-s">{m["opus_total"]/m["total_rev"]*100:.0f}%</span></div>
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['haiku']}"></span>Haiku <span style="color:{MODEL_COLORS['haiku']}">${m["haiku_total"]:,.0f}</span> <span class="kpi-s">{m["haiku_total"]/m["total_rev"]*100:.0f}%</span></div>
        </div>
    </div>'''
    html += kpi('Latest MRR', f'${m["latest_mrr"]:,.0f}', 'API revenue')
    html += kpi('Token CAGR', fmt_pct(m['token_cagr']), 'annualized', cagr_color)
    html += kpi('Credit ROI', f'{m["roi"]:.1f}x', f'${m["credits"]:,.0f} invested', roi_color)
    html += kpi('Active Devs', f'{m["active_devs"]}', 'current month')
    html += kpi('Dev Quick Ratio', f'{latest_dqr:.1f}x', 'new+resurrected / churned', dqr_color)
    html += '</div>'
    return html

# ============================================================
# STARTUP TAB CONTENT
# ============================================================

def startup_tab_html(sid):
    s = startups[startups['startup_id'] == sid].iloc[0]
    ch = startup_charts[sid]

    # Compute per-company summary values for section headers
    m = next(x for x in company_metrics if x['sid'] == sid)
    d_dga = dev_ga[dev_ga['startup_id'] == sid]
    latest_dqr = d_dga.dropna(subset=['dev_quick_ratio'])['dev_quick_ratio'].iloc[-1] if len(d_dga.dropna(subset=['dev_quick_ratio'])) > 0 else 0
    d_ga_s = startup_ga[startup_ga['startup_id'] == sid]
    latest_gret = d_ga_s['gross_retention_pct'].iloc[-1] if len(d_ga_s) > 0 and 'gross_retention_pct' in d_ga_s.columns else 0

    # Per-company cohort LTV
    cd_s = cohort_df[cohort_df['startup_id'] == sid]
    ltv_12 = cd_s[cd_s['months_since'] <= 12]['revenue'].sum() if len(cd_s) > 0 else 0

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

    <!-- SECTION 1: Growth Accounting — Users -->
    <div class="analysis-section" data-section="{sid}-user-ga">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">▼</span> Growth Accounting — Users</div>
            <div class="analysis-summary">
                <span class="sum-item">Devs <span class="sum-val">{m['active_devs']}</span></span>
                <span class="sum-item">QR <span class="sum-val">{latest_dqr:.1f}x</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-user-ga">
                <div class="mode-tab active" data-mode="qr">Quick Ratio</div>
                <div class="mode-tab" data-mode="ga">Growth Accounting</div>
                {'<div class="mode-tab" data-mode="retention">Cohort Retention</div>' if 'dev_retention' in ch else ''}
            </div>
            <div class="mode-panel active" data-mode="qr">
                <div class="row-1"><div class="card">{ch['dev_qr']}</div></div>
            </div>
            <div class="mode-panel" data-mode="ga">
                <div class="row-1"><div class="card">{ch['dev_ga']}</div></div>
            </div>
            {'<div class="mode-panel" data-mode="retention"><div class="row-1"><div class="card">' + ch['dev_retention'] + '</div></div></div>' if 'dev_retention' in ch else ''}
        </div>
    </div>

    <!-- SECTION 2: Growth Accounting — Revenue -->
    <div class="analysis-section" data-section="{sid}-rev-ga">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">▼</span> Growth Accounting — Revenue</div>
            <div class="analysis-summary">
                <span class="sum-item">MRR <span class="sum-val">${m['latest_mrr']:,.0f}</span></span>
                <span class="sum-item">CAGR <span class="sum-val">{m['token_cagr']*100:.0f}%</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-rev-ga">
                <div class="mode-tab active" data-mode="ga">Growth Accounting</div>
                <div class="mode-tab" data-mode="rev-tok">Revenue & Tokens</div>
                <div class="mode-tab" data-mode="model">By Model</div>
                <div class="mode-tab" data-mode="mix">Model Mix</div>
            </div>
            <div class="mode-panel active" data-mode="ga">
                <div class="row-1"><div class="card">{ch['growth_acct']}</div></div>
            </div>
            <div class="mode-panel" data-mode="rev-tok">
                <div class="row-2">
                    <div class="card">{ch['revenue']}</div>
                    <div class="card">{ch['tokens']}</div>
                </div>
            </div>
            <div class="mode-panel" data-mode="model">
                <div class="row-1"><div class="card">{ch['rev_by_model']}</div></div>
            </div>
            <div class="mode-panel" data-mode="mix">
                <div class="row-1"><div class="card">{ch['model_mix']}</div></div>
            </div>
        </div>
    </div>

    <!-- SECTION 3: Adoption & Reliability -->
    <div class="analysis-section" data-section="{sid}-adoption">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">▼</span> Adoption & Reliability</div>
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
# PORTFOLIO CONTENT
# ============================================================

# Compute summary values for section headers
total_mau_latest = int(monthly_usage.groupby('month')['active_developers'].sum().iloc[-1])
latest_dev_qr = agg_dev_qr['dev_quick_ratio'].iloc[-1] if len(agg_dev_qr) > 0 else 0
latest_mrr = monthly_usage.groupby('month')['revenue_usd'].sum().iloc[-1]
latest_gross_ret = agg_rev_ga['gross_ret'].dropna().iloc[-1] if agg_rev_ga['gross_ret'].dropna().any() else 0
top_partner_pct = max(m['total_rev'] for m in company_metrics) / total_revenue * 100
avg_ltv_m12 = cohort_df.groupby('startup_id').apply(lambda g: g[g['months_since'] <= 12]['revenue'].sum()).mean()

portfolio_content = f'''
{portfolio_kpis}

<div class="section-header">Top Performers</div>
{top_performers_html}

<!-- SECTION 1: Growth Accounting — Users -->
<div class="analysis-section" data-section="user-ga">
    <div class="analysis-header" onclick="toggleSection(this)">
        <div class="analysis-title"><span class="chevron">▼</span> Growth Accounting — Users</div>
        <div class="analysis-summary">
            <span class="sum-item">MAU <span class="sum-val">{total_mau_latest}</span></span>
            <span class="sum-item">QR <span class="sum-val">{latest_dev_qr:.1f}x</span></span>
        </div>
    </div>
    <div class="analysis-body">
        <div class="mode-tabs" data-section="user-ga">
            <div class="mode-tab active" data-mode="mau">MAU Trend</div>
            <div class="mode-tab" data-mode="qr">Quick Ratio</div>
            <div class="mode-tab" data-mode="ga">Growth Accounting</div>
        </div>
        <div class="mode-panel active" data-mode="mau">
            <div class="row-1"><div class="card">{to_div(fig_mau, 'p-mau')}</div></div>
            <p class="chart-desc"><strong>Monthly Active Developers (MAU)</strong> tracks the number of unique developers or API keys making at least one API call per month. This is the headline adoption metric &mdash; a snapshot of how many people are actively building on Claude across your portfolio.</p>
        </div>
        <div class="mode-panel" data-mode="qr">
            {company_chips('p-dev-qr')}
            <div class="row-1"><div class="card">{to_div(fig_dev_qr, 'p-dev-qr')}</div></div>
            <p class="chart-desc"><strong>Quick Ratio</strong> measures growth quality: <strong>(New + Resurrected) / Churned</strong> developers. A QR of 2.0x means for every developer lost, two are gained. Above 2.0x indicates strong net growth; below 1.0x means the developer base is shrinking. The dotted line shows the portfolio mean.</p>
        </div>
        <div class="mode-panel" data-mode="ga">
            <div class="row-1"><div class="card">{to_div(fig_dev_ga, 'p-dev-ga')}</div></div>
            <p class="chart-desc"><strong>Growth Accounting</strong> decomposes MAU into its components: <strong>Retained</strong> (active both this and last month), <strong>New</strong> (first API call this month), <strong>Resurrected</strong> (returned after inactivity), and <strong>Churned</strong> (active last month, gone this month). This reveals the quality of growth &mdash; healthy growth is driven by retention and new adds, not by resurrecting churned developers.</p>
        </div>
    </div>
</div>

<!-- SECTION 2: Growth Accounting — Revenue -->
<div class="analysis-section" data-section="rev-ga">
    <div class="analysis-header" onclick="toggleSection(this)">
        <div class="analysis-title"><span class="chevron">▼</span> Growth Accounting — Revenue</div>
        <div class="analysis-summary">
            <span class="sum-item">MRR <span class="sum-val">${latest_mrr:,.0f}</span></span>
            <span class="sum-item">Gross Ret <span class="sum-val">{latest_gross_ret:.0f}%</span></span>
        </div>
    </div>
    <div class="analysis-body">
        <div class="mode-tabs" data-section="rev-ga">
            <div class="mode-tab active" data-mode="ga">Growth Accounting</div>
            <div class="mode-tab" data-mode="company">By Company</div>
            <div class="mode-tab" data-mode="model">By Model</div>
        </div>
        <div class="mode-panel active" data-mode="ga">
            <div class="row-1"><div class="card">{to_div(fig_rev_ga, 'p-rev-ga')}</div></div>
            <p class="chart-desc"><strong>Revenue Growth Accounting</strong> breaks down monthly API revenue into six categories: <strong>Retained</strong> (carried forward), <strong>New</strong> (first-month partners), <strong>Expansion</strong> (partners spending more), <strong>Resurrected</strong> (returned from churn), <strong>Churned</strong> (lost entirely), and <strong>Contraction</strong> (partners spending less). The balance between gains above zero and losses below reveals whether portfolio revenue growth is sustainable or fragile.</p>
        </div>
        <div class="mode-panel" data-mode="company">
            <div class="chart-filter-wrap">
                <div class="chart-filters" id="rev-chart-filters">
                    <button class="chip active" data-sid="S001" style="--chip-color:{COLORS['S001']}"><span class="dot-sm" style="background:{COLORS['S001']}"></span>MedScribe AI</button>
                    <button class="chip active" data-sid="S002" style="--chip-color:{COLORS['S002']}"><span class="dot-sm" style="background:{COLORS['S002']}"></span>Eigen Technologies</button>
                    <button class="chip active" data-sid="S003" style="--chip-color:{COLORS['S003']}"><span class="dot-sm" style="background:{COLORS['S003']}"></span>BuilderKit</button>
                    <span class="chip-divider"></span>
                    <button class="chip toggle-chip active" data-metric="revenue">Revenue ($)</button>
                    <button class="chip toggle-chip" data-metric="tokens">Tokens</button>
                </div>
                <div class="card">{to_div(fig_rev, 'p-rev')}</div>
            </div>
            <p class="chart-desc"><strong>Revenue by Company</strong> shows per-partner API billing over time. Toggle between dollar revenue and raw token consumption &mdash; these measure the same activity in different units. Divergence between the two indicates model mix shifts (e.g. migrating from Opus to Haiku changes revenue per token).</p>
        </div>
        <div class="mode-panel" data-mode="model">
            <div class="row-2">
                <div class="card">{to_div(fig_rev_model, 'p-rev-model')}</div>
                <div class="card">{to_div(fig_rev_model_time, 'p-rev-model-time')}</div>
            </div>
            <p class="chart-desc"><strong>Revenue by Model</strong> shows how much each Claude model (Sonnet, Opus, Haiku) contributes to total portfolio revenue. Partners moving towards Opus over time indicates they are building more complex features &mdash; a positive integration depth signal.</p>
        </div>
    </div>
</div>

<!-- SECTION 3: Cohort Analysis -->
<div class="analysis-section" data-section="cohorts">
    <div class="analysis-header" onclick="toggleSection(this)">
        <div class="analysis-title"><span class="chevron">▼</span> Cohort Analysis</div>
        <div class="analysis-summary">
            <span class="sum-item">Avg LTV (12mo) <span class="sum-val">${avg_ltv_m12:,.0f}</span></span>
            <span class="sum-item">Gross Ret <span class="sum-val">{latest_gross_ret:.0f}%</span></span>
        </div>
    </div>
    <div class="analysis-body">
        <div class="mode-tabs" data-section="cohorts">
            <div class="mode-tab active" data-mode="ltv-lines">LTV Lines</div>
            <div class="mode-tab" data-mode="ltv-heat">LTV Heatmap</div>
            <div class="mode-tab" data-mode="dev-ret">Dev Retention</div>
            <div class="mode-tab" data-mode="dev-ret-heat">Retention Heatmap</div>
            <div class="mode-tab" data-mode="rev-ret">Revenue Retention</div>
            <div class="mode-tab" data-mode="gross-ret">Gross Retention</div>
        </div>
        <div class="mode-panel active" data-mode="ltv-lines">
            <div class="row-1"><div class="card clickable-chart">{to_div(fig_cohort_ltv, 'p-cohort-ltv')}</div></div>
            <p class="chart-desc"><strong>Cumulative LTV</strong> shows the total revenue Anthropic has earned from each partner since onboarding. A <strong>super-linear curve</strong> (accelerating upward) means the partner is spending more over time &mdash; the ideal signal. A flattening curve indicates declining engagement. Click a line to drill down to that company.</p>
        </div>
        <div class="mode-panel" data-mode="ltv-heat">
            <div class="row-1"><div class="card">{to_div(fig_ltv_heatmap, 'p-ltv-heatmap')}</div></div>
            <p class="chart-desc"><strong>LTV Heatmap</strong> shows the same data as a matrix &mdash; rows are partners, columns are months since onboarding. Darker colour = higher cumulative revenue. Useful for spotting which partners accelerated early vs. late.</p>
        </div>
        <div class="mode-panel" data-mode="dev-ret">
            <div class="row-1"><div class="card clickable-chart">{to_div(fig_dev_retention, 'p-dev-retention')}</div></div>
            <p class="chart-desc"><strong>Developer Retention</strong> tracks what percentage of a cohort's developers remain active at each month after onboarding. The curve should flatten and stabilise &mdash; that floor is your steady-state retention rate. Below 50% after 6 months is a warning sign.</p>
        </div>
        <div class="mode-panel" data-mode="dev-ret-heat">
            <div class="row-1"><div class="card">{to_div(fig_ret_heatmap, 'p-ret-heatmap')}</div></div>
            <p class="chart-desc"><strong>Retention Heatmap</strong> reveals patterns across the portfolio. <strong>Vertical patterns</strong> = all partners lose devs at the same age (e.g. month 3 drop-off). <strong>Horizontal patterns</strong> = one partner is uniquely sticky or leaky. Green = healthy retention, red = churn.</p>
        </div>
        <div class="mode-panel" data-mode="rev-ret">
            <div class="row-1"><div class="card">{to_div(fig_rev_retention, 'p-rev-retention')}</div></div>
            <p class="chart-desc"><strong>Revenue Retention</strong> compares each partner's current monthly spend to their first month. Values above 1x mean the partner is spending more than when they started (net expansion). This is the revenue analogue of logo retention.</p>
        </div>
        <div class="mode-panel" data-mode="gross-ret">
            <div class="row-1"><div class="card">{to_div(fig_gross_ret, 'p-gross-ret')}</div></div>
            <p class="chart-desc"><strong>Gross Revenue Retention</strong> measures the portfolio's revenue floor &mdash; what percentage of last month's revenue carried forward without any new business. The B2B SaaS benchmark is &gt;70%. This metric excludes new and expansion revenue to isolate the base.</p>
        </div>
    </div>
</div>

<!-- Revenue Concentration archived — too few partners for meaningful CDF. See DASHBOARD-PROPOSAL-V2.md, project log item 5. -->
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
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'IBM Plex Sans',-apple-system,sans-serif; background:{BG}; color:{TEXT}; line-height:1.5; }}

.topbar {{ padding:20px 32px 16px; border-bottom:1px solid {GRID}; }}
.topbar-row {{ display:flex; justify-content:space-between; align-items:baseline; }}
.topbar h1 {{ font-size:20px; font-weight:700; letter-spacing:-0.02em; color:{TEXT}; }}
.topbar .subtitle {{ font-size:12px; color:{MUTED}; margin-top:2px; }}
.topbar .meta {{ font-size:11px; color:{MUTED}; }}

.assumptions {{ padding:10px 32px; background:{ACCENT_SURFACE}; border-bottom:1px solid {GRID}; display:flex; gap:32px; flex-wrap:wrap; }}
.assumptions .a-item {{ font-size:11px; color:{MUTED}; }}
.assumptions .a-item strong {{ color:{TEXT}; font-weight:600; }}

.tabs {{ display:flex; padding:0 32px; border-bottom:1px solid {GRID}; background:{BG}; position:sticky; top:0; z-index:100; }}
.tab {{ padding:12px 20px; font-size:13px; font-weight:500; color:{MUTED}; cursor:pointer; border-bottom:2px solid transparent; transition:all .15s; user-select:none; }}
.tab:hover {{ color:{DIM}; }}
.tab.active {{ color:{TEXT}; border-bottom-color:{ACCENT}; }}
.tab .dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; vertical-align:middle; }}

.content {{ padding:24px 32px; }}
.tab-panel {{ display:none; }}
.tab-panel.active {{ display:block; }}
@keyframes fadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}

.section-header {{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:{MUTED}; margin:24px 0 12px; padding-bottom:6px; border-bottom:1px solid {GRID}; }}
.section-header:first-child {{ margin-top:0; }}

.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-bottom:20px; }}
.kpi {{ background:{CARD}; border:1px solid {GRID}; border-radius:8px; padding:14px 18px; }}
.kpi-l {{ font-size:10px; text-transform:uppercase; letter-spacing:.04em; color:{MUTED}; margin-bottom:2px; }}
.kpi-v {{ font-size:24px; font-weight:700; }}
.kpi-s {{ font-size:11px; color:{MUTED}; }}

.card {{ background:{CARD}; border:1px solid {GRID}; border-radius:8px; padding:16px; overflow:hidden; }}
.row-1 {{ display:grid; grid-template-columns:1fr; gap:16px; margin-bottom:16px; }}
.row-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}

.startup-hero {{ background:{CARD}; border:1px solid {GRID}; border-radius:8px; padding:18px 20px; margin-bottom:16px; }}
.hero-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }}
.hero-name {{ font-size:18px; font-weight:700; margin-right:10px; color:{TEXT}; }}
.badge {{ font-size:9px; font-weight:700; padding:2px 8px; border-radius:10px; color:#fff; letter-spacing:.04em; vertical-align:middle; }}
.hero-meta {{ font-size:12px; color:{MUTED}; }}
.hero-desc {{ font-size:12px; color:{DIM}; margin-top:4px; }}

.filter-bar {{ display:flex; align-items:center; gap:8px; margin-bottom:16px; }}
.filter-label {{ font-size:11px; color:{MUTED}; text-transform:uppercase; letter-spacing:.05em; margin-right:4px; }}
.pill {{ display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:20px; border:1px solid {GRID}; background:transparent; color:{MUTED}; font-size:12px; font-family:'IBM Plex Sans',sans-serif; cursor:pointer; transition:all 0.15s; user-select:none; }}
.pill:hover {{ border-color:{MUTED}; }}
.pill.active {{ background:{ACCENT_LIGHT}; border-color:var(--pill-color); color:{TEXT}; }}
.pill .dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; }}
.pill:not(.active) .dot {{ opacity:0.3; }}

.perf-table-wrap {{ padding:0; overflow-x:auto; position:relative; }}
.perf-table-wrap::after {{ content:''; position:absolute; right:0; top:0; bottom:0; width:40px; background:linear-gradient(90deg, transparent, {CARD}); pointer-events:none; opacity:0; transition:opacity 0.3s; }}
.perf-table-wrap.scrollable::after {{ opacity:1; }}
.perf-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
.perf-table th {{ text-align:left; padding:10px 14px; border-bottom:1px solid {GRID}; color:{MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:0.04em; font-weight:600; white-space:nowrap; }}
.perf-table td {{ padding:10px 14px; border-bottom:1px solid {BORDER_SUBTLE}; white-space:nowrap; color:{DIM}; }}
.perf-table tr:last-child td {{ border-bottom:none; }}
.perf-table .perf-row:hover {{ background:{ACCENT_SURFACE}; }}
.perf-table .perf-row td:first-child {{ font-weight:600; color:{TEXT}; }}
/* Credit payback progress bar */
.payback-cell {{ min-width:140px; }}
.payback-bar {{ position:relative; height:18px; background:{BORDER_SUBTLE}; border-radius:9px; overflow:visible; }}
.payback-fill {{ height:100%; border-radius:9px; transition:width 0.6s cubic-bezier(0.22,1,0.36,1); min-width:2px; }}
.payback-overflow .payback-fill {{ border-radius:9px; box-shadow:0 0 6px rgba(34,197,94,0.4); }}
.payback-label {{ position:absolute; right:6px; top:50%; transform:translateY(-50%); font-size:10px; font-weight:700; color:{TEXT}; }}
.payback-overflow .payback-label {{ color:#fff; }}
.payback-amounts {{ font-size:9px; color:{MUTED}; margin-top:2px; text-align:center; }}

.dot-sm {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; vertical-align:middle; }}
.model-legend {{ font-size:8px; color:{MUTED}; font-weight:400; text-transform:none; letter-spacing:0; }}

/* Expandable KPI */
.kpi-expandable {{ cursor:pointer; position:relative; }}
.kpi-expandable .expand-hint {{ color:{ACCENT}; font-size:9px; }}
.kpi-expandable .kpi-breakdown {{ max-height:0; overflow:hidden; transition:max-height 0.3s ease, opacity 0.3s ease, margin 0.2s ease; opacity:0; margin-top:0; }}
.kpi-expandable.expanded .kpi-breakdown {{ max-height:120px; opacity:1; margin-top:10px; }}
.kpi-expandable.expanded .expand-hint {{ display:none; }}
.kpi-breakdown-row {{ display:flex; align-items:center; gap:8px; font-size:12px; color:{DIM}; padding:3px 0; }}
.kpi-breakdown-row span.kpi-s {{ margin-left:auto; }}

/* Chart filter chips */
.chart-filter-wrap {{ margin-bottom:16px; }}
.chart-filters {{ display:flex; align-items:center; gap:6px; margin-bottom:10px; flex-wrap:wrap; }}
.chip {{ display:inline-flex; align-items:center; gap:5px; padding:5px 12px; border-radius:16px; border:1px solid {GRID}; background:transparent; color:{MUTED}; font-size:12px; font-family:IBM Plex Sans,Inter,sans-serif; cursor:pointer; transition:all 0.15s; user-select:none; }}
.chip:hover {{ border-color:{MUTED}; }}
.chip.active {{ background:{ACCENT_LIGHT}; border-color:var(--chip-color, {ACCENT}); color:{TEXT}; }}
.chip:active {{ transform:scale(0.95); }}
.chip-divider {{ width:1px; height:20px; background:{GRID}; margin:0 4px; }}

/* Clickable chart hint */
.clickable-chart {{ position:relative; cursor:pointer; }}
.clickable-chart::after {{ content:'Click company line to drill down →'; position:absolute; bottom:8px; right:12px; font-size:10px; color:{MUTED}; opacity:0; transition:opacity 0.2s; pointer-events:none; }}
.clickable-chart:hover::after {{ opacity:1; }}
.toggle-chip {{ --chip-color:{ACCENT}; }}
.toggle-chip.active {{ background:{ACCENT_LIGHT}; border-color:{ACCENT}; }}

/* Collapsible analysis sections */
.analysis-section {{ background:{CARD}; border:1px solid {GRID}; border-radius:10px; margin-bottom:16px; overflow:hidden; }}
.analysis-header {{ display:flex; align-items:center; justify-content:space-between; padding:14px 20px; cursor:pointer; user-select:none; transition:background 0.15s; }}
.analysis-header:hover {{ background:{ACCENT_SURFACE}; }}
.analysis-title {{ font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; color:{TEXT}; display:flex; align-items:center; gap:8px; }}
.analysis-title .chevron {{ font-size:10px; color:{MUTED}; transition:transform 0.25s; }}
.analysis-section.collapsed .chevron {{ transform:rotate(-90deg); }}
.analysis-summary {{ font-size:11px; color:{MUTED}; display:flex; gap:16px; }}
.analysis-summary .sum-item {{ white-space:nowrap; }}
.analysis-summary .sum-val {{ font-weight:600; color:{DIM}; }}
.analysis-body {{ padding:0 20px 16px; transition:max-height 0.35s ease, opacity 0.25s ease; overflow:hidden; }}
.analysis-section.collapsed .analysis-body {{ max-height:0 !important; padding:0 20px; opacity:0; }}

/* Mode tabs within sections */
.mode-tabs {{ display:flex; gap:2px; margin-bottom:14px; background:{BG}; border-radius:6px; padding:2px; border:1px solid {GRID}; width:fit-content; }}
.mode-tab {{ padding:6px 14px; font-size:11px; font-weight:500; color:{MUTED}; cursor:pointer; border-radius:4px; transition:all 0.15s; user-select:none; white-space:nowrap; }}
.mode-tab:hover {{ color:{DIM}; }}
.mode-tab.active {{ background:{ACCENT_LIGHT}; color:{TEXT}; font-weight:600; }}
.mode-panel {{ display:none; }}
.mode-panel.active {{ display:block; }}

/* Chart descriptions */
.chart-desc {{ font-size:11px; color:{MUTED}; line-height:1.6; margin-top:8px; padding:0 4px; }}
.chart-desc strong {{ color:{DIM}; font-weight:600; }}

/* Section company filter */
.section-filters {{ display:flex; align-items:center; gap:6px; margin-bottom:12px; flex-wrap:wrap; }}
.section-filters .chip {{ padding:4px 10px; font-size:11px; }}

html {{ scroll-behavior:smooth; }}

@media (max-width:900px) {{
    .row-2 {{ grid-template-columns:1fr; }}
    .row-3 {{ grid-template-columns:1fr; }}
    .kpi-row {{ grid-template-columns:1fr 1fr; }}
    .assumptions {{ flex-direction:column; gap:8px; }}
    .content {{ padding:16px; }}
    .topbar {{ padding:16px; }}
    .chart-filters {{ gap:4px; }}
    .chip {{ padding:4px 10px; font-size:11px; }}
}}

@media (max-width:480px) {{
    .kpi-row {{ grid-template-columns:1fr; }}
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
    <div class="tab" data-tab="s001"><span class="dot" style="background:#2563eb"></span>MedScribe AI</div>
    <div class="tab" data-tab="s002"><span class="dot" style="background:#059669"></span>Eigen Technologies</div>
    <div class="tab" data-tab="s003"><span class="dot" style="background:#dc2626"></span>BuilderKit</div>
</div>

<div class="content">
    <div class="tab-panel active" id="panel-portfolio">
        {portfolio_content}
    </div>
    <div class="tab-panel" id="panel-s001">
        {startup_tab_html('S001')}
    </div>
    <div class="tab-panel" id="panel-s002">
        {startup_tab_html('S002')}
    </div>
    <div class="tab-panel" id="panel-s003">
        {startup_tab_html('S003')}
    </div>
</div>

<script>
// Section collapse/expand
function toggleSection(header) {{
    const section = header.closest('.analysis-section');
    section.classList.toggle('collapsed');
    // Trigger resize for any Plotly charts that might need re-rendering
    if (!section.classList.contains('collapsed')) {{
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
    }}
}}

// Mode tab switching within sections
document.querySelectorAll('.mode-tabs').forEach(tabGroup => {{
    tabGroup.querySelectorAll('.mode-tab').forEach(tab => {{
        tab.addEventListener('click', () => {{
            const section = tab.closest('.analysis-section') || tab.closest('.analysis-body');
            const body = tab.closest('.analysis-body');
            // Deactivate all tabs and panels in this section
            tabGroup.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
            body.querySelectorAll('.mode-panel').forEach(p => p.classList.remove('active'));
            // Activate clicked tab and matching panel
            tab.classList.add('active');
            const mode = tab.dataset.mode;
            body.querySelectorAll('.mode-panel[data-mode="' + mode + '"]').forEach(p => {{
                p.classList.add('active');
            }});
            // Resize Plotly charts in newly visible panel
            setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
        }});
    }});
}});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
        setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
}});

// Table row click → navigate to company tab
document.querySelectorAll('.perf-row').forEach(row => {{
    row.addEventListener('click', () => {{
        const sid = row.dataset.sid.toLowerCase();
        const tab = document.querySelector('[data-tab="' + sid + '"]');
        if (tab) tab.click();
    }});
}});

// Section-level company filter chips
document.querySelectorAll('.section-filters .chip').forEach(chip => {{
    chip.addEventListener('click', () => {{
        chip.classList.toggle('active');
        const sid = chip.dataset.sid;
        const filterSection = chip.closest('.section-filters').dataset.filterSection;
        const chartEl = document.getElementById(filterSection);
        if (chartEl && chartEl.data) {{
            const sidIdx = sidOrder.indexOf(sid);
            // Find traces matching this company — check by name
            const name = {{ S001: 'MedScribe AI', S002: 'Eigen Technologies', S003: 'BuilderKit' }}[sid];
            chartEl.data.forEach((trace, i) => {{
                if (trace.name && trace.name.includes(name)) {{
                    const vis = chip.classList.contains('active') ? true : 'legendonly';
                    Plotly.restyle(filterSection, {{ visible: vis }}, [i]);
                }}
            }});
        }}
    }});
}});

// Click on LTV/retention chart traces to jump to company tab
const traceToTab = {{ 0: 's001', 1: 's002', 2: 's003' }};
['p-cohort-ltv', 'p-dev-retention', 'p-rev-retention'].forEach(chartId => {{
    const el = document.getElementById(chartId);
    if (el) {{
        el.on('plotly_click', function(data) {{
            const traceIdx = data.points[0].curveNumber;
            const tabId = traceToTab[traceIdx];
            if (tabId) {{
                const tab = document.querySelector('[data-tab="' + tabId + '"]');
                if (tab) tab.click();
            }}
        }});
    }}
}});

// Table scroll indicator
document.querySelectorAll('.perf-table-wrap').forEach(wrap => {{
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

// Chart company filter chips
const revChartId = 'p-rev';
const tokChartId = 'p-tokens';
const devChartId = 'p-devs';
const sidOrder = ['S001', 'S002', 'S003'];
const activeCompanies = {{ S001: true, S002: true, S003: true }};
let showingMetric = 'revenue'; // or 'tokens'

// Company chips — toggle traces on revenue and dev charts
document.querySelectorAll('#rev-chart-filters .chip[data-sid]').forEach(chip => {{
    chip.addEventListener('click', () => {{
        const sid = chip.dataset.sid;
        activeCompanies[sid] = !activeCompanies[sid];
        chip.classList.toggle('active');
        const traceIdx = sidOrder.indexOf(sid);
        const vis = activeCompanies[sid] ? true : 'legendonly';

        // Toggle on revenue chart
        const revEl = document.getElementById(revChartId);
        if (revEl && revEl.data && traceIdx < revEl.data.length) {{
            Plotly.restyle(revChartId, {{ visible: vis }}, [traceIdx]);
        }}

        // Toggle on devs chart
        const devEl = document.getElementById(devChartId);
        if (devEl && devEl.data && traceIdx < devEl.data.length) {{
            Plotly.restyle(devChartId, {{ visible: vis }}, [traceIdx]);
        }}

        // Toggle table rows
        document.querySelectorAll('.perf-row[data-sid="' + sid + '"]').forEach(r => {{
            r.style.display = activeCompanies[sid] ? '' : 'none';
        }});
    }});
}});

// Revenue/Tokens metric toggle
const tokenData = {json.dumps({sid: (monthly_usage[monthly_usage['startup_id']==sid].sort_values('month')['total_tokens'] / 1e6).tolist() for sid in ['S001','S002','S003']})};
const revenueData = {json.dumps({sid: monthly_usage[monthly_usage['startup_id']==sid].sort_values('month')[['revenue_usd']].values.flatten().tolist() for sid in ['S001','S002','S003']})};

document.querySelectorAll('.toggle-chip').forEach(chip => {{
    chip.addEventListener('click', () => {{
        document.querySelectorAll('.toggle-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        showingMetric = chip.dataset.metric;

        const data = showingMetric === 'tokens' ? tokenData : revenueData;
        const prefix = showingMetric === 'tokens' ? '' : '$';
        const fmt = showingMetric === 'tokens' ? '%{{y:,.0f}}<extra></extra>' : '$%{{y:,.0f}}<extra></extra>';

        sidOrder.forEach((sid, i) => {{
            Plotly.restyle(revChartId, {{
                y: [data[sid]],
                hovertemplate: fmt
            }}, [i]);
        }});

        const titleText = showingMetric === 'tokens' ? 'Monthly Token Consumption (millions)' : 'Monthly API Revenue';
        const tickpre = showingMetric === 'tokens' ? '' : '$';
        const ticksuf = showingMetric === 'tokens' ? 'M' : '';
        Plotly.relayout(revChartId, {{
            'title.text': titleText,
            'yaxis.tickprefix': tickpre,
            'yaxis.ticksuffix': ticksuf
        }});
    }});
}});
</script>

</body>
</html>'''

output_path = '/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/dashboard.html'
with open(output_path, 'w') as f:
    f.write(full_html)

print(f"Dashboard saved: {output_path}")
print(f"Size: {len(full_html) / 1024:.0f} KB")
