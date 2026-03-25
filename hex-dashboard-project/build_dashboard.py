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
unit_economics = pd.read_csv(f'{OUTPUT_DIR}/unit_economics.csv')
unit_economics['month'] = pd.to_datetime(unit_economics['month'])
engagement = pd.read_csv(f'{OUTPUT_DIR}/engagement_depth.csv')

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

# Canonical GA colors (shared across Pulse and company detail)
GA_NEW = GAIN           # #1D9E75
GA_RETAINED = '#94a3b8'
GA_EXPANSION = '#34d399'
GA_RESURRECTED = '#6ee7b7'
GA_CONTRACTION = '#fb923c'
GA_CHURNED = LOSS       # #D85A30

# ============================================================
# COMPUTE PER-COMPANY METRICS
# ============================================================

company_metrics = []
for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    ue = unit_economics[unit_economics['startup_id'] == sid]
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
    rev_per_dev = latest['revenue_usd'] / latest['active_developers'] if latest['active_developers'] > 0 else 0
    tok_per_dev = latest['total_tokens'] / latest['active_developers'] if latest['active_developers'] > 0 else 0

    if len(u) >= 6:
        recent_3 = u.tail(3)['revenue_usd'].mean()
        prior_3 = u.iloc[-6:-3]['revenue_usd'].mean()
        momentum = (recent_3 / prior_3 - 1) * 100 if prior_3 > 0 else 0
    else:
        momentum = 0

    avg_qr = 0  # overwritten after per-company GA is computed from dev_activity

    # Latest gross retention for this company
    latest_gross_ret = 0  # overwritten after per-company GA is computed from dev_activity

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
        active_devs=int(latest['active_developers']),
        rev_per_dev=rev_per_dev, tok_per_dev=tok_per_dev,
        momentum=momentum, avg_qr=avg_qr,
        latest_latency=latest['avg_latency_ms'],
        latest_error=latest['error_rate'],
        gross_retention=latest_gross_ret,
        last_active_days=last_active_days,
    ))

company_metrics.sort(key=lambda x: x['latest_mrr'], reverse=True)

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

# === REGENERATE DEVELOPER-LEVEL ACTIVITY DATA ===
# Staggered onboarding: devs join gradually across months, not all at once.
# Archetype-aware: star/strong accelerate, declining/churned lose devs.
# Case study partners (CS01/CS02/CS03) use special cohort-aware generation.

np.random.seed(2024)
_archetype_map = dict(zip(startups['startup_id'], startups['archetype']))

_dev_rows = []

# --- Case study partner generation (cohort-aware) ---
def _gen_cs_devs(sid, cohort_plan, churn_range, rev_power=0.5):
    """Generate dev rows for a case study partner.
    cohort_plan: list of (month_idx, n_devs) for onboarding events
    churn_range: (lo, hi) monthly churn probability per dev
    rev_power: exponent for power-law revenue distribution
    """
    _rng = np.random.RandomState(hash(sid) % (2**31))
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    months = u['month'].tolist()
    rev_vals = u['revenue_usd'].values
    n_months = len(months)
    rows = []
    all_devs = {}
    dev_counter = 0
    active_pool = []

    # Build onboard schedule from plan
    onboard_at = {mi: n for mi, n in cohort_plan}

    for mi in range(n_months):
        target_rev = rev_vals[mi]
        # Churn existing devs
        surviving = []
        for did in active_pool:
            cr = _rng.uniform(churn_range[0], churn_range[1])
            if _rng.random() > cr:
                surviving.append(did)
        active_pool = surviving
        # Onboard
        n_new = onboard_at.get(mi, 0)
        for _ in range(n_new):
            dev_counter += 1
            did = f'{sid}_d{dev_counter}'
            all_devs[did] = mi
            active_pool.append(did)
        if not active_pool or target_rev <= 0:
            continue
        n_active = len(active_pool)
        w = np.array([1.0 / (i + 1) ** rev_power for i in range(n_active)])
        _rng.shuffle(w)
        w = w / w.sum() * target_rev
        for i, did in enumerate(active_pool):
            rv = round(max(w[i] * _rng.uniform(0.92, 1.08), 0.50), 2)
            rows.append({'dev_id': did, 'startup_id': sid,
                         'month': months[mi].strftime('%Y-%m-%d'), 'revenue': rv})
    # Rescale each month to match target revenue exactly
    import pandas as _pd
    df = _pd.DataFrame(rows)
    for mi in range(n_months):
        m = months[mi].strftime('%Y-%m-%d')
        target = rev_vals[mi]
        mask = df['month'] == m
        actual = df.loc[mask, 'revenue'].sum()
        if actual > 0:
            df.loc[mask, 'revenue'] = (df.loc[mask, 'revenue'] / actual * target).round(2)
    return df.to_dict('records')

# CS01 WriteFlow: consumer app, 40-60 total unique devs, high turnover (28-40% churn)
_cs01_cohorts = [(0,6),(1,4),(2,6),(3,4),(4,2),(5,2),(6,4),(7,3),(8,1),(9,1),
                 (10,1),(11,1),(12,2),(13,1),(14,2),(15,2),(16,1),(18,1),(20,1),(21,1),(22,1),(23,1)]
_dev_rows.extend(_gen_cs_devs('CS01', _cs01_cohorts, (0.28, 0.40), 0.5))

# CS02 FinLedger: internal dev tooling, 8-12 devs, very low churn (2%)
_cs02_cohorts = [(0,4),(5,1),(10,1),(15,1),(20,1)]
_dev_rows.extend(_gen_cs_devs('CS02', _cs02_cohorts, (0.01, 0.03), 0.3))

# CS03 BrieflyAI: B2B platform, 15-25 devs, step-function onboarding, moderate churn (8-12%)
_cs03_cohorts = [(0,5),(5,3),(10,4),(12,1),(16,4),(21,4),(23,1)]
_dev_rows.extend(_gen_cs_devs('CS03', _cs03_cohorts, (0.08, 0.12), 0.4))

