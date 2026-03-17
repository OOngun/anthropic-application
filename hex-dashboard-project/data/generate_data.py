import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)
MONTHS = pd.date_range(START_DATE, END_DATE, freq='MS')

# Realistic blended token rate:
# Claude 3.5 Sonnet: $3/1M input, $15/1M output
# Claude 3 Opus: $15/1M input, $75/1M output
# Claude 3.5 Haiku: $0.25/1M input, $1.25/1M output
# Typical ratio: 5:1 input:output, mix ~60% Sonnet, 15% Opus, 25% Haiku
# Blended ≈ $8-12/1M tokens
BLENDED_RATE_PER_M_TOKENS = 10.0

# Seasonality factors (index 0=Jan, 11=Dec)
# Light summer dip, Q4 budget flush, Dec holiday slowdown
SEASONALITY = [1.0, 1.0, 1.05, 1.05, 1.0, 0.95, 0.90, 0.85, 1.0, 1.05, 1.10, 0.88]

# ============================================================
# 3 STARTUPS — all growth stage, different trajectories
# ============================================================

startups_raw = [
    {
        'startup_id': 'S001',
        'startup_name': 'MedScribe AI',
        'hq_city': 'Paris',
        'country': 'France',
        'vertical': 'HealthTech',
        'stage': 'Series A',
        'founding_year': 2022,
        'onboard_date': '2024-01-01',
        'source': 'accelerator',
        'tier': 'growth',
        'archetype': 'rocket',
        'description': 'AI clinical note-taking. Uses Claude to transcribe and summarise patient consultations. Expanding from France into DACH.',
        # Startup-specific params
        'initial_arr': 1_800_000,
        'arr_qoq_growth': 0.35,  # 35% QoQ = ~230% YoY (T2D3 triple territory)
        'initial_headcount': 28,
        'headcount_growth_qoq': 0.18,
        'burn_multiple_base': 1.1,
        'runway_months_start': 22,
        'nrr_base': 138,
        'last_funding_date': '2023-09-15',
        'last_funding_amount': 12_000_000,
        # API usage params
        'base_monthly_tokens': 150_000_000,  # ~$1,500/mo starting
        'mom_growth': 0.14,  # 14% MoM
        'max_developers': 35,  # small team, fast-growing
        'ramp_months': 2,
        'primary_model': 'sonnet',
        'model_mix_start': {'sonnet': 0.75, 'opus': 0.15, 'haiku': 0.10},
        'model_mix_end': {'sonnet': 0.55, 'opus': 0.10, 'haiku': 0.35},  # optimises over time
    },
    {
        'startup_id': 'S002',
        'startup_name': 'Eigen Technologies',
        'hq_city': 'London',
        'country': 'UK',
        'vertical': 'Document AI',
        'stage': 'Series B',
        'founding_year': 2014,
        'onboard_date': '2024-04-01',
        'source': 'vc_referral',
        'tier': 'growth',
        'archetype': 'steady',
        'description': 'Intelligent document processing for financial services. Migrating from in-house models to Claude for complex extraction. Established but conservative growth.',
        'initial_arr': 8_500_000,
        'arr_qoq_growth': 0.12,  # 12% QoQ = ~59% YoY (solid Series B)
        'initial_headcount': 95,
        'headcount_growth_qoq': 0.05,
        'burn_multiple_base': 2.2,
        'runway_months_start': 26,
        'nrr_base': 112,
        'last_funding_date': '2023-03-01',
        'last_funding_amount': 35_000_000,
        'base_monthly_tokens': 300_000_000,  # ~$3,000/mo starting (bigger starting base)
        'mom_growth': 0.04,  # 4% MoM — steady adopter
        'max_developers': 22,  # established team, fewer devs touch API directly
        'ramp_months': 4,  # enterprise — slow integration
        'primary_model': 'sonnet',
        'model_mix_start': {'sonnet': 0.60, 'opus': 0.25, 'haiku': 0.15},
        'model_mix_end': {'sonnet': 0.50, 'opus': 0.15, 'haiku': 0.35},
    },
    {
        'startup_id': 'S003',
        'startup_name': 'BuilderKit',
        'hq_city': 'London',
        'country': 'UK',
        'vertical': 'No-Code/AI',
        'stage': 'Series B',
        'founding_year': 2018,
        'onboard_date': '2024-06-01',
        'source': 'vc_referral',
        'tier': 'growth',
        'archetype': 'declining',
        'description': 'AI-powered no-code app builder. Initially enthusiastic Claude adopter but struggled with cost management and shifted some workloads to open-source models.',
        'initial_arr': 6_200_000,
        'arr_qoq_growth': 0.05,  # 5% QoQ = ~22% YoY (slowing)
        'initial_headcount': 85,
        'headcount_growth_qoq': -0.03,  # slight layoffs / attrition
        'burn_multiple_base': 5.5,
        'runway_months_start': 10,
        'nrr_base': 86,
        'last_funding_date': '2022-11-01',
        'last_funding_amount': 45_000_000,
        'base_monthly_tokens': 250_000_000,
        'mom_growth': -0.04,  # declining usage
        'max_developers': 18,
        'ramp_months': 3,
        'primary_model': 'haiku',  # cost-sensitive
        'model_mix_start': {'sonnet': 0.50, 'opus': 0.20, 'haiku': 0.30},
        'model_mix_end': {'sonnet': 0.25, 'opus': 0.05, 'haiku': 0.70},  # shifts to cheap models
    },
]

