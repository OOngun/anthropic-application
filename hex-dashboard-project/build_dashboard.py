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

COLORS = {'S001': '#472D7B', 'S002': '#3B528B', 'S003': '#21918C'}
NAMES = {'S001': 'MedScribe AI', 'S002': 'Eigen Technologies', 'S003': 'BuilderKit'}

# ============================================================
# COMPUTE DEVELOPER GROWTH ACCOUNTING (synthetic decomposition)
# ============================================================

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
for sid in ['S001', 'S002', 'S003']:
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
# DESIGN TOKENS
# ============================================================

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

# Tier 1 color tokens
GAIN = '#1D9E75'
LOSS = '#D85A30'
CMGR_BLUE = '#3B6BE0'

# ============================================================
# COMPUTE PER-COMPANY METRICS
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

    avg_qr = ga['quick_ratio'].tail(6).mean()

    # Latest gross retention for this company
    latest_gross_ret = ga['gross_retention_pct'].iloc[-1] if len(ga) > 0 and 'gross_retention_pct' in ga.columns else 0

    # Days since last active (simulate: latest month data is "current")
    last_active_days = np.random.choice([2, 5, 10, 18, 3])  # synthetic

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
        gross_retention=latest_gross_ret,
        last_active_days=last_active_days,
    ))

# Set deterministic last_active_days
company_metrics[0]['last_active_days'] = 2   # MedScribe: very active
company_metrics[1]['last_active_days'] = 5   # Eigen: active
company_metrics[2]['last_active_days'] = 11  # BuilderKit: somewhat dormant

company_metrics.sort(key=lambda x: x['token_cagr'], reverse=True)

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

# Aggregate revenue GA
agg_rev_ga = startup_ga.groupby('month').agg(
    new_revenue=('new_revenue', 'sum'),
    expansion_revenue=('expansion_revenue', 'sum'),
    resurrected_revenue=('resurrected_revenue', 'sum'),
    churned_revenue=('churned_revenue', 'sum'),
    contraction_revenue=('contraction_revenue', 'sum'),
    retained_revenue=('retained_revenue', 'sum'),
    total_revenue=('total_revenue', 'sum'),
).reset_index().sort_values('month')

agg_rev_ga['gross_ret'] = agg_rev_ga['retained_revenue'] / agg_rev_ga['total_revenue'].shift(1) * 100

# Latest month GA percentages (for waterfall bars)
latest_ga = agg_rev_ga.iloc[-1]
prior_total = agg_rev_ga.iloc[-2]['total_revenue'] if len(agg_rev_ga) >= 2 else 1

