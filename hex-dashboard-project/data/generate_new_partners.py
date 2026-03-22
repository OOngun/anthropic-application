#!/usr/bin/env python3
"""
Generate 20 synthetic startup partners (S004-S023) for the EMEA Startup Partnerships dashboard.

Distribution:
  Star: 1 (S004)
  Strong: 2 (S005-S006)
  Fine: 9 (S007-S015)
  Declining: 3 (S016-S018)
  Churned: 3 (S019-S021)
  Minimal: 2 (S022-S023)

Revenue formula: revenue_usd = total_tokens * (sonnet_pct*15 + opus_pct*75 + haiku_pct*1) / 1_000_000
"""

import csv
import random
import os

random.seed(42)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
MONTHS = [f"2024-{m:02d}-01" for m in range(1, 13)] + [f"2025-{m:02d}-01" for m in range(1, 13)]


def blended_rate(s, o, h):
    return s * 15 + o * 75 + h * 1

def calc_revenue(tokens, s, o, h):
    return round(tokens * blended_rate(s, o, h) / 1_000_000, 2)

def tokens_for_revenue(target_rev, s, o, h):
    """Compute tokens needed to hit a target revenue given model mix."""
    br = blended_rate(s, o, h)
    if br == 0:
        return 0
    return int(target_rev * 1_000_000 / br)

def noise(val, pct=0.15):
    return val * random.uniform(1 - pct, 1 + pct)

def make_model_mix(sonnet, opus, haiku):
    total = sonnet + opus + haiku
    if total == 0:
        return 0.0, 0.0, 0.0
    s = round(sonnet / total, 3)
    o = round(opus / total, 3)
    h = round(1.0 - s - o, 3)
    if h < 0:
        h = 0.0
        s = round(sonnet / (sonnet + opus), 3)
        o = round(1.0 - s, 3)
    return s, o, h

def make_row(sid, month_idx, tokens, sonnet, opus, haiku, use_cases, devs, latency=None, err=None):
    s, o, h = make_model_mix(sonnet, opus, haiku)
    tokens = max(0, int(tokens))
    rev = calc_revenue(tokens, s, o, h)
    calls = int(tokens / random.uniform(1000, 3000)) if tokens > 0 else 0
    lat = latency or round(random.uniform(350, 550), 1)
    er = err or round(random.uniform(0.01, 0.03), 4)
    return {
        'startup_id': sid,
        'month': MONTHS[month_idx],
        'total_tokens': tokens,
        'api_calls': calls,
        'revenue_usd': rev,
        'sonnet_pct': s,
        'opus_pct': o,
        'haiku_pct': h,
        'unique_use_cases': use_cases,
        'active_developers': devs,
        'avg_latency_ms': lat,
        'error_rate': er,
    }

def zero_row(sid, month_idx):
    return {
        'startup_id': sid,
        'month': MONTHS[month_idx],
        'total_tokens': 0,
        'api_calls': 0,
        'revenue_usd': 0.0,
        'sonnet_pct': 0.0,
        'opus_pct': 0.0,
        'haiku_pct': 0.0,
        'unique_use_cases': 0,
        'active_developers': 0,
        'avg_latency_ms': 0.0,
        'error_rate': 0.0,
    }


# ═══════════════════════════════════════════════════
# STARTUP METADATA
# ═══════════════════════════════════════════════════