startups = pd.DataFrame(startups_raw)
startups['onboard_date'] = pd.to_datetime(startups['onboard_date'])
startups['region'] = startups['country'].map({
    'UK': 'UK & Ireland', 'France': 'France',
})

# ============================================================
# CREDIT GRANTS — with noise, not perfectly mechanical
# ============================================================

credit_rows = []
for _, s in startups.iterrows():
    base_credit = 25000  # growth tier
    # Add noise: ±15%
    initial = int(base_credit * np.random.uniform(0.85, 1.15))
    credit_rows.append({
        'startup_id': s['startup_id'],
        'grant_date': s['onboard_date'],
        'grant_type': 'initial',
        'amount_usd': initial,
    })

    months_active = len(MONTHS) - list(MONTHS).index(s['onboard_date'])

    # Top-up at 5-7 months (not exactly 6)
    if months_active > 6:
        topup_month_offset = np.random.randint(5, 8)
        topup_idx = min(list(MONTHS).index(s['onboard_date']) + topup_month_offset, len(MONTHS) - 1)

        # Rocket gets bigger top-up, declining gets smaller or none
        if s['archetype'] == 'rocket':
            topup_mult = np.random.uniform(0.55, 0.75)
        elif s['archetype'] == 'declining':
            topup_mult = np.random.uniform(0.20, 0.35) if np.random.random() > 0.3 else 0
        else:
            topup_mult = np.random.uniform(0.40, 0.55)

        if topup_mult > 0:
            credit_rows.append({
                'startup_id': s['startup_id'],
                'grant_date': MONTHS[topup_idx],
                'grant_type': 'topup',
                'amount_usd': int(initial * topup_mult),
            })

    # Renewal at 11-13 months
    if months_active > 12 and s['archetype'] != 'declining':
        renewal_offset = np.random.randint(11, 14)
        renewal_idx = min(list(MONTHS).index(s['onboard_date']) + renewal_offset, len(MONTHS) - 1)
        renewal_mult = np.random.uniform(0.60, 0.85)
        credit_rows.append({
            'startup_id': s['startup_id'],
            'grant_date': MONTHS[renewal_idx],
            'grant_type': 'renewal',
            'amount_usd': int(initial * renewal_mult),
        })

credits = pd.DataFrame(credit_rows)

# ============================================================
# MONTHLY USAGE — path-dependent, autocorrelated, seasonal
# ============================================================

usage_rows = []