wf_new_pct = latest_ga['new_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_expansion_pct = latest_ga['expansion_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_resurrected_pct = latest_ga['resurrected_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_contraction_pct = latest_ga['contraction_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_churned_pct = latest_ga['churned_revenue'] / prior_total * 100 if prior_total > 0 else 0
wf_net_pct = (latest_ga['total_revenue'] - prior_total) / prior_total * 100 if prior_total > 0 else 0

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

    # Cohort LTV for this company
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

def wf_bar(label, pct, color, is_loss=False):
    width = abs(pct) / wf_max * 100
    sign = '-' if is_loss else '+'
    return f'''<div class="waterfall-row">
        <span class="wf-label">{label}</span>
        <div class="waterfall-bar">
            <div class="wf-track"><div class="wf-fill" style="width:{width:.1f}%;background:{color}"></div></div>
        </div>
        <span class="wf-value" style="color:{color}">{sign}{abs(pct):.1f}%</span>
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
    c3 = cmgr(sub, 3) if len(sub) > 3 else None
    c6 = cmgr(sub, 6) if len(sub) > 6 else None
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
            mode='lines', line=dict(color=color, width=2.5, dash=dash),
            yaxis='y2', visible='legendonly',
            hovertemplate=f'{name}: %{{y:.1f}}%<extra></extra>'))

ga_cmgr_layout = layout('Growth Accounting + CMGR', h=380)
ga_cmgr_layout['barmode'] = 'relative'
ga_cmgr_layout['yaxis']['tickprefix'] = '$'
ga_cmgr_layout['yaxis']['tickformat'] = ','
ga_cmgr_layout['yaxis']['title'] = 'Revenue'
ga_cmgr_layout['yaxis2'] = dict(
    overlaying='y', side='right', showgrid=False, zeroline=False,
    title='CMGR %', ticksuffix='%',
    titlefont=dict(color='#3B6BE0', size=11),
    tickfont=dict(color='#3B6BE0', size=10))
ga_cmgr_layout['legend'] = dict(
    bgcolor='rgba(0,0,0,0)', orientation='h', yanchor='bottom', y=1.02,
    xanchor='left', x=0, font=dict(size=10))
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
        <div class="pulse-card">
            <div class="pc-label">ACTIVE PARTNERS</div>
            <div class="pc-value">{active_partners}</div>
            <div class="pc-sub">API activity in last 30d</div>
        </div>
        <div class="pulse-card">
            <div class="pc-label">QUICK RATIO</div>
            <div class="pc-value">{portfolio_qr:.1f}x</div>
            <div class="pc-sub">(new+res+exp) / (churn+contr)</div>
        </div>
        <div class="pulse-card">
            <div class="pc-label">NET API CHURN</div>
            <div class="pc-value">{net_churn_display}</div>
            <div class="pc-sub">{net_churn_note}</div>
        </div>
        <div class="pulse-card">
            <div class="pc-label">GROSS RETENTION</div>
            <div class="pc-value">{latest_gross_ret:.0f}%</div>
            <div class="pc-sub">30-day rolling</div>
        </div>
    </div>

    <div class="pulse-panels">
        <div class="pulse-panel">
            <div class="panel-title">GROWTH ACCOUNTING WATERFALL</div>
            <div class="panel-subtitle">Latest month vs prior month revenue</div>
            <div class="waterfall-rows">
                {wf_bar('New', wf_new_pct, GAIN)}
                {wf_bar('Expansion', wf_expansion_pct, GAIN)}
                {wf_bar('Resurrected', wf_resurrected_pct, GAIN)}
                <div class="wf-divider"></div>
                {wf_bar('Contraction', wf_contraction_pct, LOSS, True)}
                {wf_bar('Churned', wf_churned_pct, LOSS, True)}
                <div class="wf-divider"></div>
                <div class="waterfall-row wf-net">
                    <span class="wf-label">Net Growth</span>
                    <div class="waterfall-bar">
                        <div class="wf-track"><div class="wf-fill" style="width:{abs(wf_net_pct)/wf_max*100:.1f}%;background:{GAIN if wf_net_pct >= 0 else LOSS}"></div></div>
                    </div>
                    <span class="wf-value" style="font-weight:600">{'+' if wf_net_pct >= 0 else ''}{wf_net_pct:.1f}%</span>
                </div>
            </div>
            <div class="wf-legend">
                <span class="wf-legend-item"><span class="wf-dot" style="background:{GAIN}"></span>Gains</span>
                <span class="wf-legend-item"><span class="wf-dot" style="background:{LOSS}"></span>Losses</span>
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

    cagr_cls = metric_class(m['token_cagr'], (2.0, 0.5))
    qr_cls = metric_class(m['avg_qr'], (2.0, 1.0))
    gret_cls = metric_class(m['gross_retention'], (80, 60))
    last_cls = metric_class(m['last_active_days'], (7, 14), invert=True)

    # Last active display
    la = m['last_active_days']
    la_display = f'{la}d ago' if la > 0 else 'Today'

    partner_rows += f'''<tr class="perf-row" data-sid="{m['sid']}" style="cursor:pointer">
        <td><span class="dot-sm" style="background:{COLORS[m['sid']]}"></span>{m['name']} <span class="stage-badge">{m['stage']}</span></td>
        <td class="payback-cell">
            <div class="payback-bar{bar_extra_class}">
                <div class="payback-fill" style="width:{payback_pct}%;background:{bar_color}"></div>
                <span class="payback-label">{bar_label}</span>
            </div>
        </td>
        <td class="metric-cell {cagr_cls}">{fmt_pct(m['token_cagr'])}</td>
        <td class="metric-cell {qr_cls}">{m['avg_qr']:.1f}x</td>
        <td class="metric-cell {gret_cls}">{m['gross_retention']:.0f}%</td>
        <td class="metric-cell {last_cls}">{la_display}</td>
    </tr>'''

tier2_html = f'''
<div class="partner-list-section">
    <div class="pl-header">
        <div class="pl-title">PARTNER LIST</div>
        <div class="pl-subtitle">Click a partner to view full analysis</div>
    </div>
    <div class="partner-list card">
        <table class="perf-table">
            <thead>
                <tr>
                    <th>Company</th>
                    <th>Credit Payback</th>
                    <th>Token CAGR</th>
                    <th>Quick Ratio</th>
                    <th>Gross Retention</th>
                    <th>Last Active</th>
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
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['sonnet']}"></span>Sonnet <span style="color:{MODEL_COLORS['sonnet']}">${m["sonnet_total"]:,.0f}</span> <span class="kpi-s">{m["sonnet_total"]/m["total_rev"]*100:.0f}%</span></div>
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['opus']}"></span>Opus <span style="color:{MODEL_COLORS['opus']}">${m["opus_total"]:,.0f}</span> <span class="kpi-s">{m["opus_total"]/m["total_rev"]*100:.0f}%</span></div>
            <div class="kpi-breakdown-row"><span class="dot-sm" style="background:{MODEL_COLORS['haiku']}"></span>Haiku <span style="color:{MODEL_COLORS['haiku']}">${m["haiku_total"]:,.0f}</span> <span class="kpi-s">{m["haiku_total"]/m["total_rev"]*100:.0f}%</span></div>
        </div>
    </div>'''
    html += kpi('Latest MRR', f'${m["latest_mrr"]:,.0f}', 'API revenue')
    html += kpi('Token CAGR', fmt_pct(m['token_cagr']), 'annualized', cagr_color)
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

    <!-- SECTION 1: Developer Adoption (renamed from Growth Accounting — Users) -->
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

    <!-- SECTION 2: Growth Overview (renamed from Growth Accounting — Revenue) -->
    <div class="analysis-section" data-section="{sid}-rev-ga">
        <div class="analysis-header" onclick="toggleSection(this)">
            <div class="analysis-title"><span class="chevron">&#x25BC;</span> Growth Overview</div>
            <div class="analysis-summary">
                <span class="sum-item">MRR <span class="sum-val">${m['latest_mrr']:,.0f}</span></span>
                <span class="sum-item">CAGR <span class="sum-val">{m['token_cagr']*100:.0f}%</span></span>
            </div>
        </div>
        <div class="analysis-body">
            <div class="mode-tabs" data-section="{sid}-rev-ga">
                <div class="mode-tab active" data-mode="qr">Quick Ratio</div>
                <div class="mode-tab" data-mode="ga">Growth Accounting</div>
                <div class="mode-tab" data-mode="rev-tok">Revenue & Tokens</div>
            </div>
            <div class="mode-panel active" data-mode="qr">
                <div class="row-1"><div class="card">{ch.get('spend_qr', '')}</div></div>
            </div>
            <div class="mode-panel" data-mode="ga">
                <div class="row-1"><div class="card">{ch['growth_acct']}</div></div>
            </div>
            <div class="mode-panel" data-mode="rev-tok">
                <div class="row-2">
                    <div class="card">{ch['revenue']}</div>
                    <div class="card">{ch['tokens']}</div>
                </div>
            </div>
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
                <div class="mode-tab active" data-mode="ltv">LTV Curve</div>
                <div class="mode-tab" data-mode="ltv-heat">LTV Heatmap</div>
                {'<div class="mode-tab" data-mode="rev-ret">Revenue Retention</div>' if 'rev_retention' in ch else ''}
                {'<div class="mode-tab" data-mode="gross-ret">Gross Retention</div>' if 'gross_ret' in ch else ''}
            </div>
            <div class="mode-panel active" data-mode="ltv">
                <div class="row-1"><div class="card">{ch.get('ltv_curve', '')}</div></div>
            </div>
            <div class="mode-panel" data-mode="ltv-heat">
                <div class="row-1"><div class="card">{ch.get('ltv_heatmap', '')}</div></div>
            </div>
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
# PORTFOLIO CONTENT = Tier 1 + Tier 2 only
# ============================================================

portfolio_content = f'''
{tier1_html}
{tier2_html}
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