startups = [
    {'startup_id': 'S004', 'startup_name': 'NovaMed AI', 'hq_city': 'Tel Aviv',
     'country': 'Israel', 'region': 'Middle East', 'vertical': 'HealthTech',
     'stage': 'Series B', 'founding_year': 2021, 'onboard_date': '2024-01-01',
     'source': 'accelerator', 'tier': 'growth', 'archetype': 'star',
     'description': 'AI-powered clinical trial matching platform. Found product-market fit around month 6, raised Series A at month 10. Their core matching engine runs entirely on Claude.'},

    {'startup_id': 'S005', 'startup_name': 'LegalLens', 'hq_city': 'London',
     'country': 'UK', 'region': 'UK & Ireland', 'vertical': 'LegalTech',
     'stage': 'Series A', 'founding_year': 2022, 'onboard_date': '2024-01-01',
     'source': 'vc_referral', 'tier': 'growth', 'archetype': 'strong',
     'description': 'Contract analysis and due diligence tool for law firms. Very consistent B2B usage patterns with strong retention.'},

    {'startup_id': 'S006', 'startup_name': 'SupplyChainIQ', 'hq_city': 'Amsterdam',
     'country': 'Netherlands', 'region': 'Western Europe', 'vertical': 'Logistics',
     'stage': 'Series A', 'founding_year': 2022, 'onboard_date': '2024-01-01',
     'source': 'accelerator', 'tier': 'growth', 'archetype': 'strong',
     'description': 'Logistics optimisation using Claude for demand forecasting and route planning. Growth driven by landing large enterprise customers.'},

    {'startup_id': 'S007', 'startup_name': 'TutorBot', 'hq_city': 'Berlin',
     'country': 'Germany', 'region': 'DACH', 'vertical': 'EdTech',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'AI tutoring assistant for secondary school students. Seasonal usage following European school calendar.'},

    {'startup_id': 'S008', 'startup_name': 'CodeReview.ai', 'hq_city': 'Dublin',
     'country': 'Ireland', 'region': 'UK & Ireland', 'vertical': 'DevTools',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Automated code review tool using Claude for explanations and suggestions. Steady but unspectacular usage.'},

    {'startup_id': 'S009', 'startup_name': 'RetailPulse', 'hq_city': 'Paris',
     'country': 'France', 'region': 'France', 'vertical': 'Retail',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Retail analytics and demand forecasting. Clear Q4 seasonal spikes around Black Friday.'},

    {'startup_id': 'S010', 'startup_name': 'ChatAssist', 'hq_city': 'Stockholm',
     'country': 'Sweden', 'region': 'Nordics', 'vertical': 'SaaS',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Customer support chatbot running entirely on Haiku. Low cost, low growth, stable.'},

    {'startup_id': 'S011', 'startup_name': 'DataClean', 'hq_city': 'Zurich',
     'country': 'Switzerland', 'region': 'DACH', 'vertical': 'Data',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Data cleaning and normalisation tool. Haiku-only, batch processing workload.'},

    {'startup_id': 'S012', 'startup_name': 'SalesForge', 'hq_city': 'Barcelona',
     'country': 'Spain', 'region': 'Southern Europe', 'vertical': 'Marketing',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Sales email generation and personalisation. Sonnet-based, modest but consistent volume.'},

    {'startup_id': 'S013', 'startup_name': 'DocuStream', 'hq_city': 'Berlin',
     'country': 'Germany', 'region': 'DACH', 'vertical': 'Document AI',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Document automation for small businesses. Single developer maintaining a simple integration.'},

    {'startup_id': 'S014', 'startup_name': 'PolicyPal', 'hq_city': 'London',
     'country': 'UK', 'region': 'UK & Ireland', 'vertical': 'InsurTech',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'vc_referral', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Insurance policy comparison and summarisation. Mostly Sonnet for quality, low volume.'},

    {'startup_id': 'S015', 'startup_name': 'MenuMind', 'hq_city': 'Paris',
     'country': 'France', 'region': 'France', 'vertical': 'FoodTech',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'fine',
     'description': 'Restaurant menu optimisation and dietary analysis. Niche but stable usage.'},

    {'startup_id': 'S016', 'startup_name': 'VoiceAI Labs', 'hq_city': 'London',
     'country': 'UK', 'region': 'UK & Ireland', 'vertical': 'Voice Tech',
     'stage': 'Series A', 'founding_year': 2021, 'onboard_date': '2024-01-01',
     'source': 'vc_referral', 'tier': 'standard', 'archetype': 'declining',
     'description': 'Voice transcription and analysis. Lost ground to Whisper and OpenAI. Model mix shifted to Haiku before volume declined.'},

    {'startup_id': 'S017', 'startup_name': 'MarketingGPT', 'hq_city': 'Amsterdam',
     'country': 'Netherlands', 'region': 'Western Europe', 'vertical': 'Marketing',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'declining',
     'description': 'Content generation for marketers. Space became commoditised, steady decline from early peak.'},

    {'startup_id': 'S018', 'startup_name': 'FinBot Analytics', 'hq_city': 'Zurich',
     'country': 'Switzerland', 'region': 'DACH', 'vertical': 'FinTech',
     'stage': 'Seed', 'founding_year': 2022, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'declining',
     'description': 'Financial analysis chatbot. Regulatory concerns slowed roadmap, lost their primary customer.'},

    {'startup_id': 'S019', 'startup_name': 'QuickDraft', 'hq_city': 'Dublin',
     'country': 'Ireland', 'region': 'UK & Ireland', 'vertical': 'Content',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'churned',
     'description': 'Content drafting tool. Active 8 months then cliff-edge churn — switched to a competitor.'},

    {'startup_id': 'S020', 'startup_name': 'AIRecruiter', 'hq_city': 'Stockholm',
     'country': 'Sweden', 'region': 'Nordics', 'vertical': 'HR',
     'stage': 'Seed', 'founding_year': 2023, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'churned',
     'description': 'AI-powered hiring and screening tool. Gradual decline over 4 months then zero. Deprioritised the AI feature.'},

    {'startup_id': 'S021', 'startup_name': 'PropTech AI', 'hq_city': 'Lagos',
     'country': 'Nigeria', 'region': 'Africa', 'vertical': 'PropTech',
     'stage': 'Seed', 'founding_year': 2022, 'onboard_date': '2024-01-01',
     'source': 'accelerator', 'tier': 'standard', 'archetype': 'churned',
     'description': 'Real estate valuation and listing tool for African markets. Growing well for 10 months then sudden cliff — lost funding.'},

    {'startup_id': 'S022', 'startup_name': 'NoteAI', 'hq_city': 'Barcelona',
     'country': 'Spain', 'region': 'Southern Europe', 'vertical': 'Productivity',
     'stage': 'Pre-Seed', 'founding_year': 2024, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'minimal',
     'description': 'Note-taking assistant. Made a handful of API calls, never built a real integration.'},

    {'startup_id': 'S023', 'startup_name': 'GreenTech AI', 'hq_city': 'Tel Aviv',
     'country': 'Israel', 'region': 'Middle East', 'vertical': 'CleanTech',
     'stage': 'Pre-Seed', 'founding_year': 2024, 'onboard_date': '2024-01-01',
     'source': 'application', 'tier': 'standard', 'archetype': 'minimal',
     'description': 'Sporadic testing by a solo founder. A few API calls every couple months, never shipped anything.'},
]


# ═══════════════════════════════════════════════════
# CREDIT GRANTS
# ═══════════════════════════════════════════════════

credit_grants = [
    {'startup_id': 'S004', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 50000},
    {'startup_id': 'S004', 'grant_date': '2024-09-01', 'grant_type': 'topup', 'amount_usd': 25000},
    {'startup_id': 'S005', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 25000},
    {'startup_id': 'S005', 'grant_date': '2024-12-01', 'grant_type': 'renewal', 'amount_usd': 15000},
    {'startup_id': 'S006', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 25000},
    {'startup_id': 'S007', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 15000},
    {'startup_id': 'S008', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 15000},
    {'startup_id': 'S009', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 15000},
    {'startup_id': 'S010', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S011', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S012', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S013', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S014', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S015', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S016', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 20000},
    {'startup_id': 'S017', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 15000},
    {'startup_id': 'S018', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 15000},
    {'startup_id': 'S019', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S020', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S021', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 12000},
    {'startup_id': 'S022', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
    {'startup_id': 'S023', 'grant_date': '2024-01-01', 'grant_type': 'initial', 'amount_usd': 10000},
]


# ═══════════════════════════════════════════════════
# MONTHLY USAGE — REVENUE-FIRST APPROACH
# For each month, define target revenue and model mix,
# then derive tokens from the formula.
# ═══════════════════════════════════════════════════

all_usage_rows = []


# ── S004: STAR — NovaMed AI ──
# Slow start, inflection month 6, exponential, Series A month 10
# Revenue: ~$200 m1 → ~$35K m24. Model shifts toward Opus.
def gen_star():
    rows = []
    # Target monthly revenue trajectory
    rev_targets = [
        150, 280, 400, 500, 600,          # m1-5: slow experimenting
        1200, 2200, 3500, 3000,           # m6-9: inflection + beta launch m8, slight dip m9
        5000, 7000, 9000,                 # m10-12: Series A boost
        11000, 13000, 10000,              # m13-15: credits exhaust m14, infra dip m15
        14500, 17000, 20000,              # m16-18: resume growth
        21000, 22000,                     # m19-20: slight plateau
        24000, 26000, 28000, 30000,       # m21-24: resume
    ]

    # Model mix: haiku-heavy → opus shift
    model_mix = [
        (0.20, 0.00, 0.80), (0.25, 0.02, 0.73), (0.30, 0.03, 0.67),
        (0.30, 0.05, 0.65), (0.35, 0.05, 0.60),
        (0.40, 0.10, 0.50), (0.40, 0.15, 0.45), (0.42, 0.18, 0.40), (0.40, 0.20, 0.40),
        (0.42, 0.22, 0.36), (0.42, 0.25, 0.33), (0.40, 0.30, 0.30),
        (0.42, 0.30, 0.28), (0.45, 0.30, 0.25), (0.45, 0.32, 0.23),
        (0.45, 0.33, 0.22), (0.48, 0.33, 0.19), (0.48, 0.34, 0.18),
        (0.50, 0.33, 0.17), (0.50, 0.34, 0.16),
        (0.50, 0.35, 0.15), (0.50, 0.35, 0.15), (0.48, 0.37, 0.15), (0.50, 0.35, 0.15),
    ]

    devs = [2, 2, 3, 3, 4, 5, 6, 7, 7, 10, 12, 14, 16, 17, 15, 18, 19, 20, 20, 21, 21, 22, 22, 22]
    use_cases = [2, 2, 3, 3, 4, 5, 6, 8, 7, 8, 10, 12, 12, 14, 12, 14, 14, 15, 15, 16, 16, 16, 16, 16]

    for i in range(24):
        s, o, h = model_mix[i]
        sm, om, hm = make_model_mix(s, o, h)
        target_rev = noise(rev_targets[i], 0.08)
        tokens = tokens_for_revenue(target_rev, sm, om, hm)
        rows.append(make_row('S004', i, tokens, s, o, h, use_cases[i], devs[i]))
    return rows

all_usage_rows.extend(gen_star())


# ── S005: STRONG — LegalLens ──
# Steady B2B growth. Revenue ~$200 → $8-10K/mo. Mostly Sonnet.
def gen_legallens():
    rows = []
    rev_targets = [
        200, 400, 650, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000, 3300,
        3600, 4000, 4300, 4600, 5000, 5400, 5800, 6200, 6600, 7000, 7500, 8000,
    ]
    devs = [2, 3, 3, 3, 4, 4, 5, 5, 5, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 10, 10]
    use_cases = [1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8]

    for i in range(24):
        s = random.uniform(0.68, 0.74)
        o = random.uniform(0.03, 0.07)
        h = 1.0 - s - o
        sm, om, hm = make_model_mix(s, o, h)
        target_rev = noise(rev_targets[i], 0.08)
        tokens = tokens_for_revenue(target_rev, sm, om, hm)
        rows.append(make_row('S005', i, tokens, s, o, h, use_cases[i], devs[i]))
    return rows

all_usage_rows.extend(gen_legallens())


# ── S006: STRONG — SupplyChainIQ ──
# Low 8 months, step-changes at month 9 and 16. Haiku-heavy.
def gen_supplychainiq():
    rows = []
    rev_targets = [
        200, 250, 300, 350, 400, 450, 500, 550,  # m1-8: pre-customer
        3000, 3300, 3600, 3800, 4000, 4200, 4400,  # m9-15: first big customer
        7000, 7500, 7800, 8000, 8200, 8500, 8800, 9000, 9500,  # m16-24: second step
    ]
    devs = [2, 2, 2, 2, 2, 2, 3, 3, 4, 4, 5, 5, 5, 5, 6, 7, 7, 7, 8, 8, 8, 8, 8, 8]
    use_cases = [1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 6, 7, 7, 7, 7, 7, 7]

    for i in range(24):
        h = random.uniform(0.65, 0.75)
        s = random.uniform(0.20, 0.30)
        o = max(0, 1.0 - h - s)
        sm, om, hm = make_model_mix(s, o, h)
        target_rev = noise(rev_targets[i], 0.10)
        tokens = tokens_for_revenue(target_rev, sm, om, hm)
        rows.append(make_row('S006', i, tokens, s, o, h, use_cases[i], devs[i]))
    return rows

all_usage_rows.extend(gen_supplychainiq())


# ── FINE PARTNERS (S007-S015) ──
# $200-2K/mo, flat-ish with ±15% noise, 0-3% CMGR

def gen_fine_rev(sid, base_rev, model_bias, dev_count, use_case_count,
                 seasonal_fn=None, monthly_growth=1.01):
    rows = []
    rev = base_rev
    for i in range(24):
        rev = rev * random.uniform(monthly_growth - 0.015, monthly_growth + 0.015)
        target = noise(rev, 0.15)
        seasonal_mult = seasonal_fn(i) if seasonal_fn else 1.0
        target *= seasonal_mult

        if model_bias == 'haiku':
            h = random.uniform(0.82, 0.95)
            s = random.uniform(0.03, 0.13)
            o = max(0, 1.0 - h - s)
        elif model_bias == 'sonnet':
            s = random.uniform(0.72, 0.88)
            h = random.uniform(0.08, 0.20)
            o = max(0, 1.0 - s - h)
        else:  # mixed
            s = random.uniform(0.40, 0.55)
            h = random.uniform(0.35, 0.50)
            o = max(0, 1.0 - s - h)

        sm, om, hm = make_model_mix(s, o, h)
        tokens = tokens_for_revenue(max(target, 50), sm, om, hm)

        d = dev_count + random.choice([-1, 0, 0, 0, 0, 1]) if dev_count > 1 else dev_count
        d = max(1, d)
        uc = use_case_count + random.choice([-1, 0, 0, 0, 1])
        uc = max(1, uc)
        rows.append(make_row(sid, i, tokens, s, o, h, uc, d))
    return rows


def tutorbot_seasonal(month_idx):
    m = int(MONTHS[month_idx].split('-')[1])
    if m in (7, 8): return random.uniform(0.3, 0.5)
    if m in (9, 10): return random.uniform(1.05, 1.15)
    return 1.0

def retail_seasonal(month_idx):
    m = int(MONTHS[month_idx].split('-')[1])
    if m in (10, 11): return random.uniform(1.8, 2.5)
    if m == 12: return random.uniform(1.3, 1.6)
    if m in (1, 2): return random.uniform(0.7, 0.85)
    return 1.0

# S007 TutorBot: EdTech, ~$800/mo base, Sonnet, seasonal
all_usage_rows.extend(gen_fine_rev('S007', 800, 'sonnet', 2, 2,
                                    seasonal_fn=tutorbot_seasonal, monthly_growth=1.012))

# S008 CodeReview.ai: DevTools, ~$600/mo, mixed
all_usage_rows.extend(gen_fine_rev('S008', 600, 'mixed', 2, 2, monthly_growth=1.008))

# S009 RetailPulse: Retail, ~$500/mo base, Haiku, seasonal Q4
all_usage_rows.extend(gen_fine_rev('S009', 500, 'haiku', 2, 2,
                                    seasonal_fn=retail_seasonal, monthly_growth=1.006))

# S010 ChatAssist: 100% Haiku, ~$600/mo, flat
all_usage_rows.extend(gen_fine_rev('S010', 600, 'haiku', 2, 1, monthly_growth=1.003))

# S011 DataClean: Haiku, ~$400/mo, flat
all_usage_rows.extend(gen_fine_rev('S011', 400, 'haiku', 1, 1, monthly_growth=1.002))

# S012 SalesForge: Sonnet, ~$500/mo, very slight decline
all_usage_rows.extend(gen_fine_rev('S012', 500, 'sonnet', 2, 2, monthly_growth=0.998))

# S013 DocuStream: Mixed, 1 dev, ~$300/mo, flat
all_usage_rows.extend(gen_fine_rev('S013', 300, 'mixed', 1, 1, monthly_growth=1.002))

# S014 PolicyPal: Sonnet, ~$450/mo
all_usage_rows.extend(gen_fine_rev('S014', 450, 'sonnet', 2, 2, monthly_growth=1.008))

# S015 MenuMind: Mixed, ~$350/mo, niche
all_usage_rows.extend(gen_fine_rev('S015', 350, 'mixed', 1, 1, monthly_growth=1.004))


# ── DECLINING (S016-S018) ──

# S016 VoiceAI Labs: grows to ~$2K peak, model downgrade then volume decline
def gen_voiceai():
    rows = []
    rev_targets = [
        500, 800, 1100, 1400, 1700, 1900, 2000, 2100,  # m1-8: growth to peak
        1900, 1700, 1500, 1200,  # m9-12: model shifting, volume starting to drop
        900, 700, 550, 450, 380, 320, 280, 250, 220, 200, 180, 160,  # m13-24: decline
    ]
    # Model: Sonnet → Haiku BEFORE volume drops
    model_mix = [
        (0.65, 0.10, 0.25), (0.65, 0.10, 0.25), (0.63, 0.12, 0.25),
        (0.60, 0.10, 0.30), (0.60, 0.08, 0.32), (0.58, 0.07, 0.35),
        (0.55, 0.05, 0.40), (0.50, 0.05, 0.45),  # m7-8: shift starts
        (0.40, 0.03, 0.57), (0.30, 0.02, 0.68),  # m9-10: big shift
        (0.25, 0.01, 0.74), (0.20, 0.01, 0.79),
        (0.18, 0.00, 0.82), (0.15, 0.00, 0.85), (0.15, 0.00, 0.85),
        (0.12, 0.00, 0.88), (0.10, 0.00, 0.90), (0.10, 0.00, 0.90),
        (0.10, 0.00, 0.90), (0.10, 0.00, 0.90), (0.08, 0.00, 0.92),
        (0.08, 0.00, 0.92), (0.08, 0.00, 0.92), (0.05, 0.00, 0.95),
    ]
    devs = [3, 3, 4, 4, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1]
    use_cases = [2, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1]

    for i in range(24):
        s, o, h = model_mix[i]
        sm, om, hm = make_model_mix(s, o, h)
        target = noise(rev_targets[i], 0.10)
        tokens = tokens_for_revenue(max(target, 20), sm, om, hm)
        rows.append(make_row('S016', i, tokens, s, o, h, use_cases[i], devs[i]))
    return rows

all_usage_rows.extend(gen_voiceai())


# S017 MarketingGPT: early excitement ~$1.5K peak m4, steady decline
def gen_marketinggpt():
    rows = []
    rev_targets = [
        600, 1000, 1300, 1500, 1400, 1200, 1000, 900,
        800, 700, 650, 580, 520, 460, 400, 360, 320, 280, 250, 230, 210, 190, 170, 150,
    ]
    devs = [2, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    use_cases = [2, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    for i in range(24):
        sonnet_frac = max(0.15, 0.70 - i * 0.025)
        haiku_frac = min(0.85, 0.25 + i * 0.025)
        opus_frac = max(0, 0.05 - i * 0.003)
        sm, om, hm = make_model_mix(sonnet_frac, opus_frac, haiku_frac)
        target = noise(rev_targets[i], 0.10)
        tokens = tokens_for_revenue(max(target, 20), sm, om, hm)
        rows.append(make_row('S017', i, tokens, sonnet_frac, opus_frac, haiku_frac,
                             use_cases[i], devs[i]))
    return rows

all_usage_rows.extend(gen_marketinggpt())


# S018 FinBot Analytics: grows to ~$1K, flat, then declining
def gen_finbot():
    rows = []
    rev_targets = [
        200, 400, 600, 800, 950, 1000, 1050, 1100,  # growth phase
        1100, 1050, 1000, 950,  # flat/plateau
        850, 700, 550, 450, 350, 280, 230, 200, 180, 160, 140, 120,  # decline
    ]
    devs = [2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1]
    use_cases = [1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    for i in range(24):
        if i < 8:
            s, o, h = 0.50, 0.15, 0.35
        elif i < 13:
            s, o, h = 0.45, 0.08, 0.47
        else:
            s, o, h = 0.30, 0.02, 0.68
        s += random.uniform(-0.04, 0.04)
        o = max(0, o + random.uniform(-0.02, 0.02))
        h = 1.0 - s - o
        sm, om, hm = make_model_mix(s, o, h)
        target = noise(rev_targets[i], 0.12)
        tokens = tokens_for_revenue(max(target, 20), sm, om, hm)
        rows.append(make_row('S018', i, tokens, s, o, h, use_cases[i], devs[i]))
    return rows

all_usage_rows.extend(gen_finbot())


# ── CHURNED (S019-S021) ──

# S019 QuickDraft: cliff-edge at month 9
def gen_quickdraft():
    rows = []
    rev_targets = [400, 650, 850, 1000, 1100, 1050, 1000, 950]
    devs = [2, 2, 3, 3, 3, 3, 2, 2]
    use_cases = [1, 2, 2, 3, 3, 3, 3, 2]

    for i in range(8):
        s = random.uniform(0.55, 0.65)
        h = random.uniform(0.30, 0.40)
        o = max(0, 1.0 - s - h)
        sm, om, hm = make_model_mix(s, o, h)
        target = noise(rev_targets[i], 0.10)
        tokens = tokens_for_revenue(target, sm, om, hm)
        rows.append(make_row('S019', i, tokens, s, o, h, use_cases[i], devs[i]))

    for i in range(8, 24):
        rows.append(zero_row('S019', i))
    return rows

all_usage_rows.extend(gen_quickdraft())


# S020 AIRecruiter: gradual decline months 7-10 then zero
def gen_airecruiter():
    rows = []
    rev_targets = [300, 500, 700, 850, 900, 850, 650, 400, 200, 60]
    devs = [2, 2, 2, 3, 3, 3, 2, 2, 1, 1]
    use_cases = [1, 2, 2, 2, 3, 3, 2, 2, 1, 1]

    for i in range(10):
        s = random.uniform(0.50, 0.60)
        h = random.uniform(0.35, 0.45)
        o = max(0, 1.0 - s - h)
        sm, om, hm = make_model_mix(s, o, h)
        target = noise(rev_targets[i], 0.12)
        tokens = tokens_for_revenue(max(target, 10), sm, om, hm)
        rows.append(make_row('S020', i, tokens, s, o, h, use_cases[i], devs[i]))

    for i in range(10, 24):
        rows.append(zero_row('S020', i))
    return rows

all_usage_rows.extend(gen_airecruiter())


# S021 PropTech AI: growing well 10 months, cliff (lost funding)
def gen_proptech():
    rows = []
    rev_targets = [300, 600, 1000, 1500, 2100, 2800, 3500, 4200, 5000, 5500]
    devs = [2, 2, 3, 4, 4, 5, 5, 6, 7, 7]
    use_cases = [1, 2, 3, 3, 4, 4, 5, 5, 6, 6]

    for i in range(10):
        s = random.uniform(0.45, 0.55)
        o = random.uniform(0.10, 0.18)
        h = 1.0 - s - o
        sm, om, hm = make_model_mix(s, o, h)
        target = noise(rev_targets[i], 0.08)
        tokens = tokens_for_revenue(target, sm, om, hm)
        rows.append(make_row('S021', i, tokens, s, o, h, use_cases[i], devs[i]))

    for i in range(10, 24):
        rows.append(zero_row('S021', i))
    return rows

all_usage_rows.extend(gen_proptech())


# ── MINIMAL (S022-S023) ──

# S022 NoteAI: 3 calls month 1, 1 call month 2, nothing after
def gen_noteai():
    rows = []
    rows.append(make_row('S022', 0, 5000, 0.5, 0.0, 0.5, 1, 1))
    rows.append(make_row('S022', 1, 1800, 0.5, 0.0, 0.5, 1, 1))
    for i in range(2, 24):
        rows.append(zero_row('S022', i))
    return rows

all_usage_rows.extend(gen_noteai())


# S023 GreenTech AI: sporadic, a few calls every other month, stops after month 16
def gen_greentech():
    rows = []
    for i in range(24):
        if i % 2 == 0 and i < 16:
            t = int(random.uniform(2000, 12000))
            rows.append(make_row('S023', i, t, 0.3, 0.0, 0.7, 1, 1))
        else:
            rows.append(zero_row('S023', i))
    return rows

all_usage_rows.extend(gen_greentech())


# ═══════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════

print("=" * 60)
print("VALIDATION")
print("=" * 60)

errors = 0

# 1. Model pct sums
for row in all_usage_rows:
    if row['total_tokens'] > 0:
        pct_sum = row['sonnet_pct'] + row['opus_pct'] + row['haiku_pct']
        if abs(pct_sum - 1.0) > 0.002:
            print(f"ERROR: {row['startup_id']} {row['month']} pcts sum to {pct_sum}")
            errors += 1

# 2. No negatives
for row in all_usage_rows:
    for k, v in row.items():
        if isinstance(v, (int, float)) and v < 0:
            print(f"ERROR: {row['startup_id']} {row['month']} {k} = {v} (negative)")
            errors += 1

# 3. Revenue matches formula (within 1%)
for row in all_usage_rows:
    if row['total_tokens'] > 0:
        expected = calc_revenue(row['total_tokens'], row['sonnet_pct'], row['opus_pct'], row['haiku_pct'])
        if abs(expected - row['revenue_usd']) > 0.02:
            print(f"ERROR: {row['startup_id']} {row['month']} rev mismatch: {row['revenue_usd']} vs {expected}")
            errors += 1

# Revenue totals
rev_by_partner = {}
for row in all_usage_rows:
    sid = row['startup_id']
    rev_by_partner[sid] = rev_by_partner.get(sid, 0) + row['revenue_usd']

print("\nRevenue by partner (24-month total):")
sorted_rev = sorted(rev_by_partner.items(), key=lambda x: -x[1])
total_rev = sum(v for _, v in sorted_rev)
for sid, rev in sorted_rev:
    name = next(s['startup_name'] for s in startups if s['startup_id'] == sid)
    pct = rev / total_rev * 100
    print(f"  {sid} {name:20s}: ${rev:>12,.2f} ({pct:.1f}%)")

top3_rev = sum(v for _, v in sorted_rev[:3])
top3_pct = top3_rev / total_rev * 100
print(f"\nTop 3 = {top3_pct:.1f}% of total revenue (target: 50-60%)")

# Last month revenue
print("\nDec 2025 revenue:")
for row in all_usage_rows:
    if row['month'] == '2025-12-01' and row['revenue_usd'] > 0:
        name = next(s['startup_name'] for s in startups if s['startup_id'] == row['startup_id'])
        print(f"  {row['startup_id']} {name:20s}: ${row['revenue_usd']:>10,.2f}")

if errors == 0:
    print("\nAll validation checks passed")
else:
    print(f"\n{errors} errors found")


# ═══════════════════════════════════════════════════
# ALSO VALIDATE AGAINST EXISTING DATA
# ═══════════════════════════════════════════════════

# Read existing usage to compute portfolio-level power law with S001-S003 included
existing_rev = {}
usage_path = os.path.join(DATA_DIR, 'monthly_usage.csv')
with open(usage_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sid = row['startup_id']
        existing_rev[sid] = existing_rev.get(sid, 0) + float(row['revenue_usd'])

# Combine
combined_rev = {**existing_rev, **rev_by_partner}
sorted_combined = sorted(combined_rev.items(), key=lambda x: -x[1])
total_combined = sum(v for _, v in sorted_combined)

print("\n\nFULL PORTFOLIO (S001-S023):")
for sid, rev in sorted_combined:
    pct = rev / total_combined * 100
    print(f"  {sid}: ${rev:>12,.2f} ({pct:.1f}%)")

top3_combined = sum(v for _, v in sorted_combined[:3])
top3_combined_pct = top3_combined / total_combined * 100
print(f"\nFull portfolio top 3 = {top3_combined_pct:.1f}% (target: 50-60%)")


# ═══════════════════════════════════════════════════
# WRITE TO CSV FILES (APPEND)
# ═══════════════════════════════════════════════════

startups_path = os.path.join(DATA_DIR, 'startups.csv')
with open(startups_path, 'a', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'startup_id', 'startup_name', 'hq_city', 'country', 'region', 'vertical',
        'stage', 'founding_year', 'onboard_date', 'source', 'tier', 'archetype', 'description'
    ])
    for s in startups:
        writer.writerow(s)
print(f"\nAppended {len(startups)} startups to {startups_path}")

with open(usage_path, 'a', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'startup_id', 'month', 'total_tokens', 'api_calls', 'revenue_usd',
        'sonnet_pct', 'opus_pct', 'haiku_pct', 'unique_use_cases',
        'active_developers', 'avg_latency_ms', 'error_rate'
    ])
    for row in all_usage_rows:
        writer.writerow(row)
print(f"Appended {len(all_usage_rows)} usage rows to {usage_path}")

grants_path = os.path.join(DATA_DIR, 'credit_grants.csv')
with open(grants_path, 'a', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'startup_id', 'grant_date', 'grant_type', 'amount_usd'
    ])
    for g in credit_grants:
        writer.writerow(g)
print(f"Appended {len(credit_grants)} credit grants to {grants_path}")

print("\nDone!")