for _, s in startups.iterrows():
    onboard_idx = list(MONTHS).index(s['onboard_date'])
    months_active = len(MONTHS) - onboard_idx

    current_tokens = s['base_monthly_tokens']
    mom = s['mom_growth']
    ramp_months = s['ramp_months']

    # Model mix — linear interpolation from start to end
    mix_start = s['model_mix_start']
    mix_end = s['model_mix_end']

    # Active developer trajectory: logistic ramp to max
    max_devs = s['max_developers']

    # Track previous month for autocorrelation
    prev_sonnet = mix_start['sonnet']
    prev_opus = mix_start['opus']
    prev_latency = 350 if s['primary_model'] == 'sonnet' else (550 if s['primary_model'] == 'opus' else 180)
    prev_error_rate = 0.02

    for m in range(months_active):
        month_idx = onboard_idx + m
        if month_idx >= len(MONTHS):
            break

        month = MONTHS[month_idx]
        cal_month = month.month - 1  # 0-indexed for seasonality

        # Ramp-up: logistic curve with randomised steepness
        if m < ramp_months:
            # Logistic: starts slow, accelerates
            ramp_progress = m / ramp_months
            ramp = 0.08 + 0.92 * (ramp_progress ** 1.5)  # convex ramp
        else:
            ramp = 1.0

        # Monthly noise — autocorrelated (not pure white noise)
        noise = np.random.normal(1.0, 0.08)

        # Seasonality
        seasonal = SEASONALITY[cal_month]

        # Compute tokens
        tokens = max(0, current_tokens * ramp * noise * seasonal)

        # For declining archetype: add a step-change drop at month 8-10
        if s['archetype'] == 'declining' and m == np.random.choice([8, 9, 10]):
            tokens *= 0.65  # sharp drop — maybe lost a key use case

        tokens = int(tokens)

        # Revenue
        revenue = round((tokens / 1e6) * BLENDED_RATE_PER_M_TOKENS, 2)

        # API calls: tokens per call varies by model mix (Opus = more tokens/call)
        opus_weight = mix_start['opus'] + (mix_end['opus'] - mix_start['opus']) * (m / max(1, months_active - 1))
        tokens_per_call = np.random.uniform(700, 1800) + opus_weight * 2000
        api_calls = max(1 if tokens > 0 else 0, int(tokens / tokens_per_call))

        # Model mix — autocorrelated with drift toward end state
        t = m / max(1, months_active - 1)
        target_sonnet = mix_start['sonnet'] + (mix_end['sonnet'] - mix_start['sonnet']) * t
        target_opus = mix_start['opus'] + (mix_end['opus'] - mix_start['opus']) * t

        sonnet_pct = round(0.85 * prev_sonnet + 0.15 * target_sonnet + np.random.normal(0, 0.02), 3)
        opus_pct = round(0.85 * prev_opus + 0.15 * target_opus + np.random.normal(0, 0.01), 3)
        sonnet_pct = np.clip(sonnet_pct, 0.15, 0.85)
        opus_pct = np.clip(opus_pct, 0.02, 0.35)
        haiku_pct = round(1.0 - sonnet_pct - opus_pct, 3)
        haiku_pct = max(0.0, haiku_pct)
        # Renormalise
        total = sonnet_pct + opus_pct + haiku_pct
        sonnet_pct = round(sonnet_pct / total, 3)
        opus_pct = round(opus_pct / total, 3)
        haiku_pct = round(1.0 - sonnet_pct - opus_pct, 3)

        prev_sonnet = sonnet_pct
        prev_opus = opus_pct

        # Active developers: logistic growth capped at max_devs
        dev_capacity = max_devs * (1 / (1 + np.exp(-0.4 * (m - ramp_months - 2))))
        if s['archetype'] == 'declining':
            dev_capacity *= max(0.4, 1 - 0.03 * max(0, m - 6))
        active_devs = max(1, int(dev_capacity + np.random.normal(0, max(1, dev_capacity * 0.1))))
        active_devs = min(active_devs, max_devs)

        # Use cases: grows in discrete steps, not linearly with tokens
        base_use_cases = min(2 + m, 8) if s['archetype'] != 'rocket' else min(3 + m * 2, 15)
        if s['archetype'] == 'declining' and m > 8:
            base_use_cases = max(2, base_use_cases - (m - 8))
        use_cases = max(1, base_use_cases + np.random.randint(-1, 2))

        # Latency: function of model mix (Opus-heavy = slower)
        base_latency = 250 + opus_pct * 800 + sonnet_pct * 200
        latency = round(0.7 * prev_latency + 0.3 * (base_latency + np.random.normal(0, 30)), 0)
        prev_latency = latency

        # Error rate: autocorrelated, occasional spikes
        base_error = 0.015
        error_rate = round(0.8 * prev_error_rate + 0.2 * base_error + np.random.normal(0, 0.003), 4)
        error_rate = np.clip(error_rate, 0.001, 0.08)
        prev_error_rate = error_rate

        usage_rows.append({
            'startup_id': s['startup_id'],
            'month': month,
            'total_tokens': tokens,
            'api_calls': api_calls,
            'revenue_usd': revenue,
            'sonnet_pct': sonnet_pct,
            'opus_pct': opus_pct,
            'haiku_pct': haiku_pct,
            'unique_use_cases': use_cases,
            'active_developers': active_devs,
            'avg_latency_ms': latency,
            'error_rate': error_rate,
        })

        # Compound growth for next month
        growth_noise = np.random.normal(0, 0.015)
        current_tokens *= (1 + mom + growth_noise)
        current_tokens = max(0, current_tokens)