/* ========== TIER 1: PULSE BLOCK ========== */
.pulse-block {{ margin-bottom:28px; }}

.pulse-cards {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:16px; }}
.pulse-card {{ background:{CARD}; border-radius:8px; padding:16px 18px; }}
.pc-label {{ font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:{MUTED}; font-weight:500; margin-bottom:4px; }}
.pc-value {{ font-size:22px; font-weight:500; color:{TEXT}; }}
.pc-sub {{ font-size:11px; color:{MUTED}; margin-top:2px; }}

.pulse-panels {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.pulse-panel {{ background:#fff; border:0.5px solid {GRID}; border-radius:12px; padding:20px; }}
.pulse-panel-chart {{ padding:12px 8px 4px; overflow:hidden; }}
.panel-title {{ font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:{MUTED}; font-weight:600; margin-bottom:4px; }}
.panel-subtitle {{ font-size:11px; color:{MUTED}; margin-bottom:16px; }}

/* Waterfall rows */
.waterfall-rows {{ display:flex; flex-direction:column; gap:8px; }}
.waterfall-row {{ display:grid; grid-template-columns:100px 1fr 60px; align-items:center; gap:8px; }}
.wf-label {{ font-size:12px; color:{DIM}; text-align:right; }}
.waterfall-bar {{ flex:1; }}
.wf-track {{ height:18px; background:{BORDER_SUBTLE}; border-radius:3px; overflow:hidden; }}
.wf-fill {{ height:100%; border-radius:3px; transition:width 0.4s ease; }}
.wf-value {{ font-size:12px; font-weight:500; text-align:right; }}
.wf-net .wf-label {{ font-weight:600; color:{TEXT}; }}
.wf-divider {{ height:1px; background:{BORDER_SUBTLE}; margin:4px 0; }}
.wf-legend {{ display:flex; gap:16px; margin-top:12px; }}
.wf-legend-item {{ font-size:11px; color:{MUTED}; display:flex; align-items:center; gap:4px; }}
.wf-dot {{ width:8px; height:8px; border-radius:50%; }}

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
.partner-list-section {{ margin-top:4px; }}
.pl-header {{ margin-bottom:12px; }}
.pl-title {{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:{MUTED}; }}
.pl-subtitle {{ font-size:11px; color:{MUTED}; margin-top:2px; }}
.partner-list {{ padding:0; overflow-x:auto; position:relative; }}
.partner-list::after {{ content:''; position:absolute; right:0; top:0; bottom:0; width:40px; background:linear-gradient(90deg, transparent, {CARD}); pointer-events:none; opacity:0; transition:opacity 0.3s; }}
.partner-list.scrollable::after {{ opacity:1; }}

.perf-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
.perf-table th {{ text-align:left; padding:10px 14px; border-bottom:1px solid {GRID}; color:{MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:0.04em; font-weight:600; white-space:nowrap; }}
.perf-table td {{ padding:10px 14px; border-bottom:1px solid {BORDER_SUBTLE}; white-space:nowrap; color:{DIM}; }}
.perf-table tr:last-child td {{ border-bottom:none; }}
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
.metric-cell {{ font-weight:500; }}
.metric-cell.metric-green {{ color:{SUCCESS}; }}
.metric-cell.metric-amber {{ color:{WARNING}; }}
.metric-cell.metric-red {{ color:{DANGER}; }}

html {{ scroll-behavior:smooth; }}

@media (max-width:900px) {{
    .row-2 {{ grid-template-columns:1fr; }}
    .kpi-row {{ grid-template-columns:1fr 1fr; }}
    .pulse-cards {{ grid-template-columns:1fr 1fr; }}
    .pulse-panels {{ grid-template-columns:1fr; }}
    .assumptions {{ flex-direction:column; gap:8px; }}
    .content {{ padding:16px; }}
    .topbar {{ padding:16px; }}
}}

@media (max-width:480px) {{
    .kpi-row {{ grid-template-columns:1fr; }}
    .pulse-cards {{ grid-template-columns:1fr; }}
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
    <div class="tab" data-tab="s001"><span class="dot" style="background:{COLORS['S001']}"></span>MedScribe AI</div>
    <div class="tab" data-tab="s002"><span class="dot" style="background:{COLORS['S002']}"></span>Eigen Technologies</div>
    <div class="tab" data-tab="s003"><span class="dot" style="background:{COLORS['S003']}"></span>BuilderKit</div>
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
    if (!section.classList.contains('collapsed')) {{
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
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

// Table row click -> navigate to company tab
document.querySelectorAll('.perf-row').forEach(row => {{
    row.addEventListener('click', () => {{
        const sid = row.dataset.sid.toLowerCase();
        const tab = document.querySelector('[data-tab="' + sid + '"]');
        if (tab) tab.click();
    }});
}});

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

</body>
</html>'''

output_path = '/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/dashboard.html'
with open(output_path, 'w') as f:
    f.write(full_html)

print(f"Dashboard saved: {output_path}")
print(f"Size: {len(full_html) / 1024:.0f} KB")
