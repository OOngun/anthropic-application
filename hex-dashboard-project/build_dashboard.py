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
        height=h, margin=dict(l=50, r=20, t=40, b=40),
        xaxis=dict(gridcolor=BORDER_SUBTLE, linecolor=GRID, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=BORDER_SUBTLE, linecolor=GRID, showgrid=True, zeroline=False),
        legend=dict(bgcolor='rgba(0,0,0,0)', orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, font=dict(size=11)),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=TEXT, font_color=BG, font_size=12, font_family='IBM Plex Sans'),
    )

_chart_counter = [0]
def to_div(fig, chart_id=None):
    if chart_id is None:
        _chart_counter[0] += 1
        chart_id = f'chart-{_chart_counter[0]}'
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)

def kpi(label, value, sub='', color=TEXT):
    return f'<div class="kpi"><div class="kpi-l">{label}</div><div class="kpi-v" style="color:{color}">{value}</div><div class="kpi-s">{sub}</div></div>'

# ============================================================
# PORTFOLIO CHARTS
# ============================================================

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

# Token consumption
fig_tokens = go.Figure()
for sid in ['S001', 'S002', 'S003']:
    d = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    fig_tokens.add_trace(go.Scatter(x=d['month'], y=d['total_tokens'], name=NAMES[sid],
        mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=4),
        hovertemplate='%{y:,.0f}<extra></extra>'))
fig_tokens.update_layout(**layout('Monthly Token Consumption'))
fig_tokens.update_yaxes(tickformat=',')

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
    f.add_trace(go.Scatter(x=d_usage['month'], y=d_usage['total_tokens'], mode='lines+markers',
        line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False,
        hovertemplate='%{y:,.0f}<extra></extra>'))
    f.update_layout(**layout('Monthly Tokens'))
    f.update_yaxes(tickformat=',')
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
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    latest = u.iloc[-1]

    roi_color = SUCCESS if m['roi'] > 2 else WARNING if m['roi'] > 1 else DANGER
    payback_val = f"{m['payback']} mo" if m['payback'] else 'Not yet'
    payback_color = SUCCESS if m['payback'] and m['payback'] < 18 else WARNING if m['payback'] else DANGER
    cagr_color = SUCCESS if m['token_cagr'] > 2 else WARNING if m['token_cagr'] > 0.5 else DANGER

    html = '<div class="kpi-row">'
    html += kpi('Latest MRR', f'${m["latest_mrr"]:,.0f}', 'API revenue')
    html += kpi('Token CAGR', fmt_pct(m['token_cagr']), 'annualized', cagr_color)
    html += kpi('Active Devs', f'{m["active_devs"]}', 'current month')
    html += kpi('Rev/Dev', f'${m["rev_per_dev"]:,.0f}', 'per developer')
    html += kpi('Credit ROI', f'{m["roi"]:.1f}x', f'${m["credits"]:,.0f} invested', roi_color)
    html += kpi('Payback', payback_val, '', payback_color)
    html += '</div>'

    # Model revenue breakdown
    html += '<div class="kpi-row">'
    html += kpi('Sonnet Rev', f'${m["sonnet_total"]:,.0f}', f'{m["sonnet_total"]/m["total_rev"]*100:.0f}% of total', '#3b82f6')
    html += kpi('Opus Rev', f'${m["opus_total"]:,.0f}', f'{m["opus_total"]/m["total_rev"]*100:.0f}% of total', '#8b5cf6')
    html += kpi('Haiku Rev', f'${m["haiku_total"]:,.0f}', f'{m["haiku_total"]/m["total_rev"]*100:.0f}% of total', '#06b6d4')
    html += kpi('Avg Latency', f'{m["latest_latency"]:.0f}ms', '', SUCCESS if m['latest_latency'] < 400 else TEXT)
    html += '</div>'
    return html

# ============================================================
# STARTUP TAB CONTENT
# ============================================================

def startup_tab_html(sid):
    s = startups[startups['startup_id'] == sid].iloc[0]
    ch = startup_charts[sid]

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

    <div class="section-header">Revenue & Tokens</div>
    <div class="row-2">
        <div class="card">{ch['revenue']}</div>
        <div class="card">{ch['tokens']}</div>
    </div>

    <div class="section-header">Revenue by Model</div>
    <div class="row-2">
        <div class="card">{ch['rev_by_model']}</div>
        <div class="card">{ch['model_mix']}</div>
    </div>

    <div class="section-header">Spend Growth Accounting</div>
    <div class="row-1">
        <div class="card">{ch['growth_acct']}</div>
    </div>

    <div class="section-header">Adoption & Reliability</div>
    <div class="row-2">
        <div class="card">{ch['devs_calls']}</div>
        <div class="card">{ch['latency']}</div>
    </div>
    {'<div class="row-1"><div class="card">' + ch['engagement'] + '</div></div>' if 'engagement' in ch else ''}
    '''
    return html

# ============================================================
# PORTFOLIO CONTENT
# ============================================================

portfolio_content = f'''
{portfolio_kpis}

<div class="section-header">Top Performers</div>
{top_performers_html}

<div class="section-header">Revenue by Model</div>
<div class="row-2">
    <div class="card">{to_div(fig_rev_model, 'p-rev-model')}</div>
    <div class="card">{to_div(fig_rev_model_time, 'p-rev-model-time')}</div>
</div>

<div class="section-header">Revenue & Token Consumption</div>
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

<div class="section-header">Active Developers</div>
<div class="row-1">
    <div class="card">{to_div(fig_devs, 'p-devs')}</div>
</div>

<!-- TODO: Credit Payback chart — needs refinement on what "payback" means in credit context -->
<!-- <div class="section-header">Credit Payback</div>
<div class="row-1"><div class="card">{to_div(fig_payback, 'p-payback')}</div></div> -->

<!-- TODO: Spend Quick Ratio — need better understanding of growth accounting decomposition before showing -->
<!-- <div class="section-header">Spend Health</div>
<div class="row-1"><div class="card">{to_div(fig_qr, 'p-qr')}</div></div> -->
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

.kpi-row {{ display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }}
.kpi {{ background:{CARD}; border:1px solid {GRID}; border-radius:8px; padding:14px 18px; flex:1; min-width:140px; }}
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

.perf-table-wrap {{ padding:0; overflow-x:auto; }}
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
.toggle-chip {{ --chip-color:{ACCENT}; }}
.toggle-chip.active {{ background:{ACCENT_LIGHT}; border-color:{ACCENT}; }}

html {{ scroll-behavior:smooth; }}

@media (max-width:900px) {{
    .row-2 {{ grid-template-columns:1fr; }}
    .kpi-row {{ flex-direction:column; }}
    .assumptions {{ flex-direction:column; gap:8px; }}
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
    <div class="tab active" data-tab="portfolio">All Companies</div>
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
const tokenData = {json.dumps({sid: monthly_usage[monthly_usage['startup_id']==sid].sort_values('month')[['total_tokens']].values.flatten().tolist() for sid in ['S001','S002','S003']})};
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

        const titleText = showingMetric === 'tokens' ? 'Monthly Token Consumption' : 'Monthly API Revenue';
        const tickpre = showingMetric === 'tokens' ? '' : '$';
        Plotly.relayout(revChartId, {{
            'title.text': titleText,
            'yaxis.tickprefix': tickpre
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