# --- Standard partner generation ---
for sid in ALL_SIDS:
    if sid in ('CS01', 'CS02', 'CS03'):
        continue  # already generated above

    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    months = u['month'].tolist()
    rev_vals = u['revenue_usd'].values
    dev_counts = u['active_developers'].astype(int).values
    arch = _archetype_map.get(sid, 'fine')
    n_months = len(months)

    # Decide total unique developers and onboarding schedule
    total_devs_ever = max(int(max(dev_counts) * 1.4), 2)

    # Build per-month onboarding count: stagger across months
    onboard_schedule = np.zeros(n_months, dtype=int)

    if arch in ('star', 'rocket'):
        weights = np.array([(i + 1) ** 1.5 for i in range(n_months)], dtype=float)
    elif arch == 'strong':
        weights = np.array([(i + 1) ** 1.0 for i in range(n_months)], dtype=float)
    elif arch == 'steady':
        weights = np.ones(n_months, dtype=float)
        weights[:3] = 1.5
    elif arch in ('declining',):
        weights = np.array([max(n_months - i, 0) ** 2 for i in range(n_months)], dtype=float)
        weights[n_months // 2:] = 0
    elif arch == 'churned':
        cutoff = max(int(n_months * 0.4), 2)
        weights = np.zeros(n_months, dtype=float)
        weights[:cutoff] = np.array([max(cutoff - i, 0) for i in range(cutoff)], dtype=float)
    elif arch == 'minimal':
        total_devs_ever = min(total_devs_ever, 2)
        weights = np.zeros(n_months, dtype=float)
        weights[0] = 1.0
    else:
        weights = np.ones(n_months, dtype=float)

    if weights.sum() > 0:
        weights = weights / weights.sum()
    else:
        weights[0] = 1.0

    for d in range(total_devs_ever):
        month_idx = np.random.choice(n_months, p=weights)
        onboard_schedule[month_idx] += 1

    if onboard_schedule[0] == 0 and total_devs_ever > 0:
        max_idx = np.argmax(onboard_schedule)
        if onboard_schedule[max_idx] > 0:
            onboard_schedule[max_idx] -= 1
            onboard_schedule[0] += 1

    dev_pool = []
    dev_counter = 0
    for mi in range(n_months):
        for _ in range(onboard_schedule[mi]):
            dev_counter += 1
            dev_pool.append({'dev_id': f'{sid}_d{dev_counter}', 'start_month_idx': mi})

    for mi in range(n_months):
        target_active = dev_counts[mi]
        target_rev = rev_vals[mi]

        if target_active == 0 or target_rev <= 0:
            continue

        eligible = [d for d in dev_pool if d['start_month_idx'] <= mi]
        if not eligible:
            continue

        active_devs = []
        for d in eligible:
            tenure = mi - d['start_month_idx']
            if arch == 'churned':
                if mi > n_months * 0.5:
                    churn_prob = min(0.3 + 0.05 * (mi - n_months * 0.5), 0.95)
                    if np.random.random() < churn_prob:
                        continue
            elif arch == 'declining':
                if mi > n_months * 0.4:
                    churn_prob = min(0.1 + 0.02 * (mi - n_months * 0.4), 0.6)
                    if np.random.random() < churn_prob:
                        continue
            else:
                if tenure > 0 and np.random.random() < 0.05:
                    continue
            active_devs.append(d)

        if len(active_devs) > target_active:
            active_devs.sort(key=lambda d: d['start_month_idx'])
            active_devs = active_devs[:target_active]

        if not active_devs:
            continue

        n_active = len(active_devs)
        raw_weights = np.array([1.0 / (i + 1) ** 0.7 for i in range(n_active)])
        raw_weights = raw_weights / raw_weights.sum() * target_rev

        np.random.shuffle(active_devs)

        for i, d in enumerate(active_devs):
            rev = round(max(raw_weights[i] + np.random.normal(0, raw_weights[i] * 0.1), 0.01), 2)
            _dev_rows.append({
                'dev_id': d['dev_id'], 'startup_id': sid,
                'month': months[mi].strftime('%Y-%m-%d'), 'revenue': rev
            })

import csv
_dev_csv_path = f'{OUTPUT_DIR}/developer_activity.csv'
with open(_dev_csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['dev_id', 'startup_id', 'month', 'revenue'])
    w.writeheader()
    w.writerows(_dev_rows)

dev_activity = pd.DataFrame(_dev_rows)
dev_activity['month'] = pd.to_datetime(dev_activity['month'])
dev_activity['revenue'] = dev_activity['revenue'].astype(float)
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

# ============================================================
# PRE-COMPUTE PER-COMPANY GA FROM developer_activity (used by
# company_metrics AND per-company charts later)
# ============================================================
_ga_empty_cols = ['month','new_revenue','expansion_revenue','resurrected_revenue',
                  'retained_revenue','churned_revenue','contraction_revenue',
                  'total_revenue','quick_ratio','gross_retention_pct']
per_company_ga_df = {}
for sid in ALL_SIDS:
    _dev_sid = dev_activity[dev_activity['startup_id'] == sid]
    _d_usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    if len(_dev_sid) == 0 or len(_d_usage) < 2:
        per_company_ga_df[sid] = pd.DataFrame(columns=_ga_empty_cols)
        continue
    _dev_first = _dev_sid.groupby('dev_id')['month'].min().to_dict()
    _months_list = sorted(_d_usage['month'].unique())
    _rows = []
    for _j in range(1, len(_months_list)):
        _prev_m, _curr_m = _months_list[_j-1], _months_list[_j]
        _prev = _dev_sid[_dev_sid['month'] == _prev_m].set_index('dev_id')['revenue']
        _curr = _dev_sid[_dev_sid['month'] == _curr_m].set_index('dev_id')['revenue']
        _all_ids = set(_prev.index) | set(_curr.index)
        _new = _exp = _res = _ret = _churn = _contr = 0
        for _did in _all_ids:
            _p = _prev.get(_did, 0)
            _c = _curr.get(_did, 0)
            _is_new = _dev_first.get(_did) == _curr_m
            if _c > 0 and _p > 0:
                _ret += min(_c, _p)
                if _c > _p: _exp += (_c - _p)
                elif _c < _p: _contr += (_p - _c)
            elif _c > 0 and _p == 0:
                if _is_new: _new += _c
                else: _res += _c
            elif _c == 0 and _p > 0:
                _churn += _p
        _pt = _prev.sum()
        _qr = (_exp + _new + _res) / (_contr + _churn) if (_contr + _churn) > 0 else 10.0
        _gret = _ret / _pt * 100 if _pt > 0 else 0
        _rows.append({
            'month': _curr_m,
            'new_revenue': _new, 'expansion_revenue': _exp,
            'resurrected_revenue': _res, 'retained_revenue': _ret,
            'churned_revenue': _churn, 'contraction_revenue': _contr,
            'total_revenue': _ret + _new + _exp + _res,
            'quick_ratio': _qr, 'gross_retention_pct': _gret,
        })
    per_company_ga_df[sid] = pd.DataFrame(_rows) if _rows else pd.DataFrame(columns=_ga_empty_cols)

# Build per-partner-per-month GA breakdown for click drilldown
_ga_drilldown = {}  # { 'YYYY-MM-DD': { 'contraction': [{name, amount}, ...], 'churned': [...], ... } }
_all_ga_months = sorted(set(m for df in per_company_ga_df.values() for m in df['month'].tolist() if len(df) > 0))
for _m in _all_ga_months:
    _m_str = _m.strftime('%Y-%m-%d') if hasattr(_m, 'strftime') else str(_m)[:10]
    _ga_drilldown[_m_str] = {comp: [] for comp in ['new_revenue','expansion_revenue','resurrected_revenue','contraction_revenue','churned_revenue']}
    for sid in ALL_SIDS:
        _cga = per_company_ga_df.get(sid)
        if _cga is None or len(_cga) == 0:
            continue
        _row = _cga[_cga['month'] == _m]
        if len(_row) == 0:
            continue
        _r = _row.iloc[0]
        for comp in ['new_revenue','expansion_revenue','resurrected_revenue','contraction_revenue','churned_revenue']:
            val = float(_r.get(comp, 0))
            if val > 0.5:  # only include if meaningful
                _ga_drilldown[_m_str][comp].append({'name': NAMES.get(sid, sid), 'sid': sid, 'amount': round(val, 0)})
    # Sort each component by amount descending
    for comp in _ga_drilldown[_m_str]:
        _ga_drilldown[_m_str][comp].sort(key=lambda x: -x['amount'])

_ga_drilldown_json = json.dumps(_ga_drilldown)

# Per-partner QR (from partner-level) and gross retention (from developer-level)
per_partner_qr = {}
per_partner_gret = {}

# Developer-level gross retention: accounts for individual dev churn even if partner total grows
dev_months = sorted(dev_activity['month'].unique())
if len(dev_months) >= 2:
    prev_dm, curr_dm = dev_months[-2], dev_months[-1]
    for sid in ALL_SIDS:
        prev_devs = dev_activity[(dev_activity['startup_id'] == sid) & (dev_activity['month'] == prev_dm)].set_index('dev_id')['revenue']
        curr_devs = dev_activity[(dev_activity['startup_id'] == sid) & (dev_activity['month'] == curr_dm)].set_index('dev_id')['revenue']
        retained = sum(min(prev_devs.get(d, 0), curr_devs.get(d, 0)) for d in set(prev_devs.index) & set(curr_devs.index))
        prev_total = prev_devs.sum()
        per_partner_gret[sid] = retained / prev_total * 100 if prev_total > 0 else 0

for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    if len(u) < 2:
        per_partner_qr[sid] = 0
        if sid not in per_partner_gret: per_partner_gret[sid] = 0
        continue
    last_rev = u.iloc[-1]['revenue_usd']
    prev_rev = u.iloc[-2]['revenue_usd']
    if last_rev > 0 and prev_rev > 0:
        gains = losses = 0
        for j in range(max(1, len(u)-6), len(u)):
            c = u.iloc[j]['revenue_usd']
            p = u.iloc[j-1]['revenue_usd']
            if c > p: gains += (c - p)
            elif c < p: losses += (p - c)
            if c == 0 and p > 0: losses += p
            if c > 0 and p == 0: gains += c
        per_partner_qr[sid] = gains / losses if losses > 0 else 10.0
    else:
        per_partner_qr[sid] = 0
        if sid not in per_partner_gret: per_partner_gret[sid] = 0

# Fix last_active_days and overwrite avg_qr / gross_retention from per-company GA
for m in company_metrics:
    sid = m['sid']
    _cga = per_company_ga_df.get(sid)
    if _cga is not None and len(_cga) > 0 and 'quick_ratio' in _cga.columns:
        m['avg_qr'] = _cga['quick_ratio'].tail(6).mean()
    elif sid in per_partner_qr:
        m['avg_qr'] = per_partner_qr[sid]
    if _cga is not None and len(_cga) > 0 and 'gross_retention_pct' in _cga.columns and not _cga['gross_retention_pct'].isna().all():
        m['gross_retention'] = _cga['gross_retention_pct'].iloc[-1]
    elif sid in per_partner_gret:
        m['gross_retention'] = per_partner_gret[sid]
    # Last active: deterministic based on revenue tier
    # >$1000/mo => 0-2 days, $100-1000 => 1-5 days, churned => 30+
    if m['latest_mrr'] > 1000:
        m['last_active_days'] = max(0, min(2, int(2 - m['latest_mrr'] / 20000)))
    elif m['latest_mrr'] > 100:
        m['last_active_days'] = 1 + int(4 * (1 - (m['latest_mrr'] - 100) / 900))
    elif m['latest_mrr'] > 0:
        m['last_active_days'] = 10
    else:
        # Churned: find last active month
        u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
        active = u[u['revenue_usd'] > 0]
        if len(active) > 0:
            last_m = active.iloc[-1]['month']
            latest_m = u.iloc[-1]['month']
            m['last_active_days'] = max((latest_m - last_m).days, 30)
        else:
            m['last_active_days'] = 999

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

# ============================================================
# INTERACTIVE WATERFALL DATA: all scope x period combinations
# ============================================================

# Map archetype names to scope filter keys (matching the user-facing labels)
_scope_map = {
    'all': None,  # no filter
    'star': ['star', 'rocket'],
    'strong': ['strong', 'steady'],
    'fine': ['fine'],
    'declining': ['declining'],
    'churned': ['churned', 'minimal'],
}

def _compute_ga_for_sids(sid_subset):
    """Recompute aggregate revenue GA for a subset of startup IDs."""
    sub_dev = dev_activity[dev_activity['startup_id'].isin(sid_subset)]
    sub_months = sorted(sub_dev['month'].unique())
    sub_first = sub_dev.groupby('dev_id')['month'].min().to_dict()
    rows = []
    for i in range(1, len(sub_months)):
        pm, cm = sub_months[i-1], sub_months[i]
        prev = sub_dev[sub_dev['month'] == pm].set_index('dev_id')['revenue']
        curr = sub_dev[sub_dev['month'] == cm].set_index('dev_id')['revenue']
        nr = er = rr = ret = cr = ch = 0
        for did in set(prev.index) | set(curr.index):
            p, c = prev.get(did, 0), curr.get(did, 0)
            is_new = (sub_first.get(did) == cm)
            if c > 0 and p > 0:
                ret += min(c, p)
                if c > p: er += (c - p)
                elif c < p: cr += (p - c)
            elif c > 0 and p == 0:
                if is_new: nr += c
                else: rr += c
            elif c == 0 and p > 0:
                ch += p
        rows.append({'month': cm, 'total': nr + ret + er + rr,
                     'new': nr, 'expansion': er, 'resurrected': rr,
                     'retained': ret, 'contraction': cr, 'churned': ch})
    return pd.DataFrame(rows).sort_values('month') if rows else pd.DataFrame()

def _ga_pct_df(ga_df):
    """Convert raw GA df to pct-of-prior-period df."""
    if len(ga_df) < 2:
        return pd.DataFrame()
    shifted = ga_df['total'].shift(1)
    out = pd.DataFrame({'month': ga_df['month']})
    for col in ['new', 'expansion', 'resurrected', 'contraction', 'churned']:
        out[col] = ga_df[col] / shifted * 100
    out['net'] = (ga_df['total'] - ga_df['total'].shift(1)) / shifted * 100
    return out.dropna()

def _period_avg(pct_df, period):
    """Average the last N rows based on period key."""
    if len(pct_df) == 0:
        return {'new': 0, 'expansion': 0, 'resurrected': 0, 'contraction': 0, 'churned': 0, 'net': 0}
    if period == '1M':
        row = pct_df.iloc[-1]
        return {k: float(row[k]) for k in ['new', 'expansion', 'resurrected', 'contraction', 'churned', 'net']}
    elif period == '3M':
        sub = pct_df.tail(3)
    elif period == '6M':
        sub = pct_df.tail(6)
    elif period == '12M':
        sub = pct_df.tail(12)
    elif period == 'YTD':
        latest_year = pct_df['month'].iloc[-1].year
        sub = pct_df[pct_df['month'].dt.year == latest_year]
    else:  # 'All'
        sub = pct_df
    if len(sub) == 0:
        return {'new': 0, 'expansion': 0, 'resurrected': 0, 'contraction': 0, 'churned': 0, 'net': 0}
    return {k: float(sub[k].mean()) for k in ['new', 'expansion', 'resurrected', 'contraction', 'churned', 'net']}

def _trend_arrays(pct_df):
    """Return last 6 values for each component (for sparklines)."""
    tail = pct_df.tail(6)
    return {k: [round(float(v), 2) for v in tail[k].values] for k in ['new', 'expansion', 'resurrected', 'contraction', 'churned', 'net']}

# Rename ga_pct_history columns to match the standard names used by _ga_pct_df
_ga_pct_all = ga_pct_history.rename(columns={
    'new_pct': 'new', 'expansion_pct': 'expansion', 'resurrected_pct': 'resurrected',
    'contraction_pct': 'contraction', 'churned_pct': 'churned', 'net_pct': 'net'
})

# Pre-compute GA for each scope
_scope_ga = {}
_scope_pct = {}
for scope_key, arch_list in _scope_map.items():
    if arch_list is None:
        _scope_ga[scope_key] = agg_rev_ga.copy()
        _scope_pct[scope_key] = _ga_pct_all.copy()
    else:
        sids = [s for s in ALL_SIDS if _archetype_map.get(s, 'fine') in arch_list]
        if not sids:
            _scope_ga[scope_key] = pd.DataFrame()
            _scope_pct[scope_key] = pd.DataFrame()
        else:
            raw = _compute_ga_for_sids(sids)
            _scope_ga[scope_key] = raw
            _scope_pct[scope_key] = _ga_pct_df(raw)

# Build the full JSON blob: { "all|1M": {new, expansion, ...}, ... }
_wf_json = {}
_periods = ['1M', '3M', '6M', '12M', 'YTD', 'All']
for scope_key in _scope_map:
    pct_df = _scope_pct[scope_key]
    trends = _trend_arrays(pct_df) if len(pct_df) >= 2 else {k: [] for k in ['new', 'expansion', 'resurrected', 'contraction', 'churned', 'net']}
    # Compute full-history avg for the "avg" column in table view
    full_avg = _period_avg(pct_df, 'All')
    for period in _periods:
        key = f"{scope_key}|{period}"
        vals = _period_avg(pct_df, period)
        _wf_json[key] = {
            'new': round(vals['new'], 2),
            'expansion': round(vals['expansion'], 2),
            'resurrected': round(vals['resurrected'], 2),
            'contraction': round(vals['contraction'], 2),
            'churned': round(vals['churned'], 2),
            'net': round(vals['net'], 2),
            'avg_new': round(full_avg['new'], 2),
            'avg_expansion': round(full_avg['expansion'], 2),
            'avg_resurrected': round(full_avg['resurrected'], 2),
            'avg_contraction': round(full_avg['contraction'], 2),
            'avg_churned': round(full_avg['churned'], 2),
            'avg_net': round(full_avg['net'], 2),
            'trends': trends,
        }

_wf_json_str = json.dumps(_wf_json)

# Net API Churn = (Churned + Contraction - Resurrected - Expansion) / Prior Revenue
net_churn = (latest_ga['churned_revenue'] + latest_ga['contraction_revenue'] - latest_ga['resurrected_revenue'] - latest_ga['expansion_revenue']) / prior_total * 100 if prior_total > 0 else 0

# Net Dollar Retention (NDR) = (Beginning + Expansion + Resurrected - Churn - Contraction) / Beginning × 100
# a16z definition: measures how many dollars you've secured from existing partners after expansion, downsell, and churn
ndr = (prior_total + latest_ga['expansion_revenue'] + latest_ga['resurrected_revenue'] - latest_ga['churned_revenue'] - latest_ga['contraction_revenue']) / prior_total * 100 if prior_total > 0 else 0

# Active partners count
active_partners = len([m for m in company_metrics if m['last_active_days'] < 30])

# Portfolio Quick Ratio (latest month)
gains = latest_ga['new_revenue'] + latest_ga['expansion_revenue'] + latest_ga['resurrected_revenue']
losses = latest_ga['churned_revenue'] + latest_ga['contraction_revenue']
portfolio_qr = gains / losses if losses > 0 else 10.0

# Gross retention (latest)
latest_gross_ret = agg_rev_ga['gross_ret'].dropna().iloc[-1] if agg_rev_ga['gross_ret'].dropna().any() else 0

# ============================================================
# SLIDER: PRE-COMPUTE PULSE DATA FOR EVERY PARTNER COUNT
# ============================================================

# Rank partners by total revenue (highest first)
_partner_rev_rank = monthly_usage.groupby('startup_id')['revenue_usd'].sum().sort_values(ascending=False)
_ranked_sids = _partner_rev_rank.index.tolist()

# n_active = partners with revenue > 0 in latest month
_latest_m = monthly_usage['month'].max()
_latest_rev_by_sid = monthly_usage[monthly_usage['month'] == _latest_m].groupby('startup_id')['revenue_usd'].sum()
_active_sids = [sid for sid in _ranked_sids if _latest_rev_by_sid.get(sid, 0) > 0]
n_active = len(_active_sids)
n_total = len(ALL_SIDS)

# Reorder active SIDs by total revenue rank (they're already ranked from _ranked_sids)
_active_ranked = [sid for sid in _ranked_sids if sid in _active_sids]

# For each N from 1..n_active, compute KPIs, waterfall data, GA chart data, CMGR series, and revenue share data
_pulse_by_n = {}
_all_months_sorted = sorted(monthly_usage['month'].unique())

for N in range(1, n_active + 1):
    top_n_sids = _active_ranked[:N]
    top_n_set = set(top_n_sids)

    # --- KPIs ---
    # Recompute GA for this subset using dev_activity
    sub_ga_df = _compute_ga_for_sids(top_n_sids)
    if len(sub_ga_df) >= 2:
        sub_latest = sub_ga_df.iloc[-1]
        sub_prior_total = sub_ga_df.iloc[-2]['total']
        sub_gains = sub_latest['new'] + sub_latest['expansion'] + sub_latest['resurrected']
        sub_losses = sub_latest['churned'] + sub_latest['contraction']
        sub_qr = round(sub_gains / sub_losses, 1) if sub_losses > 0 else 10.0
        sub_ndr = round((sub_prior_total + sub_latest['expansion'] + sub_latest['resurrected'] - sub_latest['churned'] - sub_latest['contraction']) / sub_prior_total * 100, 0) if sub_prior_total > 0 else 0
        sub_net_churn = round((sub_latest['churned'] + sub_latest['contraction'] - sub_latest['resurrected'] - sub_latest['expansion']) / sub_prior_total * 100, 1) if sub_prior_total > 0 else 0
        sub_gross_ret_series = sub_ga_df['retained'] / sub_ga_df['total'].shift(1) * 100
        sub_gross_ret = round(sub_gross_ret_series.dropna().iloc[-1], 0) if sub_gross_ret_series.dropna().any() else 0
    else:
        sub_qr, sub_ndr, sub_net_churn, sub_gross_ret = 0, 0, 0, 0

    # Active partners in this subset
    sub_active = sum(1 for sid in top_n_sids if _latest_rev_by_sid.get(sid, 0) > 0)

    # --- Waterfall data (all scope x period) ---
    sub_pct_df = _ga_pct_df(sub_ga_df)
    sub_wf = {}
    for period in _periods:
        vals = _period_avg(sub_pct_df, period)
        full_avg = _period_avg(sub_pct_df, 'All')
        trends = _trend_arrays(sub_pct_df) if len(sub_pct_df) >= 2 else {k: [] for k in ['new', 'expansion', 'resurrected', 'contraction', 'churned', 'net']}
        sub_wf[period] = {
            'new': round(vals['new'], 2), 'expansion': round(vals['expansion'], 2),
            'resurrected': round(vals['resurrected'], 2), 'contraction': round(vals['contraction'], 2),
            'churned': round(vals['churned'], 2), 'net': round(vals['net'], 2),
            'avg_new': round(full_avg['new'], 2), 'avg_expansion': round(full_avg['expansion'], 2),
            'avg_resurrected': round(full_avg['resurrected'], 2), 'avg_contraction': round(full_avg['contraction'], 2),
            'avg_churned': round(full_avg['churned'], 2), 'avg_net': round(full_avg['net'], 2),
            'trends': trends,
        }

    # --- Expansion vs Losses (el1 data) ---
    if len(sub_ga_df) >= 1:
        _sub_latest_ga = sub_ga_df.iloc[-1]
        el1_gains = _sub_latest_ga['new'] + _sub_latest_ga['expansion'] + _sub_latest_ga['resurrected']
        el1_losses = _sub_latest_ga['churned'] + _sub_latest_ga['contraction']
        el1_coverage = round(el1_gains / el1_losses, 1) if el1_losses > 0 else 10.0
    else:
        el1_gains, el1_losses, el1_coverage = 0, 0, 0

    # --- GA+CMGR chart data (time series) ---
    ga_chart = {'months': [], 'retained': [], 'new': [], 'expansion': [],
                'resurrected': [], 'contraction': [], 'churned': []}
    if len(sub_ga_df) > 0:
        ga_chart['months'] = [m.strftime('%Y-%m-%d') for m in sub_ga_df['month']]
        ga_chart['retained'] = [round(float(v), 2) for v in sub_ga_df['retained'].values]
        ga_chart['new'] = [round(float(v), 2) for v in sub_ga_df['new'].values]
        ga_chart['expansion'] = [round(float(v), 2) for v in sub_ga_df['expansion'].values]
        ga_chart['resurrected'] = [round(float(v), 2) for v in sub_ga_df['resurrected'].values]
        ga_chart['contraction'] = [round(float(v), 2) for v in sub_ga_df['contraction'].values]
        ga_chart['churned'] = [round(float(v), 2) for v in sub_ga_df['churned'].values]

    # CMGR lines for this subset
    sub_rev_series = monthly_usage[monthly_usage['startup_id'].isin(top_n_set)].groupby('month')['revenue_usd'].sum().sort_index()
    # Also compute portfolio_tokens for this subset
    sub_tok_series = monthly_usage[monthly_usage['startup_id'].isin(top_n_set)].groupby('month')['total_tokens'].sum().sort_index()
    cmgr_chart = {'months': [], 'cmgr3': [], 'cmgr6': [], 'cmgr12': []}
    sub_months_list = sub_tok_series.index.tolist()
    for i_m in range(len(sub_months_list)):
        sub_slice = sub_tok_series.iloc[:i_m+1]
        c3 = cmgr(sub_slice, 3) if len(sub_slice) > 6 else None
        c6 = cmgr(sub_slice, 6) if len(sub_slice) > 9 else None
        c12 = cmgr(sub_slice, 12) if len(sub_slice) > 12 else None
        cmgr_chart['months'].append(sub_months_list[i_m].strftime('%Y-%m-%d'))
        cmgr_chart['cmgr3'].append(round(c3 * 100, 2) if c3 is not None else None)
        cmgr_chart['cmgr6'].append(round(c6 * 100, 2) if c6 is not None else None)
        cmgr_chart['cmgr12'].append(round(c12 * 100, 2) if c12 is not None else None)

    # --- Revenue share (AoE) chart data ---
    _sub_rev_by_pm = monthly_usage[monthly_usage['startup_id'].isin(top_n_set)].groupby(['startup_id', 'month'])['revenue_usd'].sum().reset_index()
    _sub_monthly_total = _sub_rev_by_pm.groupby('month')['revenue_usd'].sum().reindex(_all_months_sorted, fill_value=0)

    # Top 7 (or fewer) shown individually, rest as "Others"
    _sub_partner_total = _sub_rev_by_pm.groupby('startup_id')['revenue_usd'].sum().sort_values(ascending=False)
    _sub_top_n_aoe = min(7, N)
    _sub_top_sids_aoe = _sub_partner_total.head(_sub_top_n_aoe).index.tolist()
    _sub_other_sids_aoe = _sub_partner_total.iloc[_sub_top_n_aoe:].index.tolist()

    aoe_chart = {'months': [m.strftime('%Y-%m-%d') for m in _all_months_sorted], 'traces': []}

    # Others
    if _sub_other_sids_aoe:
        _sub_others_monthly = _sub_rev_by_pm[_sub_rev_by_pm['startup_id'].isin(_sub_other_sids_aoe)].groupby('month')['revenue_usd'].sum().reindex(_all_months_sorted, fill_value=0)
        _sub_others_pct = (_sub_others_monthly / _sub_monthly_total * 100).fillna(0).values.tolist()
        aoe_chart['traces'].append({
            'name': f'Others ({len(_sub_other_sids_aoe)})',
            'y': [round(v, 2) for v in _sub_others_pct],
            'color': '#94a3b8', 'fillcolor': 'rgba(148,163,184,0.4)'
        })

    # Individual top partners (reversed so biggest at bottom)
    for sid in reversed(_sub_top_sids_aoe):
        d_vals = _sub_rev_by_pm[_sub_rev_by_pm['startup_id'] == sid].set_index('month').reindex(_all_months_sorted, fill_value=0)
        _pct_v = (d_vals['revenue_usd'] / _sub_monthly_total * 100).fillna(0).values.tolist()
        aoe_chart['traces'].append({
            'name': NAMES.get(sid, sid),
            'y': [round(v, 2) for v in _pct_v],
            'color': COLORS.get(sid, '#666'), 'fillcolor': COLORS.get(sid, '#666')
        })

    _pulse_by_n[str(N)] = {
        'active': sub_active,
        'qr': float(sub_qr),
        'ndr': float(sub_ndr),
        'net_churn': float(sub_net_churn),
        'gross_ret': float(sub_gross_ret),
        'el1_gains': round(float(el1_gains), 0),
        'el1_losses': round(float(el1_losses), 0),
        'el1_coverage': float(el1_coverage),
        'wf': sub_wf,
        'ga_chart': ga_chart,
        'cmgr_chart': cmgr_chart,
        'aoe_chart': aoe_chart,
    }

_pulse_by_n_json = json.dumps(_pulse_by_n)

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

    # Use pre-computed per-company GA from developer_activity
    d_ga = per_company_ga_df[sid]

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

    # Growth Accounting (revenue) — uses canonical GA colors matching Pulse
    f = go.Figure()
    if len(d_ga) > 0:
        f.add_trace(go.Bar(x=d_ga['month'], y=d_ga['retained_revenue'], name='Retained', marker_color=GA_RETAINED, opacity=0.5))
        f.add_trace(go.Bar(x=d_ga['month'], y=d_ga['new_revenue'], name='New', marker_color=GA_NEW))
        f.add_trace(go.Bar(x=d_ga['month'], y=d_ga['expansion_revenue'], name='Expansion', marker_color=GA_EXPANSION))
        f.add_trace(go.Bar(x=d_ga['month'], y=d_ga['resurrected_revenue'], name='Resurrected', marker_color=GA_RESURRECTED))
        f.add_trace(go.Bar(x=d_ga['month'], y=-d_ga['contraction_revenue'], name='Contraction', marker_color=GA_CONTRACTION))
        f.add_trace(go.Bar(x=d_ga['month'], y=-d_ga['churned_revenue'], name='Churned', marker_color=GA_CHURNED))
    else:
        f.add_annotation(text="Insufficient data", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=13, color=MUTED))
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
    if len(d_dev_qr) > 0:
        f.add_trace(go.Scatter(x=d_dev_qr['month'], y=d_dev_qr['dev_quick_ratio'],
            mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False))
        f.add_hline(y=2, line_dash="dash", line_color=SUCCESS, annotation_text="2.0x", annotation_position="top right", annotation_font_color=SUCCESS)
        f.add_hline(y=1, line_dash="dash", line_color=DANGER, annotation_text="1.0x", annotation_position="bottom right", annotation_font_color=DANGER)
        max_qr = d_dev_qr['dev_quick_ratio'].max()
        f.update_yaxes(range=[0, min(max_qr * 1.2, 8)])
    else:
        f.add_annotation(text="No churn data (zero developer churn)", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=13, color=MUTED))
    f.update_layout(**layout('Developer Quick Ratio', h=300))
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

    # Cohort LTV curves (multiple lines, one per onboarding month)
    _d_dev_ltv = dev_activity[dev_activity['startup_id'] == sid].copy()
    if len(_d_dev_ltv) > 5:
        import plotly.express as px
        import numpy as np
        _first_dev_m_ltv = _d_dev_ltv.groupby('dev_id')['month'].min().reset_index()
        _first_dev_m_ltv.columns = ['dev_id', 'first_month']
        _d_dev_ltv = _d_dev_ltv.merge(_first_dev_m_ltv, on='dev_id')
        _d_dev_ltv['age'] = ((_d_dev_ltv['month'] - _d_dev_ltv['first_month']).dt.days / 30.44).round().astype(int)

        # --- Cohort grouping: group into quarters if too many small cohorts ---
        _raw_cohort_sizes = _d_dev_ltv.groupby('first_month')['dev_id'].nunique().reset_index()
        _raw_cohort_sizes.columns = ['first_month', 'cohort_size']
        _small_cohorts = _raw_cohort_sizes[_raw_cohort_sizes['cohort_size'] < 2]
        _needs_quarterly = len(_small_cohorts) > len(_raw_cohort_sizes) * 0.4

        if _needs_quarterly:
            _d_dev_ltv['first_quarter'] = _d_dev_ltv['first_month'].apply(
                lambda d: pd.Timestamp(d.year, ((d.month - 1) // 3) * 3 + 1, 1))
            _d_dev_ltv['cohort_key'] = _d_dev_ltv['first_quarter']
            _d_dev_ltv['age'] = ((_d_dev_ltv['month'] - _d_dev_ltv['first_quarter']).dt.days / 30.44).round().astype(int)
            _d_dev_ltv.loc[_d_dev_ltv['age'] < 0, 'age'] = 0
        else:
            _d_dev_ltv['cohort_key'] = _d_dev_ltv['first_month']

        _cohort_sizes_ltv = _d_dev_ltv.groupby('cohort_key')['dev_id'].nunique().reset_index()
        _cohort_sizes_ltv.columns = ['cohort_key', 'cohort_size']
        # Filter out cohorts with fewer than 2 devs
        _cohort_sizes_ltv = _cohort_sizes_ltv[_cohort_sizes_ltv['cohort_size'] >= 2]
        _d_dev_ltv = _d_dev_ltv[_d_dev_ltv['cohort_key'].isin(_cohort_sizes_ltv['cohort_key'])]

        _cohort_agg_ltv = _d_dev_ltv.groupby(['cohort_key', 'age'])['revenue'].sum().reset_index()
        _cohort_agg_ltv = _cohort_agg_ltv.sort_values(['cohort_key', 'age'])
        _cohort_agg_ltv = _cohort_agg_ltv.merge(_cohort_sizes_ltv, on='cohort_key')
        _cohort_agg_ltv['cum_rev'] = _cohort_agg_ltv.groupby('cohort_key')['revenue'].cumsum()
        _cohort_agg_ltv['cum_ltv_per_dev'] = _cohort_agg_ltv['cum_rev'] / _cohort_agg_ltv['cohort_size']

        _ltv_cohorts = sorted(_cohort_agg_ltv['cohort_key'].unique())
        # Filter out cohorts with fewer than 3 data points
        _ltv_cohorts = [ck for ck in _ltv_cohorts if len(_cohort_agg_ltv[_cohort_agg_ltv['cohort_key'] == ck]) >= 3]

        # Limit to ~10 largest cohorts for cleaner legend
        if len(_ltv_cohorts) > 12:
            _ck_sizes = _cohort_sizes_ltv[_cohort_sizes_ltv['cohort_key'].isin(_ltv_cohorts)].sort_values('cohort_size', ascending=False)
            _top_cohorts = set(_ck_sizes.head(10)['cohort_key'])
        else:
            _top_cohorts = set(_ltv_cohorts)

        _n_coh = len(_ltv_cohorts)
        _qual_colors = px.colors.qualitative.D3 + px.colors.qualitative.Set2 + px.colors.qualitative.Vivid
        _coh_colors = [_qual_colors[i % len(_qual_colors)] for i in range(_n_coh)]

        f = go.Figure()
        _fmt_label = lambda ck: f"Q{((ck.month-1)//3)+1} {ck.year}" if _needs_quarterly else ck.strftime('%Y-%m')
        for ci, ck in enumerate(_ltv_cohorts):
            coh = _cohort_agg_ltv[_cohort_agg_ltv['cohort_key'] == ck].sort_values('age')
            # Ensure cumulative LTV is monotonically non-decreasing
            coh = coh.copy()
            coh['cum_ltv_per_dev'] = coh['cum_ltv_per_dev'].cummax()
            _label = _fmt_label(ck)
            _in_top = ck in _top_cohorts
            f.add_trace(go.Scatter(x=coh['age'], y=coh['cum_ltv_per_dev'],
                mode='lines', name=_label,
                line=dict(width=2, color=_coh_colors[ci]),
                legendgroup=_label,
                showlegend=_in_top,
                hovertemplate=f'{_label}<br>Period %{{x}}: $%{{y:,.0f}}/dev<extra></extra>'))

        # Dashed black average line (thick, prominent)
        _avg_ltv = _cohort_agg_ltv.groupby('age')['cum_ltv_per_dev'].mean().reset_index().sort_values('age')
        _avg_ltv['cum_ltv_per_dev'] = _avg_ltv['cum_ltv_per_dev'].cummax()
        if len(_avg_ltv) > 1:
            f.add_trace(go.Scatter(x=_avg_ltv['age'], y=_avg_ltv['cum_ltv_per_dev'],
                mode='lines', name='Average',
                line=dict(width=3, color='black', dash='dash'),
                hovertemplate='Average<br>Period %{x}: $%{y:,.0f}/dev<extra></extra>'))

        f.update_layout(**layout('Cumulative LTV per Developer by Cohort', h=350))
        f.update_layout(legend=dict(bgcolor='rgba(0,0,0,0)', orientation='v',
            yanchor='top', y=1, xanchor='left', x=1.02, font=dict(size=10),
            tracegroupgap=2))
        f.update_layout(margin=dict(l=55, r=140, t=40, b=40))
        _max_ltv_val = _cohort_agg_ltv['cum_ltv_per_dev'].max() if len(_cohort_agg_ltv) > 0 else 1000
        if _max_ltv_val >= 1000:
            f.update_yaxes(tickprefix='$', tickformat='.1s')
        else:
            f.update_yaxes(tickprefix='$', tickformat=',.0f')
        f.update_xaxes(title_text='period')
        charts['ltv_curve'] = to_div(f)

    # === LTV HEATMAP (Tribe Capital style: red-to-blue, cohort sizes) ===
    d_dev = dev_activity[dev_activity['startup_id'] == sid].copy()
    if len(d_dev) > 5:
        import numpy as np
        from plotly.subplots import make_subplots

        first_dev_m = d_dev.groupby('dev_id')['month'].min().reset_index()
        first_dev_m.columns = ['dev_id', 'first_month']
        d_dev = d_dev.merge(first_dev_m, on='dev_id')
        d_dev['age'] = ((d_dev['month'] - d_dev['first_month']).dt.days / 30.44).round().astype(int)

        # --- Cohort grouping: same quarterly logic as LTV curves ---
        _hm_raw_sizes = d_dev.groupby('first_month')['dev_id'].nunique().reset_index()
        _hm_raw_sizes.columns = ['first_month', 'cohort_size']
        _hm_small = _hm_raw_sizes[_hm_raw_sizes['cohort_size'] < 2]
        _hm_quarterly = len(_hm_small) > len(_hm_raw_sizes) * 0.4

        if _hm_quarterly:
            d_dev['first_quarter'] = d_dev['first_month'].apply(
                lambda d_: pd.Timestamp(d_.year, ((d_.month - 1) // 3) * 3 + 1, 1))
            d_dev['cohort_key'] = d_dev['first_quarter']
            d_dev['age'] = ((d_dev['month'] - d_dev['first_quarter']).dt.days / 30.44).round().astype(int)
            d_dev.loc[d_dev['age'] < 0, 'age'] = 0
        else:
            d_dev['cohort_key'] = d_dev['first_month']

        cohort_sizes_local = d_dev.groupby('cohort_key')['dev_id'].nunique().reset_index()
        cohort_sizes_local.columns = ['cohort_key', 'cohort_size']
        # Filter out cohorts with fewer than 2 devs
        cohort_sizes_local = cohort_sizes_local[cohort_sizes_local['cohort_size'] >= 2]
        d_dev = d_dev[d_dev['cohort_key'].isin(cohort_sizes_local['cohort_key'])]

        cohort_agg = d_dev.groupby(['cohort_key', 'age']).agg(
            active=('dev_id', 'nunique'), rev=('revenue', 'sum')
        ).reset_index()
        cohort_agg = cohort_agg.sort_values(['cohort_key', 'age'])
        cohort_agg = cohort_agg.merge(cohort_sizes_local, on='cohort_key')
        cohort_agg['cum_rev'] = cohort_agg.groupby('cohort_key')['rev'].cumsum()
        cohort_agg['cum_ltv'] = cohort_agg['cum_rev'] / cohort_agg['cohort_size']
        # Ensure cumulative LTV is monotonically non-decreasing
        cohort_agg['cum_ltv'] = cohort_agg.groupby('cohort_key')['cum_ltv'].cummax()
        cohort_agg['retention'] = cohort_agg['active'] / cohort_agg['cohort_size'] * 100

        cohorts_sorted = sorted(cohort_agg['cohort_key'].unique())
        cohorts_sorted = [ck for ck in cohorts_sorted if len(cohort_agg[cohort_agg['cohort_key'] == ck]) >= 3]
        max_age = int(cohort_agg['age'].max()) if len(cohort_agg) > 0 else 0
        ltv_matrix = []
        ret_matrix = []
        cohort_labels = []
        cohort_size_vals = []

        _hm_fmt = lambda ck: f"Q{((ck.month-1)//3)+1} {ck.year}" if _hm_quarterly else ck.strftime('%Y-%m')

        for ck in cohorts_sorted:
            c = cohort_agg[cohort_agg['cohort_key'] == ck].set_index('age')
            cs = cohort_sizes_local[cohort_sizes_local['cohort_key'] == ck]['cohort_size'].iloc[0]
            ltv_row = []
            ret_row = []
            for a in range(max_age + 1):
                if a in c.index:
                    ltv_row.append(round(float(c.loc[a, 'cum_ltv']), 0))
                    ret_row.append(round(float(c.loc[a, 'retention']), 1))
                else:
                    ltv_row.append(None)
                    ret_row.append(None)
            ltv_matrix.append(ltv_row)
            ret_matrix.append(ret_row)
            cohort_labels.append(_hm_fmt(ck))
            cohort_size_vals.append(cs)

        if len(cohorts_sorted) > 0:
            fig_ltv_hm = make_subplots(rows=1, cols=2, column_widths=[0.15, 0.85],
                shared_yaxes=True, horizontal_spacing=0.02)

            # Grey cohort size bars (left)
            fig_ltv_hm.add_trace(go.Bar(
                y=cohort_labels, x=cohort_size_vals, orientation='h',
                marker_color='#9CA3AF', showlegend=False,
                text=[str(v) for v in cohort_size_vals], textposition='auto',
                textfont=dict(size=9),
                hovertemplate='%{y}: %{x} devs<extra></extra>'
            ), row=1, col=1)

            # Text annotations for heatmap cells — "$0.5k", "$2.1k" style
            text_matrix = []
            for row in ltv_matrix:
                text_row = []
                for v in row:
                    if v is None:
                        text_row.append('')
                    elif v >= 1000:
                        text_row.append(f'${v/1000:.1f}k')
                    elif v >= 100:
                        text_row.append(f'${v/1000:.1f}k')
                    else:
                        text_row.append(f'${v:.0f}')
                text_matrix.append(text_row)

            # Cap color scale at 90th percentile rounded to a nice number
            _all_ltv_vals = [v for row in ltv_matrix for v in row if v is not None]
            if _all_ltv_vals:
                _ltv_p90 = float(np.percentile(_all_ltv_vals, 90))
                # Round up to a nice number
                if _ltv_p90 >= 10000:
                    _ltv_cap = float(np.ceil(_ltv_p90 / 5000) * 5000)
                elif _ltv_p90 >= 1000:
                    _ltv_cap = float(np.ceil(_ltv_p90 / 1000) * 1000)
                elif _ltv_p90 >= 100:
                    _ltv_cap = float(np.ceil(_ltv_p90 / 500) * 500)
                else:
                    _ltv_cap = float(np.ceil(_ltv_p90 / 100) * 100)
                _ltv_cap = max(_ltv_cap, 100)
                _ltv_cap_label = f'${_ltv_cap/1000:.0f}k' if _ltv_cap >= 1000 else f'${_ltv_cap:.0f}'
            else:
                _ltv_cap = 1000
                _ltv_cap_label = '$1k'

            # LTV heatmap (right) — RED (low) -> WHITE (mid) -> BLUE (high)
            fig_ltv_hm.add_trace(go.Heatmap(
                z=ltv_matrix, x=list(range(max_age + 1)), y=cohort_labels,
                text=text_matrix, texttemplate='%{text}', textfont=dict(size=10),
                colorscale=[[0, '#DC2626'], [0.15, '#EF4444'], [0.35, '#FCA5A5'],
                            [0.5, '#FFFFFF'],
                            [0.65, '#93C5FD'], [0.85, '#3B82F6'], [1, '#1D4ED8']],
                showscale=True,
                colorbar=dict(title=dict(text='LTV ($)', side='right'), tickprefix='$',
                              tickformat=',.0f', len=0.85, thickness=15),
                hovertemplate='Cohort %{y}<br>Period %{x}<br>LTV: $%{z:,.0f}<extra></extra>',
                zmin=0, zmax=_ltv_cap,
                connectgaps=False,
                xgap=1, ygap=1
            ), row=1, col=2)

            _hm_height = max(400, len(cohorts_sorted) * 32 + 100)
            fig_ltv_hm.update_layout(
                height=_hm_height,
                margin=dict(t=50, b=45, l=10, r=10),
                paper_bgcolor='white', plot_bgcolor='white',
                title=dict(text=f'LTV by Cohort (color scale capped at {_ltv_cap_label})',
                           font=dict(size=14, family='IBM Plex Sans')),
                font=dict(family='IBM Plex Sans, Inter, sans-serif', size=11)
            )
            fig_ltv_hm.update_xaxes(title_text='cohort size', row=1, col=1, showticklabels=False, side='bottom')
            fig_ltv_hm.update_xaxes(title_text='period', row=1, col=2)
            fig_ltv_hm.update_yaxes(autorange='reversed', row=1, col=1)
            charts['ltv_heatmap'] = to_div(fig_ltv_hm, f'ltv-hm-{sid}')

        # Retention Heatmap (same structure, green-to-red)
        if len(cohorts_sorted) > 0:
            ret_text = []
            for row in ret_matrix:
                ret_text.append([f'{v:.0f}%' if v is not None else '' for v in row])

            fig_ret_hm = make_subplots(rows=1, cols=2, column_widths=[0.15, 0.85],
                shared_yaxes=True, horizontal_spacing=0.02)

            fig_ret_hm.add_trace(go.Bar(
                y=cohort_labels, x=cohort_size_vals, orientation='h',
                marker_color='#9CA3AF', showlegend=False
            ), row=1, col=1)

            fig_ret_hm.add_trace(go.Heatmap(
                z=ret_matrix, x=list(range(max_age + 1)), y=cohort_labels,
                text=ret_text, texttemplate='%{text}', textfont=dict(size=10),
                colorscale=[[0, '#DC2626'], [0.5, '#FBBF24'], [1, '#16A34A']],
                showscale=True, colorbar=dict(title='Ret %', ticksuffix='%', len=0.85, thickness=15),
                hovertemplate='Cohort %{y}<br>Period %{x}<br>Retention: %{z:.0f}%<extra></extra>',
                zmin=0, zmax=100,
                connectgaps=False
            ), row=1, col=2)

            fig_ret_hm.update_layout(
                height=max(320, len(cohorts_sorted) * 30 + 90),
                margin=dict(t=50, b=45, l=10, r=10),
                paper_bgcolor='white', plot_bgcolor='white',
                title=dict(text='Developer Retention by Cohort', font=dict(size=14)),
                font=dict(family='Inter, sans-serif', size=11)
            )
            fig_ret_hm.update_xaxes(title_text='cohort size', row=1, col=1, showticklabels=False)
            fig_ret_hm.update_xaxes(title_text='period', row=1, col=2)
            fig_ret_hm.update_yaxes(autorange='reversed', row=1, col=1)
            charts['retention_heatmap'] = to_div(fig_ret_hm, f'ret-hm-{sid}')

    # Revenue retention
    cd_s = cohort_df[cohort_df['startup_id'] == sid].sort_values('months_since')
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
    if len(d_ga) > 0 and 'quick_ratio' in d_ga.columns:
        f.add_trace(go.Scatter(x=d_ga['month'], y=d_ga['quick_ratio'],
            mode='lines+markers', line=dict(color=COLORS[sid], width=2.5), marker=dict(size=5), showlegend=False))
        f.add_hline(y=4, line_dash="dash", line_color=SUCCESS, annotation_text="4.0x Strong", annotation_position="top right", annotation_font_color=SUCCESS)
        f.add_hline(y=1, line_dash="dash", line_color=DANGER, annotation_text="1.0x Flat", annotation_position="bottom right", annotation_font_color=DANGER)
        f.update_yaxes(range=[0, 12])
    else:
        f.add_annotation(text="Insufficient data", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=13, color=MUTED))
    f.update_layout(**layout('Spend Quick Ratio', h=300))
    charts['spend_qr'] = to_div(f)

    # Gross retention (per-company)
    if len(d_ga) > 0 and 'gross_retention_pct' in d_ga.columns:
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

# ============================================================
# COMBINED GA + CMGR CHART (Plotly — replaces static CMGR bars)
# ============================================================
# Revenue Growth Accounting stacked bars + CMGR trailing lines on secondary axis

# === COMBINED: Growth Accounting bars + CMGR lines (dual y-axis) ===
fig_ga_cmgr = go.Figure()

# GA bars — row 1 in legend (legendgroup='ga')
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['retained_revenue'], name='Retained',
    marker_color=GA_RETAINED, opacity=0.5, legendgroup='ga', legendgrouptitle_text='Growth Accounting',
    hovertemplate='Retained: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['new_revenue'], name='New',
    marker_color=GA_NEW, legendgroup='ga',
    hovertemplate='New: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['expansion_revenue'], name='Expansion',
    marker_color=GA_EXPANSION, legendgroup='ga',
    hovertemplate='Expansion: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=agg_rev_ga['resurrected_revenue'], name='Resurrected',
    marker_color=GA_RESURRECTED, legendgroup='ga',
    hovertemplate='Resurrected: $%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=-agg_rev_ga['contraction_revenue'], name='Contraction',
    marker_color=GA_CONTRACTION, legendgroup='ga',
    hovertemplate='Contraction: -$%{y:,.0f}<extra></extra>'))
fig_ga_cmgr.add_trace(go.Bar(x=agg_rev_ga['month'], y=-agg_rev_ga['churned_revenue'], name='Churned',
    marker_color=GA_CHURNED, legendgroup='ga',
    hovertemplate='Churned: -$%{y:,.0f}<extra></extra>'))

# CMGR lines on secondary y-axis — row 2 in legend (legendgroup='cmgr')
months_list = portfolio_tokens.index.tolist()
cmgr3_series, cmgr6_series, cmgr12_series = [], [], []
cmgr_months = []
for i in range(len(months_list)):
    m = months_list[i]
    sub = portfolio_tokens.iloc[:i+1]
    c3 = cmgr(sub, 3) if len(sub) > 6 else None
    c6 = cmgr(sub, 6) if len(sub) > 9 else None
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
            marker=dict(size=5), yaxis='y2',
            legendgroup='cmgr', legendgrouptitle_text='CMGR',
            hovertemplate=f'{name}: %{{y:.1f}}%<extra></extra>'))

fig_ga_cmgr.add_hline(y=0, line=dict(color=DANGER, width=2, dash='solid'), opacity=0.6)

ga_cmgr_layout = layout('Growth Accounting + CMGR', h=420)
ga_cmgr_layout['barmode'] = 'relative'
ga_cmgr_layout['yaxis']['tickprefix'] = '$'
ga_cmgr_layout['yaxis']['tickformat'] = ','
ga_cmgr_layout['yaxis']['title'] = 'Revenue'
ga_cmgr_layout['yaxis']['zeroline'] = True
ga_cmgr_layout['yaxis']['zerolinecolor'] = DANGER
ga_cmgr_layout['yaxis']['zerolinewidth'] = 2

# CMGR y2 axis
stable_cmgr = [v for v in cmgr3_series + cmgr6_series + cmgr12_series if v is not None and abs(v) < 1.0]
if stable_cmgr:
    y2_max = max(stable_cmgr) * 100
    y2_min = min(min(stable_cmgr) * 100, 0)
    y2_pad = max((y2_max - y2_min) * 0.15, 3)
else:
    y2_min, y2_max, y2_pad = 0, 50, 5

ga_cmgr_layout['yaxis2'] = dict(
    overlaying='y', side='right', showgrid=False, zeroline=True,
    zerolinecolor='rgba(59,107,224,0.2)',
    title='CMGR %', ticksuffix='%',
    range=[y2_min - y2_pad, y2_max + y2_pad],
    titlefont=dict(color='#3B6BE0', size=11),
    tickfont=dict(color='#3B6BE0', size=10))

# Legend: two grouped rows
ga_cmgr_layout['legend'] = dict(
    bgcolor='rgba(0,0,0,0)', orientation='h', yanchor='top', y=-0.12,
    xanchor='center', x=0.5, font=dict(size=10),
    traceorder='grouped', groupclick='togglegroup',
    grouptitlefont=dict(size=9, color=MUTED))
ga_cmgr_layout['margin'] = dict(t=40, b=100, l=60, r=60)

fig_ga_cmgr.update_layout(**ga_cmgr_layout)
ga_cmgr_div = to_div(fig_ga_cmgr, 'pulse-ga-cmgr')
ga_div = ga_cmgr_div  # alias

# Deceleration note for inline display
cmgr_note_html = ''
if cmgr3 < cmgr12 and cmgr12 > 0:
    cmgr_note_html = f'<div class="cmgr-note decel">CMGR3 ({cmgr3*100:.1f}%) trails CMGR12 ({cmgr12*100:.1f}%) — growth has <strong>decelerated</strong></div>'
elif cmgr3 > cmgr12 and cmgr12 > 0:
    cmgr_note_html = f'<div class="cmgr-note accel">CMGR3 ({cmgr3*100:.1f}%) leads CMGR12 ({cmgr12*100:.1f}%) — growth is <strong>accelerating</strong></div>'

# Net churn display
net_churn_display = f'{net_churn:.1f}%'
net_churn_note = 'Negative = growing' if net_churn < 0 else 'Positive = shrinking'

# ============================================================
# ELEMENT 1: EXPANSION VS LOSSES + PORTFOLIO COMPOSITION
# ============================================================

# Dollar amounts from latest GA
el1_gains_dollars = latest_ga['new_revenue'] + latest_ga['expansion_revenue'] + latest_ga['resurrected_revenue']
el1_losses_dollars = latest_ga['churned_revenue'] + latest_ga['contraction_revenue']
el1_coverage = el1_gains_dollars / el1_losses_dollars if el1_losses_dollars > 0 else 10.0
el1_max_bar = max(el1_gains_dollars, el1_losses_dollars, 1)
el1_gains_pct = el1_gains_dollars / el1_max_bar * 100
el1_losses_pct = el1_losses_dollars / el1_max_bar * 100
el1_coverage_color = SUCCESS if el1_coverage > 1.0 else DANGER

# Portfolio composition: active / dormant / churned counts
_latest_month = monthly_usage['month'].max()
_3mo_ago = _latest_month - pd.DateOffset(months=3)
_active_count = 0
_dormant_count = 0
_churned_count = 0
for sid in ALL_SIDS:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    latest_rev = u[u['month'] == _latest_month]['revenue_usd'].sum()
    recent_3mo = u[(u['month'] > _3mo_ago) & (u['month'] < _latest_month)]['revenue_usd'].sum()
    if latest_rev > 0:
        _active_count += 1
    elif recent_3mo > 0:
        _dormant_count += 1
    else:
        _churned_count += 1

el1_html = f'''<div class="pulse-panel" id="el1-panel">
    <div class="panel-title">EXPANSION VS LOSSES</div>
    <div class="el1-bar-wrap">
        <div class="el1-track">
            <div class="el1-fill-green" style="width:{el1_gains_pct:.1f}%"></div>
            <div class="el1-fill-red" style="width:{el1_losses_pct:.1f}%"></div>
        </div>
    </div>
    <div class="el1-summary">Gains: ${el1_gains_dollars:,.0f} &middot; Losses: ${el1_losses_dollars:,.0f} &middot; Coverage: <span style="color:{el1_coverage_color};font-weight:600">{el1_coverage:.1f}x</span></div>
    <div class="el1-composition"><span class="el1-dot" style="background:{SUCCESS}"></span> {_active_count} active &nbsp; <span class="el1-dot" style="background:{WARNING}"></span> {_dormant_count} dormant &nbsp; <span class="el1-dot" style="background:{DANGER}"></span> {_churned_count} churned</div>
</div>'''

# ============================================================
# ELEMENT 3: REVENUE SHARE AREA OF EFFECT CHART (Plotly)
# ============================================================

# Aggregate monthly revenue per partner over full 24 months
_rev_by_partner_month = monthly_usage.groupby(['startup_id', 'month'])['revenue_usd'].sum().reset_index()
_all_months = sorted(monthly_usage['month'].unique())

# Sort partners by total revenue — top 7 shown individually, rest collapsed to "Others"
TOP_N_AOE = 7
_partner_total_rev = _rev_by_partner_month.groupby('startup_id')['revenue_usd'].sum().sort_values(ascending=False)
_top_sids = _partner_total_rev.head(TOP_N_AOE).index.tolist()
_other_sids = _partner_total_rev.iloc[TOP_N_AOE:].index.tolist()

# Compute "Others" aggregate
_others_monthly = _rev_by_partner_month[_rev_by_partner_month['startup_id'].isin(_other_sids)].groupby('month')['revenue_usd'].sum().reindex(_all_months, fill_value=0)

# Pre-compute monthly totals for manual percentage calculation
_monthly_total = _rev_by_partner_month.groupby('month')['revenue_usd'].sum().reindex(_all_months, fill_value=0)
_others_pct = (_others_monthly / _monthly_total * 100).fillna(0).values

fig_rev_share = go.Figure()

# Add "Others" first (bottom of stack, grey) — using pre-computed percentages
fig_rev_share.add_trace(go.Scatter(
    x=_all_months, y=_others_pct,
    name=f'Others ({len(_other_sids)})',
    stackgroup='one',
    line=dict(width=0.5, color='#94a3b8'),
    fillcolor='rgba(148,163,184,0.4)',
    hovertemplate=f'Others ({len(_other_sids)}): %{{y:.1f}}%<extra></extra>',
))

# Add top partners (biggest at bottom = most stable, reversed so biggest is first added after Others)
for sid in reversed(_top_sids):
    d = _rev_by_partner_month[_rev_by_partner_month['startup_id'] == sid].set_index('month').reindex(_all_months, fill_value=0)
    _pct_vals = (d['revenue_usd'] / _monthly_total * 100).fillna(0).values
    fig_rev_share.add_trace(go.Scatter(
        x=_all_months, y=_pct_vals,
        name=NAMES[sid],
        stackgroup='one',
        line=dict(width=0.5, color=COLORS[sid]),
        fillcolor=COLORS[sid],
        hovertemplate=f'{NAMES[sid]}: %{{y:.1f}}%<extra></extra>',
    ))

# Add text annotations for top 3 at last month
_last_month = _all_months[-1]
_last_month_rev = _rev_by_partner_month[_rev_by_partner_month['month'] == _last_month].sort_values('revenue_usd', ascending=False)
_top3_last = _last_month_rev.head(3)
_total_last = _last_month_rev['revenue_usd'].sum()
_annot_list = []
_cum_pct = (_others_monthly.iloc[-1] / _total_last * 100) if _total_last > 0 else 0
for sid in reversed(_top_sids):
    rev = _last_month_rev[_last_month_rev['startup_id'] == sid]['revenue_usd'].values
    pct = (rev[0] / _total_last * 100) if len(rev) > 0 and _total_last > 0 else 0
    if sid in _top3_last['startup_id'].values:
        _annot_list.append(dict(
            x=_last_month, y=_cum_pct + pct / 2, yref='y',
            text=f'<b>{NAMES[sid]}</b>',
            showarrow=False, font=dict(size=9, color='white'),
            xanchor='right', xshift=-6,
        ))
    _cum_pct += pct

# Update trace names to include latest % share for the legend
for trace in fig_rev_share.data:
    _trace_name = trace.name
    if _trace_name.startswith('Others'):
        _pct = (_others_monthly.iloc[-1] / _total_last * 100) if _total_last > 0 else 0
        trace.name = f'Others ({len(_other_sids)}): {_pct:.0f}%'
    else:
        _sid_match = [s for s in _top_sids if NAMES.get(s) == _trace_name]
        if _sid_match:
            _rev_val = _last_month_rev[_last_month_rev['startup_id'] == _sid_match[0]]['revenue_usd'].values
            _pct = (_rev_val[0] / _total_last * 100) if len(_rev_val) > 0 and _total_last > 0 else 0
            trace.name = f'{_trace_name}: {_pct:.0f}%'

rev_share_layout = layout('Portfolio Revenue Share', h=280)
rev_share_layout['showlegend'] = True
rev_share_layout['legend'] = dict(
    bgcolor='rgba(0,0,0,0)', orientation='v', yanchor='middle', y=0.5,
    xanchor='left', x=1.02, font=dict(size=10), traceorder='reversed')
rev_share_layout['yaxis']['ticksuffix'] = '%'
rev_share_layout['yaxis']['range'] = [0, 100]
rev_share_layout['margin'] = dict(l=45, r=160, t=40, b=35)
rev_share_layout['hovermode'] = 'x unified'
rev_share_layout['annotations'] = _annot_list
fig_rev_share.update_layout(**rev_share_layout)

rev_share_div = to_div(fig_rev_share, 'pulse-rev-share')

tier1_html = f'''
<div class="pulse-slider-compact">
    <div class="slider-row">
        <div class="slider-label">Partners</div>
        <div class="slider-container-compact">
            <input type="range" id="partner-range" min="1" max="{n_total}" value="{n_total}" step="1">
        </div>
        <div class="slider-value" id="slider-value-label"><span id="slider-count">{n_total}</span> / {n_total}</div>
    </div>
    <div class="slider-presets">
        <button class="slider-preset" data-val="3">Top 3</button>
        <button class="slider-preset" data-val="5">Top 5</button>
        <button class="slider-preset" data-val="10">Top 10</button>
        <button class="slider-preset" data-val="{n_active}">Active ({n_active})</button>
        <button class="slider-preset active" data-val="{n_total}">All ({n_total})</button>
    </div>
</div>
<script>window.__pulse_by_n = {_pulse_by_n_json}; window.__n_active = {n_active}; window.__n_total = {n_total};</script>
<div class="pulse-block" id="pulse-block-main">
    <div class="pulse-cards">
        <div class="pulse-card" data-tip="active-partners">
            <div class="pc-label">ACTIVE PARTNERS</div>
            <div class="pc-value" id="kpi-active">{active_partners}</div>
            <div class="pc-sub">API activity in last 30d</div>
        </div>
        <div class="pulse-card" data-tip="quick-ratio">
            <div class="pc-label">QUICK RATIO</div>
            <div class="pc-value" id="kpi-qr" style="color:{'#16A34A' if portfolio_qr >= 4 else '#CA8A04' if portfolio_qr >= 1 else '#DC2626'}">{portfolio_qr:.1f}x</div>
            <div class="pc-sub">(new+res+exp) / (churn+contr)</div>
            <div class="ndr-bench">
                <div class="ndr-bench-track">
                    <div class="ndr-bench-zone" style="left:0%;width:20%;background:#7f1d1d" title="Shrinking (<1x)"></div>
                    <div class="ndr-bench-zone" style="left:20%;width:20%;background:#b45309" title="Weak (1-2x)"></div>
                    <div class="ndr-bench-zone" style="left:40%;width:20%;background:#ca8a04" title="Moderate (2-3x)"></div>
                    <div class="ndr-bench-zone" style="left:60%;width:20%;background:#15803d" title="Healthy (3-4x)"></div>
                    <div class="ndr-bench-zone" style="left:80%;width:20%;background:#166534" title="Strong (>4x)"></div>
                    <div class="ndr-bench-marker" id="bench-qr-marker" style="left:{max(0, min(100, portfolio_qr / 6 * 100)):.1f}%" title="Portfolio: {portfolio_qr:.1f}x"></div>
                </div>
                <div class="ndr-bench-labels">
                    <span>0x</span>
                    <span style="left:20%">1x</span>
                    <span style="left:40%">2x</span>
                    <span style="left:60%">3x</span>
                    <span style="left:80%">4x</span>
                    <span style="left:100%">6x</span>
                </div>
                <div class="ndr-bench-note">Industry benchmarks · &gt;4x very healthy</div>
            </div>
        </div>
        <div class="pulse-card" data-tip="ndr">
            <div class="pc-label">NET DOLLAR RETENTION</div>
            <div class="pc-value" id="kpi-ndr" style="color:{'#16A34A' if ndr >= 100 else '#DC2626'}">{ndr:.0f}%</div>
            <div class="pc-sub" id="kpi-ndr-sub">{'Expanding' if ndr >= 100 else 'Contracting'} &middot; existing partners</div>
            <div class="ndr-bench">
                <div class="ndr-bench-track">
                    <div class="ndr-bench-zone" style="left:0%;width:25%;background:#1e3a5f" title="Below 25th pctl"></div>
                    <div class="ndr-bench-zone" style="left:25%;width:25%;background:#2563eb" title="25th-50th pctl"></div>
                    <div class="ndr-bench-zone" style="left:50%;width:25%;background:#60a5fa" title="50th-75th pctl"></div>
                    <div class="ndr-bench-zone" style="left:75%;width:25%;background:#93c5fd" title="75th-90th pctl"></div>
                    <div class="ndr-bench-marker" id="bench-ndr-marker" style="left:{max(0, min(100, (ndr - 80) / (180 - 80) * 100)):.1f}%" title="Portfolio: {ndr:.0f}%"></div>
                </div>
                <div class="ndr-bench-labels">
                    <span>80%</span>
                    <span style="left:48%">128</span>
                    <span style="left:69%">149</span>
                    <span style="left:73%">153</span>
                    <span style="left:100%">157+</span>
                </div>
                <div class="ndr-bench-note">Industry benchmarks (P25–P90)</div>
            </div>
        </div>
        <div class="pulse-card" data-tip="gross-retention">
            <div class="pc-label">GROSS RETENTION</div>
            <div class="pc-value" id="kpi-gret" style="color:{'#16A34A' if latest_gross_ret >= 80 else '#CA8A04' if latest_gross_ret >= 60 else '#DC2626'}">{latest_gross_ret:.0f}%</div>
            <div class="pc-sub">30-day rolling</div>
            <div class="ndr-bench">
                <div class="ndr-bench-track">
                    <div class="ndr-bench-zone" style="left:0%;width:30%;background:#7f1d1d" title="Critical (<60%)"></div>
                    <div class="ndr-bench-zone" style="left:30%;width:20%;background:#b45309" title="Watch (60-70%)"></div>
                    <div class="ndr-bench-zone" style="left:50%;width:20%;background:#ca8a04" title="Moderate (70-80%)"></div>
                    <div class="ndr-bench-zone" style="left:70%;width:15%;background:#15803d" title="Healthy (80-90%)"></div>
                    <div class="ndr-bench-zone" style="left:85%;width:15%;background:#166534" title="Strong (>90%)"></div>
                    <div class="ndr-bench-marker" id="bench-gret-marker" style="left:{max(0, min(100, latest_gross_ret)):.1f}%" title="Portfolio: {latest_gross_ret:.0f}%"></div>
                </div>
                <div class="ndr-bench-labels">
                    <span>0%</span>
                    <span style="left:30%">60</span>
                    <span style="left:50%">70</span>
                    <span style="left:70%">80</span>
                    <span style="left:85%">90</span>
                    <span style="left:100%">100</span>
                </div>
                <div class="ndr-bench-note">Industry benchmarks · &gt;80% healthy</div>
            </div>
        </div>
    </div>

    <div class="pulse-panels">
        <div class="pulse-panel">
            <div class="panel-title">GROWTH ACCOUNTING WATERFALL</div>
            <div class="wf-options">
                <div class="wf-option-group">
                    <span class="wf-option-label">Period</span>
                    <button class="wf-pill active" data-period="1M">1M</button>
                    <button class="wf-pill" data-period="3M">3M</button>
                    <button class="wf-pill" data-period="6M">6M</button>
                    <button class="wf-pill" data-period="12M">12M</button>
                    <button class="wf-pill" data-period="YTD">YTD</button>
                    <button class="wf-pill" data-period="All">All</button>
                </div>
                <div class="wf-option-group">
                    <span class="wf-option-label">View</span>
                    <button class="wf-pill active" data-view="bars">Bars</button>
                    <button class="wf-pill" data-view="table">Table</button>
                    <button class="wf-pill" data-view="trend">Trend</button>
                </div>
                <div class="wf-option-group">
                    <span class="wf-option-label">Scope</span>
                    <button class="wf-pill active" data-scope="all">All</button>
                    <button class="wf-pill" data-scope="star">Star</button>
                    <button class="wf-pill" data-scope="strong">Strong</button>
                    <button class="wf-pill" data-scope="fine">Fine</button>
                    <button class="wf-pill" data-scope="declining">Declining</button>
                    <button class="wf-pill" data-scope="churned">Churned</button>
                </div>
            </div>
            <div id="wf-content"></div>
            <script>window.__waterfall_data = {_wf_json_str};</script>
            {el1_html}
        </div>

        <div class="pulse-panel pulse-panel-chart">
            <div class="panel-title">GROWTH ACCOUNTING + CMGR</div>
            <div class="panel-subtitle">Revenue breakdown with compound monthly growth rate. Click a bar to see which partners drove that component.</div>
            {ga_cmgr_div}
            <div class="ga-breakdown-trigger">
                <button class="ga-breakdown-btn" onclick="document.getElementById('ga-breakdown').style.display=document.getElementById('ga-breakdown').style.display==='none'?'block':'none'">View monthly breakdown by partner &rarr;</button>
            </div>
            <div id="ga-breakdown" class="ga-breakdown" style="display:none">
                <div class="ga-dd-header">
                    <div style="display:flex;align-items:center;gap:12px">
                        <span class="ga-dd-title">Growth Accounting by Partner</span>
                        <select id="ga-month-select" class="ga-month-select"></select>
                    </div>
                    <span class="ga-dd-close" onclick="document.getElementById('ga-breakdown').style.display='none'">&times;</span>
                </div>
                <div id="ga-breakdown-body" class="ga-dd-body"></div>
            </div>
            {cmgr_note_html}
        </div>
    </div>
</div>
<script>window.__ga_drilldown = {_ga_drilldown_json};</script>
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
        data-cmgr="{cmgr3_val:.6f}"
        data-qr="{m['avg_qr']:.4f}" data-gret="{m['gross_retention']:.2f}" data-active="{m['last_active_days']}"
        style="cursor:pointer">
        <td><span class="dot-sm" style="background:{COLORS[m['sid']]}"></span>{m['name']} <span class="stage-badge">{m['stage']}</span></td>
        <td class="metric-cell num">{rev_display}</td>
        <td class="metric-cell num">{mau_display}</td>
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

# Build top-5 mini-table for Pulse
top5_rows = ''
sorted_metrics = sorted(company_metrics, key=lambda m: m['latest_mrr'], reverse=True)[:5]
for i, m in enumerate(sorted_metrics):
    sid = m['sid']
    name = NAMES[sid]
    rev = m['latest_mrr']
    devs = m['active_devs']
    cmgr3_val = m['cmgr3']
    cmgr_display = f'{cmgr3_val*100:.1f}%' if cmgr3_val is not None else 'n/a'
    cmgr_color = SUCCESS if cmgr3_val and cmgr3_val > 0.05 else WARNING if cmgr3_val and cmgr3_val > 0 else DANGER
    top5_rows += f'''<tr class="top5-row" data-sid="{sid}" style="cursor:pointer">
        <td style="color:{MUTED};font-size:12px;padding:8px 6px">{i+1}</td>
        <td style="padding:8px 6px;font-weight:600">{name}</td>
        <td class="num" style="padding:8px 6px">${rev:,.0f}</td>
        <td class="num" style="padding:8px 6px">{devs}</td>
        <td class="num" style="padding:8px 6px;color:{cmgr_color}">{cmgr_display}</td>
    </tr>'''

top5_html = f'''
<div style="margin-top:28px;border-top:1px solid {GRID};padding-top:20px">
    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px">
        <div class="panel-title">TOP PARTNERS</div>
        <a href="#" class="view-all-link" onclick="document.querySelector('[data-tab=partners]').click();return false" style="font-size:12px;color:{ACCENT};text-decoration:none">View all partners &rarr;</a>
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
        <thead>
            <tr style="border-bottom:1px solid {GRID}">
                <th style="text-align:left;padding:6px;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;color:{MUTED};font-weight:600;width:30px">#</th>
                <th style="text-align:left;padding:6px;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;color:{MUTED};font-weight:600">Company</th>
                <th style="text-align:right;padding:6px;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;color:{MUTED};font-weight:600">MRR</th>
                <th style="text-align:right;padding:6px;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;color:{MUTED};font-weight:600">Devs</th>
                <th style="text-align:right;padding:6px;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;color:{MUTED};font-weight:600">CMGR-3</th>
            </tr>
        </thead>
        <tbody>{top5_rows}</tbody>
    </table>
</div>'''

rev_share_section = f'''<div class="pulse-block" style="border-bottom:none;margin-bottom:0;padding-bottom:0">
    <div class="pulse-panel pulse-panel-chart" style="border:1px solid {GRID};border-radius:12px">
        {rev_share_div}
    </div>
</div>'''

pulse_content = tier1_html + rev_share_section + tier2_html
partners_content = f'''{tier2_html}
{scoreboard_html}'''

# ============================================================
# CASE STUDIES CONTENT
# ============================================================
CASE_STUDIES = [
    {
        'sid': 'CS01', 'name': 'WriteFlow', 'type': 'Customer-Facing',
        'type_color': '#8B5CF6',
        'tagline': 'AI Writing Assistant',
        'stage': 'Series A', 'hq': 'London, UK',
        'summary': 'Browser-based writing assistant — users draft emails, blog posts, social copy. Freemium + Pro ($12/mo). Every "Generate" click is an API call. Usage scales with consumer adoption.',
        'model_mix': 'Haiku 56% · Sonnet 31% · Opus 13%',
        'expected_ga': 'High churn, high new + resurrected. Volatile Quick Ratio (1.5–2.5×). Consumer behaviour drives seasonality — exam spikes, holiday dips, viral surges.',
        'what_to_watch': 'Churn rate vs new acquisition rate. If churn exceeds new for 2+ months, the product is losing PMF. Model mix shift toward Sonnet signals premium feature adoption.'
    },
    {
        'sid': 'CS02', 'name': 'FinLedger', 'type': 'Developer Tooling',
        'type_color': '#0EA5E9',
        'tagline': 'Internal Engineering Use (Fintech)',
        'stage': 'Seed', 'hq': 'Berlin, Germany',
        'summary': 'Accounting automation startup. Their product isn\'t AI — but their 4 engineers use Claude daily for code review, test generation, and docs. API keys = engineers.',
        'model_mix': 'Sonnet 64% · Haiku 21% · Opus 15%',
        'expected_ga': 'Very high retention (95%+), minimal churn (only if an engineer leaves). Near-zero new (only on hire). Expansion from adding use cases, not users. QR > 3× but slow-moving.',
        'what_to_watch': 'Step-function jumps = new use case adopted. Flat line = stable but no deepening. Any churn at all is a signal (small team, losing 1 of 4 devs is 25% churn).'
    },
    {
        'sid': 'CS03', 'name': 'BrieflyAI', 'type': 'B2B Embedded',
        'type_color': '#F59E0B',
        'tagline': 'Meeting Summarisation Platform',
        'stage': 'Series A', 'hq': 'Amsterdam, Netherlands',
        'summary': 'Records and transcribes meetings, Claude generates structured summaries with action items. Sold per-seat to enterprises. 45 clients, 3K meetings/week.',
        'model_mix': 'Sonnet 72% · Opus 16% · Haiku 11%',
        'expected_ga': 'High retained revenue, step-function expansion (new client wins), very low churn (sticky B2B contracts). Super-linear LTV as clients add seats. QR 3–5×.',
        'what_to_watch': 'Client acquisition cadence — are step-functions getting bigger or smaller? Model mix trending Opus = handling more complex meetings. Any churn cliff = lost enterprise client, investigate immediately.'
    }
]

cs_cards_html = ''
for cs in CASE_STUDIES:
    sid = cs['sid']
    ch = startup_charts.get(sid, {})
    m = next((x for x in company_metrics if x['sid'] == sid), None)

    # Get GA chart if available
    ga_chart_html = f'<div class="card">{ch["growth_acct"]}</div>' if 'growth_acct' in ch else ''

    # Revenue chart
    rev_chart_html = f'<div class="card">{ch["revenue"]}</div>' if 'revenue' in ch else ''

    # LTV charts — CS02 gets a text note instead of charts
    if sid == 'CS02':
        ltv_section_html = '''<div class="cs-section">
    <div class="cs-section-title">Lifetime Value</div>
    <p class="cs-section-text">With only 4\u20135 developers and near-zero churn, cohort analysis is not meaningful for FinLedger. Their value story is better read through the growth accounting section \u2014 specifically the step-function expansions when they adopt new Claude use cases (CI pipeline at month 9, documentation at month 16).</p>
</div>'''
    else:
        ltv_curve_html = f'<div class="card">{ch["ltv_curve"]}</div>' if 'ltv_curve' in ch else ''
        ltv_heatmap_html = f'<div class="card">{ch["ltv_heatmap"]}</div>' if 'ltv_heatmap' in ch else ''
        ltv_section_html = f'''<div class="cs-section">
                <div class="cs-section-title">LTV Cohort Analysis</div>
            </div>
            <div class="cs-charts">
                {ltv_curve_html}
                {ltv_heatmap_html}
            </div>'''

    latest_rev = m['latest_mrr'] if m else 0
    cmgr3 = m['cmgr3'] if m and m['cmgr3'] else 0
    devs = m['active_devs'] if m else 0

    cs_cards_html += f'''
    <div class="cs-card" style="border-top:3px solid {cs['type_color']}">
        <div class="cs-header-clickable" onclick="toggleCaseStudy(this)">
            <div class="cs-header-left">
                <span class="cs-chevron">&#x25BC;</span>
                <span class="cs-name">{cs['name']}</span>
                <span class="cs-type-badge" style="background:{cs['type_color']}">{cs['type']}</span>
                <span class="cs-tagline-inline">{cs['tagline']}</span>
            </div>
            <span class="cs-meta">{cs['stage']} &middot; {cs['hq']}</span>
        </div>

        <div class="cs-body">
            <p class="cs-desc">{cs['summary']}</p>

            <div class="cs-kpis">
                <div class="cs-kpi"><div class="cs-kpi-label">MRR</div><div class="cs-kpi-value">${latest_rev:,.0f}</div></div>
                <div class="cs-kpi"><div class="cs-kpi-label">CMGR-3</div><div class="cs-kpi-value">{cmgr3*100:.1f}%</div></div>
                <div class="cs-kpi"><div class="cs-kpi-label">Active Devs</div><div class="cs-kpi-value">{devs}</div></div>
                <div class="cs-kpi"><div class="cs-kpi-label">Model Mix</div><div class="cs-kpi-value" style="font-size:11px">{cs['model_mix']}</div></div>
            </div>

            <div class="cs-section">
                <div class="cs-section-title">Expected GA Profile</div>
                <p class="cs-section-text">{cs['expected_ga']}</p>
            </div>

            <div class="cs-section">
                <div class="cs-section-title">What to Watch</div>
                <p class="cs-section-text">{cs['what_to_watch']}</p>
            </div>

            <div class="cs-charts">
                {ga_chart_html}
                {rev_chart_html}
            </div>

            {ltv_section_html}

            <div class="cs-link" onclick="event.stopPropagation(); showDetail('{sid}')">View full analysis &rarr;</div>
        </div>
    </div>
    '''

casestudies_content = f'''
<div class="section-header" style="margin-top:0">CASE STUDIES</div>
<p class="pl-subtitle" style="margin-bottom:20px">Three partner archetypes demonstrating how growth accounting profiles differ by use case. Based on the <a href="https://tribecap.co/essays/a-quantitative-approach-to-product-market-fit" style="color:{MUTED};text-decoration:underline" target="_blank">Tribe Capital PMF framework</a>.</p>
{cs_cards_html}
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
.tab-detail {{ font-weight:600; }}
.tab-detail .detail-back {{ color:{ACCENT}; margin-right:4px; }}
.tab-detail:hover .detail-back {{ color:{TEXT}; }}

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

/* ========== PARTNER RANGE SLIDER ========== */
.pulse-slider-compact {{ padding:8px 0 12px; margin-bottom:4px; display:flex; flex-direction:column; align-items:center; }}
.slider-row {{ display:flex; align-items:center; gap:10px; width:33%; min-width:200px; }}
.slider-label {{ font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; color:{MUTED}; white-space:nowrap; }}
.slider-container-compact {{ flex:1; min-width:0; }}
.slider-container-compact input[type=range] {{ -webkit-appearance:none; appearance:none; width:100%; height:3px; background:{GRID}; border-radius:2px; outline:none; cursor:pointer; }}
.slider-container-compact input[type=range]::-webkit-slider-thumb {{ -webkit-appearance:none; width:14px; height:14px; border-radius:50%; background:{ACCENT}; cursor:pointer; border:2px solid #fff; box-shadow:0 1px 3px rgba(0,0,0,0.15); transition:transform 0.1s ease; }}
.slider-container-compact input[type=range]::-webkit-slider-thumb:hover {{ transform:scale(1.2); }}
.slider-container-compact input[type=range]::-moz-range-thumb {{ width:14px; height:14px; border-radius:50%; background:{ACCENT}; cursor:pointer; border:2px solid #fff; }}
.slider-container-compact input[type=range]::-webkit-slider-runnable-track {{ height:3px; border-radius:2px; }}
.slider-container-compact input[type=range]::-moz-range-track {{ height:3px; border-radius:2px; background:{GRID}; }}
.slider-value {{ font-size:11px; color:{TEXT}; font-weight:500; white-space:nowrap; font-variant-numeric:tabular-nums; min-width:40px; text-align:right; }}
.slider-value #slider-count {{ font-weight:700; color:{ACCENT}; }}
.slider-presets {{ display:flex; gap:6px; margin-top:6px; justify-content:center; }}
.slider-preset {{ padding:3px 10px; font-size:10px; font-family:inherit; border:1px solid {GRID}; border-radius:12px; background:transparent; color:{MUTED}; cursor:pointer; transition:all 0.15s; }}
.slider-preset:hover {{ border-color:{MUTED}; color:{TEXT}; }}
.slider-preset.active {{ background:rgba(59,130,246,0.1); border-color:{ACCENT}; color:{ACCENT}; font-weight:600; }}

/* ========== GA BREAKDOWN ========== */
.ga-breakdown-trigger {{ text-align:center; margin-top:10px; }}
.ga-breakdown-btn {{ background:transparent; border:1px solid {GRID}; border-radius:6px; padding:6px 16px; font-size:11px; font-family:inherit; color:{MUTED}; cursor:pointer; transition:all 0.15s; }}
.ga-breakdown-btn:hover {{ border-color:{ACCENT}; color:{ACCENT}; }}
.ga-breakdown {{ background:{CARD}; border:1px solid {GRID}; border-radius:8px; margin-top:12px; padding:14px 18px; animation:fadeIn 0.2s ease; }}
.ga-month-select {{ padding:4px 8px; font-size:11px; font-family:inherit; border:1px solid {GRID}; border-radius:4px; background:{BG}; color:{TEXT}; cursor:pointer; }}
.ga-dd-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
.ga-dd-title {{ font-size:12px; font-weight:600; color:{TEXT}; }}
.ga-dd-close {{ font-size:18px; color:{MUTED}; cursor:pointer; line-height:1; padding:0 4px; }}
.ga-dd-close:hover {{ color:{TEXT}; }}
.ga-dd-body {{ font-size:12px; }}
.ga-dd-table {{ width:100%; border-collapse:collapse; }}
.ga-dd-table th {{ text-align:left; padding:4px 8px; font-size:10px; text-transform:uppercase; letter-spacing:0.04em; color:{MUTED}; font-weight:600; border-bottom:1px solid {GRID}; }}
.ga-dd-table th:last-child {{ text-align:right; }}
.ga-dd-table td {{ padding:5px 8px; border-bottom:1px solid rgba(0,0,0,0.04); }}
.ga-dd-table td:last-child {{ text-align:right; font-variant-numeric:tabular-nums; font-weight:500; }}
.ga-dd-table tr:hover {{ background:rgba(0,0,0,0.02); cursor:pointer; }}
.ga-dd-empty {{ color:{MUTED}; font-style:italic; font-size:11px; padding:8px 0; }}

/* ========== TIER 1: PULSE BLOCK ========== */
.pulse-block {{ margin-bottom:40px; padding-bottom:32px; border-bottom:1px solid {GRID}; }}

.pulse-cards {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin-bottom:20px; }}
.pulse-card {{ background:{CARD}; border:1px solid {GRID}; border-radius:10px; padding:18px 20px; transition:border-color 0.2s ease, box-shadow 0.2s ease; }}
.pulse-card:hover {{ border-color:#d4d0da; box-shadow:0 1px 4px rgba(0,0,0,0.04); }}
.pc-label {{ font-size:10px; text-transform:uppercase; letter-spacing:0.05em; color:{MUTED}; font-weight:600; margin-bottom:4px; }}
.pc-value {{ font-size:24px; font-weight:700; color:{TEXT}; font-variant-numeric:tabular-nums; }}
.pc-sub {{ font-size:11px; color:{MUTED}; margin-top:3px; }}

/* NDR Benchmark bar */
.ndr-bench {{ margin-top:8px; }}
.ndr-bench-track {{ position:relative; height:6px; border-radius:3px; overflow:visible; display:flex; }}
.ndr-bench-zone {{ height:100%; }}
.ndr-bench-zone:first-child {{ border-radius:3px 0 0 3px; }}
.ndr-bench-zone:last-of-type {{ border-radius:0 3px 3px 0; }}
.ndr-bench-marker {{ position:absolute; top:-3px; width:3px; height:12px; background:{TEXT}; border-radius:2px; transform:translateX(-50%); z-index:2; }}
.ndr-bench-labels {{ display:flex; justify-content:space-between; position:relative; margin-top:3px; font-size:9px; color:{DIM}; font-variant-numeric:tabular-nums; }}
.ndr-bench-labels span {{ position:relative; }}
.ndr-bench-note {{ font-size:8px; color:{DIM}; margin-top:2px; text-align:center; font-style:italic; }}

.pulse-panels {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.pulse-panel {{ background:#fff; border:1px solid {GRID}; border-radius:12px; padding:22px 24px; }}
.pulse-panel-chart {{ padding:14px 10px 6px; overflow:hidden; }}

/* Insights row */
.pulse-insights-row {{ display:grid; grid-template-columns:1fr; gap:16px; margin-bottom:20px; }}

/* Element 1: Expansion vs Losses */
.el1-bar-wrap {{ margin:14px 0 12px; }}
.el1-track {{ height:18px; background:{BORDER_SUBTLE}; border-radius:3px; display:flex; overflow:hidden; }}
.el1-fill-green {{ height:100%; background:{SUCCESS}; border-radius:3px 0 0 3px; transition:width 0.4s ease; }}
.el1-fill-red {{ height:100%; background:{DANGER}; margin-left:auto; border-radius:0 3px 3px 0; transition:width 0.4s ease; }}
.el1-summary {{ font-size:12px; color:{DIM}; margin-bottom:10px; }}
.el1-composition {{ font-size:12px; color:{MUTED}; display:flex; align-items:center; gap:4px; padding-top:10px; border-top:1px solid {GRID}; }}
.el1-dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; flex-shrink:0; }}

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

/* Interactive waterfall options */
.wf-options {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:16px; align-items:center; }}
.wf-option-group {{ display:flex; align-items:center; gap:4px; flex-wrap:wrap; }}
.wf-option-label {{ font-size:9px; font-weight:700; color:{DIM}; text-transform:uppercase; letter-spacing:0.06em; margin-right:2px; }}
.wf-pill {{ padding:3px 9px; font-size:11px; font-weight:500; border:1px solid {GRID}; border-radius:12px; background:transparent; color:{MUTED}; cursor:pointer; transition:all 0.15s ease; font-family:inherit; line-height:1.3; }}
.wf-pill:hover {{ border-color:#c4c0cc; color:{DIM}; }}
.wf-pill.active {{ background:{ACCENT}; color:#fff; border-color:{ACCENT}; }}

/* Waterfall table view */
.wf-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
.wf-table th {{ text-align:right; padding:6px 10px; font-size:10px; text-transform:uppercase; letter-spacing:0.04em; color:{MUTED}; font-weight:600; border-bottom:1px solid {GRID}; }}
.wf-table th:first-child {{ text-align:left; }}
.wf-table td {{ padding:6px 10px; text-align:right; color:{DIM}; border-bottom:1px solid {BORDER_SUBTLE}; }}
.wf-table td:first-child {{ text-align:left; font-weight:500; color:{TEXT}; }}
.wf-table tr.wf-table-net td {{ font-weight:600; border-top:2px solid {GRID}; }}
.wf-table .wf-table-sep td {{ padding:0; height:1px; border:none; background:{BORDER_SUBTLE}; }}

/* Waterfall trend view */
.wf-trend-row {{ display:grid; grid-template-columns:100px 70px 1fr 60px; align-items:center; gap:8px; padding:5px 0; }}
.wf-trend-label {{ font-size:12px; color:{DIM}; text-align:right; }}
.wf-trend-spark {{ text-align:center; }}
.wf-trend-bar {{ }}
.wf-trend-val {{ font-size:12px; font-weight:500; text-align:right; }}

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

/* Metric cell color coding */
.metric-cell {{ font-weight:500; font-variant-numeric:tabular-nums; }}
.metric-cell.metric-green {{ color:{SUCCESS}; }}
.metric-cell.metric-amber {{ color:{WARNING}; }}
.metric-cell.metric-red {{ color:{DANGER}; }}

html {{ scroll-behavior:smooth; }}

/* Case Studies */
.cs-card {{ background:{CARD}; border-radius:12px; padding:0; margin-bottom:16px; overflow:hidden; }}
.cs-header-clickable {{ display:flex; justify-content:space-between; align-items:center; padding:16px 24px; cursor:pointer; user-select:none; transition:background 0.15s; }}
.cs-header-clickable:hover {{ background:rgba(0,0,0,0.08); }}
.cs-header-left {{ display:flex; align-items:center; gap:10px; }}
.cs-chevron {{ font-size:12px; color:{MUTED}; transition:transform 0.25s cubic-bezier(0.22,1,0.36,1); display:inline-block; }}
.cs-card.collapsed .cs-chevron {{ transform:rotate(-90deg); }}
.cs-name {{ font-size:16px; font-weight:700; color:{TEXT}; }}
.cs-type-badge {{ font-size:10px; font-weight:700; padding:3px 10px; border-radius:10px; color:#fff; letter-spacing:0.03em; }}
.cs-tagline-inline {{ font-size:12px; color:{DIM}; font-style:italic; }}
.cs-meta {{ font-size:12px; color:{MUTED}; flex-shrink:0; }}
.cs-body {{ padding:0 24px 24px; max-height:3000px; overflow:hidden; transition:max-height 0.4s cubic-bezier(0.22,1,0.36,1), padding 0.3s, opacity 0.25s; opacity:1; }}
.cs-card.collapsed .cs-body {{ max-height:0; padding:0 24px; opacity:0; }}
.cs-desc {{ font-size:12px; color:{DIM}; line-height:1.6; margin-bottom:16px; }}
.cs-kpis {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:16px; }}
.cs-kpi {{ background:rgba(0,0,0,0.15); border-radius:8px; padding:10px 14px; }}
.cs-kpi-label {{ font-size:10px; text-transform:uppercase; letter-spacing:0.04em; color:{MUTED}; font-weight:600; margin-bottom:2px; }}
.cs-kpi-value {{ font-size:18px; font-weight:700; color:{TEXT}; font-variant-numeric:tabular-nums; }}
.cs-section {{ margin-bottom:12px; }}
.cs-section-title {{ font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:{MUTED}; font-weight:700; margin-bottom:4px; }}
.cs-section-text {{ font-size:12px; color:{DIM}; line-height:1.6; }}
.cs-charts {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:16px 0; }}
.cs-link {{ font-size:12px; color:{MUTED}; cursor:pointer; text-align:right; padding-top:8px; border-top:1px solid {GRID}; }}
.cs-link:hover {{ color:{TEXT}; text-decoration:underline; }}

@media (max-width:900px) {{
    .cs-kpis {{ grid-template-columns:1fr 1fr; }}
    .cs-charts {{ grid-template-columns:1fr; }}
}}

@media (max-width:1100px) {{
    .pulse-panels {{ grid-template-columns:1fr; }}
    .pulse-insights-row {{ grid-template-columns:1fr; }}
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
    .wf-options {{ gap:8px; }}
    .wf-option-group {{ gap:3px; }}
    .wf-pill {{ padding:2px 7px; font-size:10px; }}
    .wf-trend-row {{ grid-template-columns:72px 60px 1fr 52px; }}
    .pl-subtitle {{ font-size:11px; }}
    .chart-desc {{ font-size:10px; }}
    .perf-table td {{ padding:8px 10px; font-size:12px; }}
    .perf-table th {{ padding:8px 10px; font-size:9px; }}
    .scoreboard-table td {{ padding:7px 8px; font-size:11px; }}
    .scoreboard-table th {{ padding:7px 8px; font-size:9px; }}
}}

@media (max-width:480px) {{
    .pulse-slider {{ flex-wrap:wrap; gap:8px; }}
    .slider-label {{ font-size:10px; }}
    .slider-value {{ font-size:11px; min-width:auto; }}
    .slider-ticks .tick {{ font-size:8px; }}
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
            <div class="subtitle">Partner Consumption Analytics</div>
        </div>
        <span class="meta">Ongun Ozdemir &middot; Mar 2026 &middot; Synthetic data</span>
    </div>
</div>

<div class="assumptions">
    <div class="a-item"><strong>$10/1M tokens</strong> blended (Sonnet/Opus/Haiku, 5:1 I/O)</div>
    <div class="a-item"><strong>65% gross margin</strong> est.</div>
    <div class="a-item"><strong>24 months</strong> Jan 2024 &ndash; Dec 2025</div>
</div>

<div class="tabs">
    <div class="tab active" data-tab="pulse">Pulse</div>
    <div class="tab" data-tab="partners">Partners</div>
    <div class="tab" data-tab="casestudies">Case Studies</div>
    <div class="tab tab-detail" data-tab="detail" style="display:none"><span class="detail-back">&larr;</span> <span class="detail-name"></span></div>
</div>

<div class="content">
    <div class="tab-panel active" id="panel-pulse">
        {pulse_content}
    </div>
    <div class="tab-panel" id="panel-partners">
        {partners_content}
    </div>
    <div class="tab-panel" id="panel-casestudies">
        {casestudies_content}
    </div>
    <div class="tab-panel" id="panel-detail">
        {''.join(f'<div class="detail-view" id="detail-{sid.lower()}" style="display:none">{startup_tab_html(sid)}</div>' for sid in ALL_SIDS)}
    </div>
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

// Case study collapse/expand
function toggleCaseStudy(header) {{
    const card = header.closest('.cs-card');
    card.classList.toggle('collapsed');
    if (!card.classList.contains('collapsed')) {{
        setTimeout(() => resizePlotlyCharts(card), 120);
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

// ======== THREE-TIER TAB NAVIGATION ========
function showPanel(tabName) {{
    document.querySelectorAll('.tab').forEach(t => {{
        if (t.dataset.tab === tabName) t.classList.add('active');
        else t.classList.remove('active');
    }});
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById('panel-' + tabName);
    if (panel) {{
        panel.classList.add('active');
        setTimeout(() => resizePlotlyCharts(panel), 80);
    }}
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

function showPartnerDetail(sid) {{
    const detailTab = document.querySelector('.tab-detail');
    const detailName = detailTab.querySelector('.detail-name');
    // Hide all detail views, show the selected one
    document.querySelectorAll('.detail-view').forEach(v => v.style.display = 'none');
    const view = document.getElementById('detail-' + sid.toLowerCase());
    if (view) {{
        view.style.display = 'block';
        const name = view.querySelector('.hero-name');
        detailName.textContent = name ? name.textContent : sid;
    }}
    detailTab.style.display = '';
    showPanel('detail');
    setTimeout(() => {{
        const panel = document.getElementById('panel-detail');
        resizePlotlyCharts(panel);
    }}, 120);
}}

// Top-level tab clicks
document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', (e) => {{
        const tabName = tab.dataset.tab;
        if (tabName === 'detail') {{
            // Back button: go to Partners
            showPanel('partners');
            tab.style.display = 'none';
            return;
        }}
        // Hide detail tab when switching to Pulse or Partners
        document.querySelector('.tab-detail').style.display = 'none';
        showPanel(tabName);
    }});
}});

// Partner list row click -> Tier 3 detail
document.querySelectorAll('.perf-row, .top5-row').forEach(row => {{
    row.addEventListener('click', () => {{
        const sid = row.dataset.sid;
        if (sid) showPartnerDetail(sid);
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

    // Excluded archetypes set (empty = show all)
    const excludedArchs = new Set();
    let searchTerm = '';
    let sortCol = 'revenue';
    let sortDir = 'desc';

    // Highlight default sort column
    (function() {{
        const th = table.querySelector('.sortable[data-sort="revenue"]');
        if (th) {{
            th.classList.add('sort-desc');
            th.querySelector('.sort-icon').textContent = '↓';
        }}
    }})();

    function applyFilters() {{
        let visible = 0;
        rows.forEach(row => {{
            const name = row.dataset.name || '';
            const arch = row.dataset.arch || '';
            const matchSearch = !searchTerm || name.includes(searchTerm.toLowerCase());
            const matchArch = !excludedArchs.has(arch);
            const show = matchSearch && matchArch;
            row.style.display = show ? '' : 'none';
            if (show) visible++;
        }});
        if (countEl) countEl.textContent = visible;
    }}

    function updateAllChip() {{
        const allChip = document.querySelector('.arch-chip[data-arch="all"]');
        if (allChip) allChip.classList.toggle('active', excludedArchs.size === 0);
    }}

    // Search
    if (searchInput) {{
        searchInput.addEventListener('input', (e) => {{
            searchTerm = e.target.value;
            applyFilters();
        }});
    }}

    // Archetype filter chips — toggle to EXCLUDE
    chips.forEach(chip => {{
        chip.addEventListener('click', () => {{
            const arch = chip.dataset.arch;
            if (arch === 'all') {{
                // Reset: clear all exclusions
                excludedArchs.clear();
                chips.forEach(c => c.classList.add('active'));
            }} else {{
                if (excludedArchs.has(arch)) {{
                    // Re-include
                    excludedArchs.delete(arch);
                    chip.classList.add('active');
                }} else {{
                    // Exclude
                    excludedArchs.add(arch);
                    chip.classList.remove('active');
                }}
            }}
            updateAllChip();
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

// ======== INTERACTIVE WATERFALL ========
(function() {{
    const WF = window.__waterfall_data;
    if (!WF) return;
    const GAIN = '{GAIN}';
    const LOSS = '{LOSS}';
    const SUCCESS_C = '{SUCCESS}';
    const DANGER_C = '{DANGER}';
    const MUTED_C = '{MUTED}';
    const TEXT_C = '{TEXT}';
    const DIM_C = '{DIM}';
    const CARD_C = '{CARD}';
    const GRID_C = '{GRID}';
    const BORDER_C = '{BORDER_SUBTLE}';

    let curPeriod = '1M', curView = 'bars', curScope = 'all';

    const container = document.getElementById('wf-content');
    if (!container) return;

    // Pill click handlers
    document.querySelectorAll('.wf-pill[data-period]').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.wf-pill[data-period]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            curPeriod = btn.dataset.period;
            render();
        }});
    }});
    document.querySelectorAll('.wf-pill[data-view]').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.wf-pill[data-view]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            curView = btn.dataset.view;
            render();
        }});
    }});
    document.querySelectorAll('.wf-pill[data-scope]').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.wf-pill[data-scope]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            curScope = btn.dataset.scope;
            render();
        }});
    }});

    function sign(v, isLoss) {{ return isLoss ? '-' : '+'; }}
    function fmt(v) {{ return Math.abs(v).toFixed(1); }}

    function sparkline(data, color) {{
        if (!data || data.length < 2) return '';
        const w = 60, h = 16;
        const vals = data.map(v => Math.abs(v));
        const mx = Math.max(...vals, 0.01);
        const pts = data.map((v, i) => {{
            const x = i * w / (data.length - 1);
            const y = h / 2 - (v / mx) * (h / 2 - 1);
            return x.toFixed(1) + ',' + y.toFixed(1);
        }}).join(' ');
        return '<svg width="' + w + '" height="' + h + '" style="vertical-align:middle"><polyline points="' + pts + '" fill="none" stroke="' + color + '" stroke-width="1.5"/></svg>';
    }}

    function deltaArrow(current, avg, isLoss) {{
        let delta;
        if (isLoss) {{
            delta = avg - current; // less loss = improving
        }} else {{
            delta = current - avg; // more gain = improving
        }}
        if (delta > 0.5) return ['↑', SUCCESS_C];
        if (delta < -0.5) return ['↓', DANGER_C];
        return ['→', MUTED_C];
    }}

    function renderBars(d) {{
        const components = [
            ['New', d.new, d.avg_new, GAIN, false],
            ['Expansion', d.expansion, d.avg_expansion, GAIN, false],
            ['Resurrected', d.resurrected, d.avg_resurrected, GAIN, false],
            ['_sep'],
            ['Contraction', d.contraction, d.avg_contraction, LOSS, true],
            ['Churned', d.churned, d.avg_churned, LOSS, true],
            ['_sep'],
            ['Net Growth', d.net, d.avg_net, null, false],
        ];
        const maxVal = Math.max(
            Math.abs(d.new), Math.abs(d.expansion), Math.abs(d.resurrected),
            Math.abs(d.contraction), Math.abs(d.churned), Math.abs(d.net), 0.1
        );
        let html = '<div class="waterfall-rows">';
        for (const c of components) {{
            if (c[0] === '_sep') {{
                html += '<div class="wf-divider"></div>';
                continue;
            }}
            const [label, val, avg, color, isLoss] = c;
            const isNet = label === 'Net Growth';
            const barColor = isNet ? (val >= 0 ? GAIN : LOSS) : color;
            const w = Math.abs(val) / maxVal * 100;
            const aw = Math.abs(avg) / maxVal * 100;
            const s = isLoss ? '-' : '+';
            const [arrow, arrowColor] = deltaArrow(val, avg, isLoss);
            const netSign = isNet ? (val >= 0 ? '+' : '') : s;
            html += '<div class="waterfall-row' + (isNet ? ' wf-net' : '') + '">';
            html += '<span class="wf-label">' + label + '</span>';
            html += '<div class="waterfall-bar"><div class="wf-track">';
            html += '<div class="wf-fill" style="width:' + w.toFixed(1) + '%;background:' + barColor + '"></div>';
            html += '<div class="wf-avg-marker" style="left:' + aw.toFixed(1) + '%" title="Avg: ' + s + fmt(avg) + '%"></div>';
            html += '</div></div>';
            html += '<span class="wf-value" style="color:' + barColor + (isNet ? ';font-weight:600' : '') + '">' + netSign + fmt(val) + '%</span>';
            html += '<span class="wf-delta" style="color:' + arrowColor + '">' + arrow + '</span>';
            html += '</div>';
        }}
        html += '</div>';
        html += '<div class="wf-legend">';
        html += '<span class="wf-legend-label">KEY</span>';
        html += '<span class="wf-legend-item"><span class="wf-dot" style="background:' + GAIN + '"></span>Gains</span>';
        html += '<span class="wf-legend-item"><span class="wf-dot" style="background:' + LOSS + '"></span>Losses</span>';
        html += '<span class="wf-legend-item"><span class="wf-avg-dot"></span>Period avg</span>';
        html += '<span class="wf-legend-item"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:transparent;border:1.5px solid ' + MUTED_C + '"></span>↑↓ vs avg</span>';
        html += '</div>';
        return html;
    }}

    function renderTable(d) {{
        const rows = [
            ['New', d.new, d.avg_new, false],
            ['Expansion', d.expansion, d.avg_expansion, false],
            ['Resurrected', d.resurrected, d.avg_resurrected, false],
            ['_sep'],
            ['Contraction', d.contraction, d.avg_contraction, true],
            ['Churned', d.churned, d.avg_churned, true],
            ['_sep'],
            ['Net Growth', d.net, d.avg_net, false],
        ];
        let html = '<table class="wf-table"><thead><tr><th style="text-align:left">Component</th><th>Current</th><th>Avg</th><th>Δ</th></tr></thead><tbody>';
        for (const r of rows) {{
            if (r[0] === '_sep') {{
                html += '<tr class="wf-table-sep"><td colspan="4"></td></tr>';
                continue;
            }}
            const [label, val, avg, isLoss] = r;
            const isNet = label === 'Net Growth';
            const s = isLoss ? '-' : '+';
            const netSign = isNet ? (val >= 0 ? '+' : '') : s;
            const avgSign = isNet ? (avg >= 0 ? '+' : '') : s;
            const [arrow, arrowColor] = deltaArrow(val, avg, isLoss);
            const color = isNet ? (val >= 0 ? GAIN : LOSS) : (isLoss ? LOSS : GAIN);
            html += '<tr' + (isNet ? ' class="wf-table-net"' : '') + '>';
            html += '<td>' + label + '</td>';
            html += '<td style="color:' + color + '">' + netSign + fmt(val) + '%</td>';
            html += '<td style="color:' + MUTED_C + '">' + avgSign + fmt(avg) + '%</td>';
            html += '<td style="color:' + arrowColor + '">' + arrow + '</td>';
            html += '</tr>';
        }}
        html += '</tbody></table>';
        return html;
    }}

    function renderTrend(d) {{
        const trends = d.trends || {{}};
        const rows = [
            ['New', 'new', GAIN, false],
            ['Expansion', 'expansion', GAIN, false],
            ['Resurrected', 'resurrected', GAIN, false],
            ['Contraction', 'contraction', LOSS, true],
            ['Churned', 'churned', LOSS, true],
            ['Net Growth', 'net', null, false],
        ];
        const maxVal = Math.max(
            Math.abs(d.new), Math.abs(d.expansion), Math.abs(d.resurrected),
            Math.abs(d.contraction), Math.abs(d.churned), Math.abs(d.net), 0.1
        );
        let html = '<div style="display:flex;flex-direction:column;gap:4px">';
        for (const [label, key, color, isLoss] of rows) {{
            const val = d[key];
            const barColor = key === 'net' ? (val >= 0 ? GAIN : LOSS) : color;
            const s = isLoss ? '-' : (key === 'net' ? (val >= 0 ? '+' : '') : '+');
            const trendData = trends[key] || [];
            const w = Math.abs(val) / maxVal * 100;
            html += '<div class="wf-trend-row">';
            html += '<span class="wf-trend-label"' + (key === 'net' ? ' style="font-weight:600;color:' + TEXT_C + '"' : '') + '>' + label + '</span>';
            html += '<span class="wf-trend-spark">' + sparkline(trendData, barColor) + '</span>';
            html += '<div class="wf-trend-bar"><div class="wf-track"><div class="wf-fill" style="width:' + w.toFixed(1) + '%;background:' + barColor + '"></div></div></div>';
            html += '<span class="wf-trend-val" style="color:' + barColor + '">' + s + fmt(val) + '%</span>';
            html += '</div>';
        }}
        html += '</div>';
        return html;
    }}

    function render() {{
        const key = curScope + '|' + curPeriod;
        const d = WF[key];
        if (!d) {{
            container.innerHTML = '<div style="color:' + MUTED_C + ';font-size:12px;padding:20px 0">No data for this combination.</div>';
            return;
        }}
        if (curView === 'bars') container.innerHTML = renderBars(d);
        else if (curView === 'table') container.innerHTML = renderTable(d);
        else container.innerHTML = renderTrend(d);
    }}

    render();

    // Expose render for slider to call
    window.__wf_render = render;
    window.__wf_setScope = function(scope) {{ curScope = scope; }};
    window.__wf_setPeriod = function(period) {{ curPeriod = period; }};
    window.__wf_getCurPeriod = function() {{ return curPeriod; }};
    window.__wf_getCurView = function() {{ return curView; }};
    window.__wf_getCurScope = function() {{ return curScope; }};
}})();

// ======== GA MONTHLY BREAKDOWN TABLE ========
(function() {{
    var ddData = window.__ga_drilldown;
    if (!ddData) return;
    var select = document.getElementById('ga-month-select');
    var body = document.getElementById('ga-breakdown-body');
    if (!select || !body) return;

    var months = Object.keys(ddData).sort().reverse();
    months.forEach(function(m) {{
        var opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m.substring(0, 7);
        select.appendChild(opt);
    }});

    var COLORS = {{
        new_revenue: '{GA_NEW}',
        expansion_revenue: '{GA_EXPANSION}',
        resurrected_revenue: '{GA_RESURRECTED}',
        contraction_revenue: '{GA_CONTRACTION}',
        churned_revenue: '{GA_CHURNED}',
        retained_revenue: '{GA_RETAINED}'
    }};

    function renderTable(monthKey) {{
        var mData = ddData[monthKey];
        if (!mData) {{ body.innerHTML = '<div class="ga-dd-empty">No data</div>'; return; }}

        // Build per-partner rows from all components
        var partners = {{}};
        ['new_revenue','expansion_revenue','resurrected_revenue','contraction_revenue','churned_revenue'].forEach(function(comp) {{
            (mData[comp] || []).forEach(function(p) {{
                if (!partners[p.sid]) partners[p.sid] = {{ name: p.name, sid: p.sid, new_revenue:0, expansion_revenue:0, resurrected_revenue:0, contraction_revenue:0, churned_revenue:0 }};
                partners[p.sid][comp] = p.amount;
            }});
        }});

        var rows = Object.values(partners);
        // Compute net for each partner
        rows.forEach(function(r) {{
            r.net = r.new_revenue + r.expansion_revenue + r.resurrected_revenue - r.contraction_revenue - r.churned_revenue;
        }});
        // Sort by absolute net descending
        rows.sort(function(a, b) {{ return Math.abs(b.net) - Math.abs(a.net); }});

        if (rows.length === 0) {{
            body.innerHTML = '<div class="ga-dd-empty">No movement this month</div>';
            return;
        }}

        var html = '<table class="ga-dd-table"><thead><tr>';
        html += '<th>Partner</th>';
        html += '<th style="text-align:right;color:' + COLORS.new_revenue + '">New</th>';
        html += '<th style="text-align:right;color:' + COLORS.expansion_revenue + '">Expansion</th>';
        html += '<th style="text-align:right;color:' + COLORS.resurrected_revenue + '">Resurrected</th>';
        html += '<th style="text-align:right;color:' + COLORS.contraction_revenue + '">Contraction</th>';
        html += '<th style="text-align:right;color:' + COLORS.churned_revenue + '">Churned</th>';
        html += '<th style="text-align:right">Net</th>';
        html += '</tr></thead><tbody>';

        rows.forEach(function(r) {{
            function fmt(v, neg) {{
                if (v === 0) return '<span style="color:{DIM}">—</span>';
                var s = '$' + Math.abs(v).toLocaleString('en-US', {{maximumFractionDigits:0}});
                return neg ? '<span style="color:{DANGER}">-' + s + '</span>' : '<span style="color:{SUCCESS}">' + s + '</span>';
            }}
            var netColor = r.net >= 0 ? '{SUCCESS}' : '{DANGER}';
            var netSign = r.net >= 0 ? '+' : '-';
            html += '<tr onclick="showDetail(\'' + r.sid + '\')" style="cursor:pointer" title="View ' + r.name + '">';
            html += '<td style="font-weight:500">' + r.name + '</td>';
            html += '<td style="text-align:right">' + fmt(r.new_revenue, false) + '</td>';
            html += '<td style="text-align:right">' + fmt(r.expansion_revenue, false) + '</td>';
            html += '<td style="text-align:right">' + fmt(r.resurrected_revenue, false) + '</td>';
            html += '<td style="text-align:right">' + fmt(r.contraction_revenue, true) + '</td>';
            html += '<td style="text-align:right">' + fmt(r.churned_revenue, true) + '</td>';
            html += '<td style="text-align:right;font-weight:600;color:' + netColor + '">' + netSign + '$' + Math.abs(r.net).toLocaleString('en-US', {{maximumFractionDigits:0}}) + '</td>';
            html += '</tr>';
        }});

        html += '</tbody></table>';
        body.innerHTML = html;
    }}

    select.addEventListener('change', function() {{ renderTable(select.value); }});
    if (months.length > 0) renderTable(months[0]);
}})();

// ======== PARTNER RANGE SLIDER ========
(function() {{
    const PBN = window.__pulse_by_n;
    if (!PBN) return;
    const slider = document.getElementById('partner-range');
    const countEl = document.getElementById('slider-count');
    const labelEl = document.getElementById('slider-value-label');
    const nActive = window.__n_active;
    const nTotal = window.__n_total;
    if (!slider) return;

    const ACCENT = '{ACCENT}';
    const GAIN = '{GAIN}';
    const LOSS = '{LOSS}';
    const GA_RETAINED = '{GA_RETAINED}';
    const GA_NEW = '{GA_NEW}';
    const GA_EXPANSION = '{GA_EXPANSION}';
    const GA_RESURRECTED = '{GA_RESURRECTED}';
    const GA_CONTRACTION = '{GA_CONTRACTION}';
    const GA_CHURNED = '{GA_CHURNED}';

    const SNAP_POINTS = [3, 5, 10, nActive, nTotal];
    const SNAP_THRESHOLD = 1;

    function snap(val) {{
        for (const sp of SNAP_POINTS) {{
            if (Math.abs(val - sp) <= SNAP_THRESHOLD && sp <= nTotal) return sp;
        }}
        return val;
    }}

    function updateLabel(n) {{
        if (n >= nTotal) {{
            countEl.textContent = nTotal;
        }} else {{
            countEl.textContent = n;
        }}
    }}

    function updatePresetHighlight(n) {{
        document.querySelectorAll('.slider-preset').forEach(function(btn) {{
            var val = parseInt(btn.dataset.val);
            btn.classList.toggle('active', val === n);
        }});
    }}

    function colorQR(v) {{ return v >= 4 ? '#16A34A' : v >= 1 ? '#CA8A04' : '#DC2626'; }}
    function colorNDR(v) {{ return v >= 100 ? '#16A34A' : '#DC2626'; }}
    function colorGRet(v) {{ return v >= 80 ? '#16A34A' : v >= 60 ? '#CA8A04' : '#DC2626'; }}

    function updateKPIs(d) {{
        const kpiActive = document.getElementById('kpi-active');
        const kpiQR = document.getElementById('kpi-qr');
        const kpiNDR = document.getElementById('kpi-ndr');
        const kpiNDRSub = document.getElementById('kpi-ndr-sub');
        const kpiGRet = document.getElementById('kpi-gret');
        if (kpiActive) kpiActive.textContent = d.active;
        if (kpiQR) {{ kpiQR.textContent = d.qr.toFixed(1) + 'x'; kpiQR.style.color = colorQR(d.qr); }}
        if (kpiNDR) {{ kpiNDR.textContent = Math.round(d.ndr) + '%'; kpiNDR.style.color = colorNDR(d.ndr); }}
        if (kpiNDRSub) {{ kpiNDRSub.innerHTML = (d.ndr >= 100 ? 'Expanding' : 'Contracting') + ' &middot; existing partners'; }}
        if (kpiGRet) {{ kpiGRet.textContent = Math.round(d.gross_ret) + '%'; kpiGRet.style.color = colorGRet(d.gross_ret); }}

        // Update benchmark markers
        const qrMarker = document.getElementById('bench-qr-marker');
        if (qrMarker) {{ qrMarker.style.left = Math.max(0, Math.min(100, d.qr / 6 * 100)).toFixed(1) + '%'; qrMarker.title = 'Portfolio: ' + d.qr.toFixed(1) + 'x'; }}
        const ndrMarker = document.getElementById('bench-ndr-marker');
        if (ndrMarker) {{ ndrMarker.style.left = Math.max(0, Math.min(100, (d.ndr - 80) / (180 - 80) * 100)).toFixed(1) + '%'; ndrMarker.title = 'Portfolio: ' + Math.round(d.ndr) + '%'; }}
        const gretMarker = document.getElementById('bench-gret-marker');
        if (gretMarker) {{ gretMarker.style.left = Math.max(0, Math.min(100, d.gross_ret)).toFixed(1) + '%'; gretMarker.title = 'Portfolio: ' + Math.round(d.gross_ret) + '%'; }}
    }}

    function updateExpansionVsLosses(d) {{
        const panel = document.getElementById('el1-panel');
        if (!panel) return;
        const maxBar = Math.max(d.el1_gains, d.el1_losses, 1);
        const gainsPct = d.el1_gains / maxBar * 100;
        const lossesPct = d.el1_losses / maxBar * 100;
        const covColor = d.el1_coverage > 1.0 ? '{SUCCESS}' : '{DANGER}';
        const greenFill = panel.querySelector('.el1-fill-green');
        const redFill = panel.querySelector('.el1-fill-red');
        const summary = panel.querySelector('.el1-summary');
        if (greenFill) greenFill.style.width = gainsPct.toFixed(1) + '%';
        if (redFill) redFill.style.width = lossesPct.toFixed(1) + '%';
        if (summary) summary.innerHTML = 'Gains: $' + d.el1_gains.toLocaleString('en-US', {{maximumFractionDigits:0}}) + ' &middot; Losses: $' + d.el1_losses.toLocaleString('en-US', {{maximumFractionDigits:0}}) + ' &middot; Coverage: <span style="color:' + covColor + ';font-weight:600">' + d.el1_coverage.toFixed(1) + 'x</span>';
    }}

    function updateWaterfall(d) {{
        // Replace __waterfall_data with slider-filtered data, using only 'all' scope
        const wfData = window.__waterfall_data;
        if (!wfData || !d.wf) return;
        // Inject the slider-filtered data for all scope x period combos
        for (const period of ['1M', '3M', '6M', '12M', 'YTD', 'All']) {{
            wfData['all|' + period] = d.wf[period];
        }}
        // Re-render waterfall using existing render function
        if (window.__wf_render) {{
            // Force scope to 'all' when slider changes
            if (window.__wf_getCurScope && window.__wf_getCurScope() !== 'all') {{
                window.__wf_setScope('all');
                document.querySelectorAll('.wf-pill[data-scope]').forEach(function(b) {{ b.classList.remove('active'); }});
                var allBtn = document.querySelector('.wf-pill[data-scope="all"]');
                if (allBtn) allBtn.classList.add('active');
            }}
            window.__wf_render();
        }}
    }}

    function updateGACMGRChart(d) {{
        const el = document.getElementById('pulse-ga-cmgr');
        if (!el || typeof Plotly === 'undefined') return;
        const ga = d.ga_chart;
        const cm = d.cmgr_chart;
        if (!ga.months.length) return;

        const traces = [
            {{ x: ga.months, y: ga.retained, name: 'Retained', marker: {{color: GA_RETAINED}}, opacity: 0.5, type: 'bar', legendgroup: 'ga', legendgrouptitle: {{text: 'Growth Accounting'}}, hovertemplate: 'Retained: $%{{y:,.0f}}<extra></extra>' }},
            {{ x: ga.months, y: ga['new'], name: 'New', marker: {{color: GA_NEW}}, type: 'bar', legendgroup: 'ga', hovertemplate: 'New: $%{{y:,.0f}}<extra></extra>' }},
            {{ x: ga.months, y: ga.expansion, name: 'Expansion', marker: {{color: GA_EXPANSION}}, type: 'bar', legendgroup: 'ga', hovertemplate: 'Expansion: $%{{y:,.0f}}<extra></extra>' }},
            {{ x: ga.months, y: ga.resurrected, name: 'Resurrected', marker: {{color: GA_RESURRECTED}}, type: 'bar', legendgroup: 'ga', hovertemplate: 'Resurrected: $%{{y:,.0f}}<extra></extra>' }},
            {{ x: ga.months, y: ga.contraction.map(function(v){{return -v}}), name: 'Contraction', marker: {{color: GA_CONTRACTION}}, type: 'bar', legendgroup: 'ga', hovertemplate: 'Contraction: -$%{{y:,.0f}}<extra></extra>' }},
            {{ x: ga.months, y: ga.churned.map(function(v){{return -v}}), name: 'Churned', marker: {{color: GA_CHURNED}}, type: 'bar', legendgroup: 'ga', hovertemplate: 'Churned: -$%{{y:,.0f}}<extra></extra>' }},
        ];

        // CMGR lines
        var cmgrColors = [['cmgr3', 'CMGR-3', '#3B6BE0', 'solid'], ['cmgr6', 'CMGR-6', '#6366f1', 'dash'], ['cmgr12', 'CMGR-12', '#a78bfa', 'dot']];
        cmgrColors.forEach(function(cfg) {{
            var key = cfg[0], name = cfg[1], color = cfg[2], dash = cfg[3];
            var validX = [], validY = [];
            cm.months.forEach(function(m, i) {{
                if (cm[key][i] !== null) {{ validX.push(m); validY.push(cm[key][i]); }}
            }});
            if (validX.length > 0) {{
                traces.push({{
                    x: validX, y: validY, name: name, mode: 'lines+markers',
                    line: {{color: color, width: 3, dash: dash}}, marker: {{size: 5}},
                    yaxis: 'y2', legendgroup: 'cmgr', legendgrouptitle: {{text: 'CMGR'}},
                    hovertemplate: name + ': %{{y:.1f}}%<extra></extra>', type: 'scatter'
                }});
            }}
        }});

        Plotly.react(el, traces, el.layout);
    }}

    function updateAoEChart(d) {{
        const el = document.getElementById('pulse-rev-share');
        if (!el || typeof Plotly === 'undefined') return;
        const aoe = d.aoe_chart;
        if (!aoe.months.length) return;

        var traces = [];
        aoe.traces.forEach(function(t) {{
            traces.push({{
                x: aoe.months, y: t.y, name: t.name, stackgroup: 'one',
                line: {{width: 0.5, color: t.color}}, fillcolor: t.fillcolor,
                hovertemplate: t.name + ': %{{y:.1f}}%<extra></extra>', type: 'scatter'
            }});
        }});

        Plotly.react(el, traces, el.layout);
    }}

    function onSliderChange() {{
        var val = parseInt(slider.value);
        val = snap(val);
        slider.value = val;
        updateLabel(val);
        updatePresetHighlight(val);
        var key = String(Math.min(val, nActive));
        var d = PBN[key] || PBN[String(nActive)];
        if (!d) return;
        updateKPIs(d);
        updateExpansionVsLosses(d);
        updateWaterfall(d);
        updateGACMGRChart(d);
        updateAoEChart(d);
    }}

    slider.addEventListener('input', function() {{
        var val = parseInt(slider.value);
        updateLabel(val);
        updatePresetHighlight(snap(val));
        var key = String(Math.min(val, nActive));
        var d = PBN[key] || PBN[String(nActive)];
        if (d) updateKPIs(d);
    }});

    slider.addEventListener('change', onSliderChange);

    // Preset button clicks
    document.querySelectorAll('.slider-preset').forEach(function(btn) {{
        btn.addEventListener('click', function() {{
            var val = parseInt(btn.dataset.val);
            slider.value = val;
            onSliderChange();
        }});
    }});
}})();
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

<div id="tip-ndr">
    <div class="tip-title">Net Dollar Retention (NDR)</div>
    <div class="tip-formula"><span class="frac"><span class="frac-num">Beginning ARR + Expansion + Resurrected &minus; Churn &minus; Contraction</span><span class="frac-den">Beginning ARR</span></span><span class="op">&times;</span>100</div>
    <div class="tip-body">Measures how many dollars you retain from existing partners after expansion, downsell, and churn. &gt;100% means the portfolio grows even without new partners.</div>
    <div class="tip-bench">Benchmarks: 128% (25th pctl) &middot; 149% (50th) &middot; 153% (75th) &middot; 157% (90th)</div>
</div>

<div id="tip-gross-retention">
    <div class="tip-title">Gross Retention</div>
    <div class="tip-formula"><span class="frac"><span class="frac-num">Retained Revenue</span><span class="frac-den">Prior Period Revenue</span></span><span class="op">&times;</span>100</div>
    <div class="tip-body">The floor &mdash; how much revenue survives without new business or expansion.</div>
    <div class="tip-bench">&gt; 80% healthy &middot; 60&ndash;80% watch &middot; &lt; 60% critical</div>
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