monthly_usage = pd.DataFrame(usage_rows)

# ============================================================
# STARTUP HEALTH — path-dependent, cumulative, consistent
# ============================================================

health_rows = []
quarters = pd.date_range(START_DATE, END_DATE, freq='QS')

for _, s in startups.iterrows():
    onboard_date = s['onboard_date']
    arr = s['initial_arr']
    hc = s['initial_headcount']
    runway = s['runway_months_start']
    burn_mult = s['burn_multiple_base']
    nrr = s['nrr_base']

    prev_arr = None
    arr_history = []

    for q in quarters:
        if q < onboard_date:
            continue
        if q > END_DATE:
            break

        quarters_in = max(1, (q - onboard_date).days // 90)

        # ARR: compound forward with noise (path-dependent!)
        qoq = s['arr_qoq_growth'] + np.random.normal(0, 0.03)
        if s['archetype'] == 'declining' and quarters_in > 3:
            qoq = max(-0.08, qoq - 0.06 * (quarters_in - 3))

        arr = arr * (1 + qoq)
        arr = max(500_000, arr)
        arr_history.append(arr)

        # YoY: compute from actual ARR history
        if len(arr_history) >= 5:
            yoy = ((arr_history[-1] / arr_history[-5]) - 1) * 100
        elif len(arr_history) >= 2:
            yoy = ((arr_history[-1] / arr_history[0]) - 1) * 100 * (4 / len(arr_history))
        else:
            yoy = s['arr_qoq_growth'] * 4 * 100  # estimate from QoQ

        # Headcount: monotonic for growing, slight decline for declining
        hc_growth = s['headcount_growth_qoq'] + np.random.normal(0, 0.02)
        hc = max(int(hc * (1 + hc_growth)), 5)

        # Burn multiple: slight drift with noise
        burn_drift = np.random.normal(0, 0.15)
        if s['archetype'] == 'rocket':
            burn_drift -= 0.05  # improving over time
        elif s['archetype'] == 'declining':
            burn_drift += 0.1
        burn_mult = max(0.5, burn_mult + burn_drift)

        # Runway: decreasing unless they raise
        runway -= np.random.uniform(2.5, 3.5)
        if s['archetype'] == 'declining':
            runway -= np.random.uniform(0.5, 1.5)
        runway = max(2, runway)

        # NRR: autocorrelated
        nrr_noise = np.random.normal(0, 2)
        if s['archetype'] == 'declining':
            nrr_noise -= 1.5
        nrr = nrr + nrr_noise
        nrr = np.clip(nrr, 60, 170)

        health_rows.append({
            'startup_id': s['startup_id'],
            'quarter': q,
            'estimated_arr': round(arr, 0),
            'yoy_growth_pct': round(yoy, 1),
            'headcount': hc,
            'burn_multiple': round(burn_mult, 2),
            'runway_months': round(runway, 1),
            'nrr_pct': round(nrr, 1),
            'last_funding_date': s['last_funding_date'],
            'last_funding_amount': s['last_funding_amount'],
        })

startup_health = pd.DataFrame(health_rows)

# ============================================================
# PARTNERSHIP EVENTS
# ============================================================

event_rows = []

def add_event(sid, base_date, day_offset, etype):
    event_rows.append({
        'startup_id': sid,
        'event_date': base_date + timedelta(days=day_offset),
        'event_type': etype,
    })

for _, s in startups.iterrows():
    base = s['onboard_date']
    months_active = len(MONTHS) - list(MONTHS).index(base)

    # Universal events
    add_event(s['startup_id'], base, np.random.randint(0, 5), 'credits_activated')
    add_event(s['startup_id'], base, np.random.randint(3, 14), 'first_api_call')

    if s['archetype'] == 'rocket':
        add_event(s['startup_id'], base, np.random.randint(25, 55), 'production_deployment')
        add_event(s['startup_id'], base, np.random.randint(90, 150), 'enterprise_upgrade')
        add_event(s['startup_id'], base, np.random.randint(150, 210), 'builder_summit_speaker')
        add_event(s['startup_id'], base, np.random.randint(60, 120), 'expanded_use_case')
        add_event(s['startup_id'], base, np.random.randint(120, 200), 'referred_another_startup')
        for i in range(4):
            add_event(s['startup_id'], base, 45 + i * 75 + np.random.randint(-10, 10), 'feedback_session')
        if months_active > 8:
            add_event(s['startup_id'], base, np.random.randint(200, 300), 'case_study_published')

    elif s['archetype'] == 'steady':
        add_event(s['startup_id'], base, np.random.randint(50, 100), 'production_deployment')
        for i in range(3):
            add_event(s['startup_id'], base, 60 + i * 90 + np.random.randint(-10, 10), 'feedback_session')
        if months_active > 10:
            add_event(s['startup_id'], base, np.random.randint(250, 350), 'expanded_use_case')

    elif s['archetype'] == 'declining':
        add_event(s['startup_id'], base, np.random.randint(40, 80), 'production_deployment')
        add_event(s['startup_id'], base, np.random.randint(90, 150), 'feedback_session')
        add_event(s['startup_id'], base, np.random.randint(150, 240), 'churn_risk_flagged')
        if months_active > 12:
            add_event(s['startup_id'], base, np.random.randint(300, 400), 'win_back_attempt')

events = pd.DataFrame(event_rows)

# ============================================================
# GROWTH ACCOUNTING
# ============================================================

growth_acct_rows = []

for month_idx in range(1, len(MONTHS)):
    month = MONTHS[month_idx]
    prev_month = MONTHS[month_idx - 1]

    curr = monthly_usage[monthly_usage['month'] == month].set_index('startup_id')['revenue_usd']
    prev = monthly_usage[monthly_usage['month'] == prev_month].set_index('startup_id')['revenue_usd']

    all_ids = set(curr.index) | set(prev.index)

    new_rev = expansion_rev = contraction_rev = churned_rev = resurrected_rev = 0

    for sid in all_ids:
        c = curr.get(sid, 0)
        p = prev.get(sid, 0)

        if p == 0 and c > 0:
            earlier = monthly_usage[
                (monthly_usage['startup_id'] == sid) &
                (monthly_usage['month'] < prev_month) &
                (monthly_usage['revenue_usd'] > 0)
            ]
            if len(earlier) > 0:
                resurrected_rev += c
            else:
                new_rev += c
        elif p > 0 and c == 0:
            churned_rev += p
        elif c > p:
            expansion_rev += (c - p)
        elif c < p:
            contraction_rev += (p - c)

    denom = max(1, contraction_rev + churned_rev)
    qr = (new_rev + expansion_rev + resurrected_rev) / denom

    growth_acct_rows.append({
        'month': month,
        'new_revenue': round(new_rev, 2),
        'expansion_revenue': round(expansion_rev, 2),
        'contraction_revenue': round(contraction_rev, 2),
        'churned_revenue': round(churned_rev, 2),
        'resurrected_revenue': round(resurrected_rev, 2),
        'quick_ratio': round(qr, 2),
    })

growth_accounting = pd.DataFrame(growth_acct_rows)

# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR = '/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/data'

startups[['startup_id', 'startup_name', 'hq_city', 'country', 'region', 'vertical',
          'stage', 'founding_year', 'onboard_date', 'source', 'tier', 'archetype',
          'description']].to_csv(f'{OUTPUT_DIR}/startups.csv', index=False)
credits.to_csv(f'{OUTPUT_DIR}/credit_grants.csv', index=False)
monthly_usage.to_csv(f'{OUTPUT_DIR}/monthly_usage.csv', index=False)
startup_health.to_csv(f'{OUTPUT_DIR}/startup_health.csv', index=False)
events.to_csv(f'{OUTPUT_DIR}/partnership_events.csv', index=False)
growth_accounting.to_csv(f'{OUTPUT_DIR}/growth_accounting.csv', index=False)

# ============================================================
# SUMMARY
# ============================================================

print("=" * 60)
print("DATA GENERATION COMPLETE — 3 GROWTH-STAGE STARTUPS")
print("=" * 60)

for _, s in startups.iterrows():
    usage = monthly_usage[monthly_usage['startup_id'] == s['startup_id']]
    creds = credits[credits['startup_id'] == s['startup_id']]
    health = startup_health[startup_health['startup_id'] == s['startup_id']]
    evts = events[events['startup_id'] == s['startup_id']]

    print(f"\n{'='*50}")
    print(f"{s['startup_name']} ({s['startup_id']}) — {s['archetype'].upper()}")
    print(f"{'='*50}")
    print(f"  {s['vertical']} | {s['stage']} | {s['hq_city']}, {s['country']}")
    print(f"  Onboarded: {s['onboard_date'].strftime('%Y-%m-%d')} | Source: {s['source']}")
    print(f"  Credits granted: ${creds['amount_usd'].sum():,.0f}")
    print(f"  Total revenue: ${usage['revenue_usd'].sum():,.0f}")
    print(f"  Revenue range: ${usage['revenue_usd'].min():,.0f} – ${usage['revenue_usd'].max():,.0f}/mo")
    print(f"  Months of data: {len(usage)}")
    print(f"  Events: {len(evts)} ({', '.join(evts['event_type'].value_counts().head(3).index.tolist())})")
    print(f"  Health snapshots: {len(health)}")

    print(f"\n  Monthly revenue trajectory:")
    for _, u in usage.iterrows():
        bar = '█' * max(1, int(u['revenue_usd'] / 500))
        print(f"    {u['month'].strftime('%Y-%m')}  ${u['revenue_usd']:>10,.2f}  devs:{u['active_developers']:>3d}  {bar}")

    print(f"\n  Quarterly health:")
    for _, h in health.iterrows():
        print(f"    {h['quarter'].strftime('%Y-Q%q') if hasattr(h['quarter'], 'quarter') else h['quarter']}  ARR: ${h['estimated_arr']:>12,.0f}  HC: {h['headcount']:>4d}  Burn: {h['burn_multiple']:.1f}x  NRR: {h['nrr_pct']:.0f}%  Runway: {h['runway_months']:.0f}mo")

print(f"\n{'='*60}")
print(f"PORTFOLIO SUMMARY")
print(f"{'='*60}")
print(f"Total credits: ${credits['amount_usd'].sum():,.0f}")
print(f"Total revenue: ${monthly_usage['revenue_usd'].sum():,.0f}")
print(f"ROI: {monthly_usage['revenue_usd'].sum() / credits['amount_usd'].sum():.2f}x")
print(f"\nGrowth accounting months: {len(growth_accounting)}")
print(f"Quick Ratio range: {growth_accounting['quick_ratio'].min():.1f} – {growth_accounting['quick_ratio'].max():.1f}")
print(f"\nFiles saved to: {OUTPUT_DIR}/")
