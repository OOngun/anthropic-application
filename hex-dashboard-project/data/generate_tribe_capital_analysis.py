"""
Generate Tribe Capital-style analytical tables for the 3 startup case studies.

Based on:
- "A Quantitative Approach to Product-Market Fit" (Tribe Capital)
- "Unit Economics and the Pursuit of Scale Invariance" (Tribe Capital)
- Social Capital Diligence Series Parts 1-6

Produces:
1. cohort_revenue_ltv.csv — Monthly cohort LTV curves (cumulative revenue per user cohort)
2. cohort_retention.csv — Monthly revenue retention % and logo retention %
3. unit_economics.csv — gm × LTV_n - CAC payback analysis per startup
4. revenue_distribution.csv — CDF of revenue concentration (Pareto analysis)
5. engagement_depth.csv — L28-style depth of usage metrics
"""

import pandas as pd
import numpy as np

np.random.seed(42)

OUTPUT_DIR = '/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/data'

# Load base data
startups = pd.read_csv(f'{OUTPUT_DIR}/startups.csv')
monthly_usage = pd.read_csv(f'{OUTPUT_DIR}/monthly_usage.csv')
monthly_usage['month'] = pd.to_datetime(monthly_usage['month'])
startups['onboard_date'] = pd.to_datetime(startups['onboard_date'])
credits = pd.read_csv(f'{OUTPUT_DIR}/credit_grants.csv')

# ============================================================
# 1. COHORT REVENUE LTV — cumulative revenue per "user cohort"
#    Each startup's end-customers are grouped by signup month.
#    We simulate 6 monthly cohorts per startup.
# ============================================================

cohort_ltv_rows = []

for _, s in startups.iterrows():
    sid = s['startup_id']
    archetype = s['archetype']
    usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')

    if len(usage) == 0:
        continue

    # Simulate end-customer cohorts (the startup's own customers using their Claude-powered product)
    # Each month of the startup's life, they acquire a cohort of end-users
    n_months = len(usage)

    # Cohort size depends on archetype and growth
    if archetype == 'rocket':
        base_cohort_size = 150
        cohort_growth_rate = 0.12  # 12% more users each month
        retention_curve = [1.0, 0.72, 0.62, 0.56, 0.52, 0.50, 0.48, 0.47, 0.46, 0.46, 0.45, 0.45]
        expansion_factor = 1.08  # 8% revenue expansion per period for retained users
    elif archetype == 'steady':
        base_cohort_size = 80
        cohort_growth_rate = 0.04
        retention_curve = [1.0, 0.65, 0.55, 0.48, 0.44, 0.42, 0.40, 0.39, 0.38, 0.37, 0.37, 0.36]
        expansion_factor = 1.03
    else:  # declining
        base_cohort_size = 100
        cohort_growth_rate = -0.02
        retention_curve = [1.0, 0.55, 0.40, 0.32, 0.26, 0.22, 0.19, 0.17, 0.15, 0.14, 0.13, 0.12]
        expansion_factor = 0.95  # contraction

    # Average revenue per user in month 0 (derived from startup's actual revenue)
    first_month_rev = usage.iloc[0]['revenue_usd'] if len(usage) > 0 else 100
    if archetype == 'rocket':
        arpu_month0 = np.random.uniform(15, 30)
    elif archetype == 'steady':
        arpu_month0 = np.random.uniform(25, 45)
    else:
        arpu_month0 = np.random.uniform(10, 20)

    # Generate cohorts for each month the startup is active
    for cohort_idx in range(min(n_months, 18)):  # max 18 cohorts
        cohort_month = usage.iloc[cohort_idx]['month']
        cohort_size = max(10, int(base_cohort_size * (1 + cohort_growth_rate) ** cohort_idx + np.random.normal(0, 10)))

        cumulative_revenue = 0
        for age in range(min(12, n_months - cohort_idx)):  # max 12 months of aging
            # Retention: use curve with noise
            if age < len(retention_curve):
                ret = retention_curve[age] + np.random.normal(0, 0.02)
            else:
                ret = retention_curve[-1] + np.random.normal(0, 0.01)
            ret = np.clip(ret, 0.05, 1.0)

            # Revenue per retained user: ARPU × expansion
            arpu = arpu_month0 * (expansion_factor ** age) + np.random.normal(0, 1)
            arpu = max(1, arpu)

            # Active users this period
            active_users = int(cohort_size * ret)

            # Period revenue
            period_revenue = active_users * arpu
            cumulative_revenue += period_revenue

            # Logo retention (slightly higher than revenue retention for declining, lower for rocket with expansion)
            logo_ret = ret + np.random.normal(0, 0.015)
            logo_ret = np.clip(logo_ret, 0.05, 1.0)

            # Revenue retention relative to month 0
            month0_revenue = cohort_size * arpu_month0
            revenue_retention = period_revenue / month0_revenue if month0_revenue > 0 else 0

            cohort_ltv_rows.append({
                'startup_id': sid,
                'cohort_month': cohort_month,
                'cohort_size': cohort_size,
                'age_months': age,
                'active_users': active_users,
                'period_revenue': round(period_revenue, 2),
                'cumulative_revenue': round(cumulative_revenue, 2),
                'ltv_per_user': round(cumulative_revenue / cohort_size, 2),
                'revenue_retention_pct': round(revenue_retention * 100, 1),
                'logo_retention_pct': round(logo_ret * 100, 1),
            })

cohort_ltv = pd.DataFrame(cohort_ltv_rows)
cohort_ltv.to_csv(f'{OUTPUT_DIR}/cohort_revenue_ltv.csv', index=False)

# ============================================================
# 2. UNIT ECONOMICS — gm × LTV_n - CAC payback
#    Per Tribe Capital's framework:
#    - CAC = credits invested / startup (our "acquisition cost")
#    - LTV_n = cumulative revenue at month n
#    - gm = Anthropic's gross margin on API revenue (~60-70%)
# ============================================================

ANTHROPIC_GROSS_MARGIN = 0.65  # estimated — GPU costs are ~30-40% of revenue

ue_rows = []

for _, s in startups.iterrows():
    sid = s['startup_id']
    usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    creds = credits[credits['startup_id'] == sid]['amount_usd'].sum()

    if len(usage) == 0:
        continue

    cumulative_rev = 0
    for idx, (_, u) in enumerate(usage.iterrows()):
        cumulative_rev += u['revenue_usd']
        gm_ltv = ANTHROPIC_GROSS_MARGIN * cumulative_rev
        contribution_margin = gm_ltv - creds
        payback_achieved = contribution_margin >= 0

        ue_rows.append({
            'startup_id': sid,
            'month': u['month'],
            'months_since_onboard': idx,
            'monthly_revenue': round(u['revenue_usd'], 2),
            'cumulative_revenue': round(cumulative_rev, 2),
            'gm_x_ltv': round(gm_ltv, 2),
            'cac_credits': creds,
            'contribution_margin': round(contribution_margin, 2),
            'payback_achieved': payback_achieved,
            'gross_margin': ANTHROPIC_GROSS_MARGIN,
        })

unit_economics = pd.DataFrame(ue_rows)
unit_economics.to_csv(f'{OUTPUT_DIR}/unit_economics.csv', index=False)

# ============================================================
# 3. REVENUE DISTRIBUTION — Pareto / CDF analysis
#    "What % of customers generate what % of revenue?"
#    We simulate the startup's end-customer revenue distribution
# ============================================================

distribution_rows = []

for _, s in startups.iterrows():
    sid = s['startup_id']
    archetype = s['archetype']
    usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')

    if len(usage) < 6:
        continue

    # Take a snapshot at month 6 and latest month
    for snapshot_label, month_idx in [('month_6', 5), ('latest', len(usage) - 1)]:
        if month_idx >= len(usage):
            continue

        snapshot_month = usage.iloc[month_idx]['month']
        monthly_rev = usage.iloc[month_idx]['revenue_usd']

        # Simulate individual customer revenue distribution
        if archetype == 'rocket':
            # Power law: few big customers, long tail
            n_customers = np.random.randint(80, 200)
            # Pareto distribution (alpha=1.5 → moderate concentration)
            raw = np.random.pareto(1.8, n_customers) + 1
            customer_revenues = raw / raw.sum() * monthly_rev
        elif archetype == 'steady':
            # More uniform, enterprise-heavy (fewer, bigger customers)
            n_customers = np.random.randint(30, 80)
            raw = np.random.pareto(2.5, n_customers) + 1
            customer_revenues = raw / raw.sum() * monthly_rev
        else:
            # Highly concentrated — few customers dominate, rest tiny
            n_customers = np.random.randint(40, 100)
            raw = np.random.pareto(1.2, n_customers) + 1
            customer_revenues = raw / raw.sum() * monthly_rev

        # Sort descending for CDF
        customer_revenues = np.sort(customer_revenues)[::-1]
        cumulative = np.cumsum(customer_revenues)
        total = cumulative[-1]

        for i, (rev, cum_rev) in enumerate(zip(customer_revenues, cumulative)):
            percentile = (i + 1) / n_customers * 100
            cum_pct = cum_rev / total * 100

            distribution_rows.append({
                'startup_id': sid,
                'snapshot': snapshot_label,
                'snapshot_month': snapshot_month,
                'customer_rank': i + 1,
                'n_customers': n_customers,
                'customer_percentile': round(percentile, 1),
                'customer_revenue': round(rev, 2),
                'cumulative_revenue': round(cum_rev, 2),
                'cumulative_revenue_pct': round(cum_pct, 1),
            })

distribution = pd.DataFrame(distribution_rows)
distribution.to_csv(f'{OUTPUT_DIR}/revenue_distribution.csv', index=False)

# ============================================================
# 4. ENGAGEMENT DEPTH — L28 style
#    "How many days per 28-day period are end-users active?"
#    Power user curve / histogram
# ============================================================

engagement_rows = []

for _, s in startups.iterrows():
    sid = s['startup_id']
    archetype = s['archetype']
    usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')

    if len(usage) < 3:
        continue

    for snapshot_label, month_idx in [('early', 2), ('mid', min(len(usage) - 1, 9)), ('latest', len(usage) - 1)]:
        if month_idx >= len(usage):
            continue

        snapshot_month = usage.iloc[month_idx]['month']
        active_devs = usage.iloc[month_idx]['active_developers']
        n_users = max(active_devs * np.random.randint(5, 15), 50)  # end users, not devs

        # Generate L28 distribution (days active out of 28)
        if archetype == 'rocket':
            # Bimodal: power users (20+ days) and casual (3-8 days)
            power_users = int(n_users * 0.25)
            casual_users = n_users - power_users
            days_power = np.clip(np.random.normal(22, 3, power_users), 1, 28).astype(int)
            days_casual = np.clip(np.random.normal(8, 4, casual_users), 1, 28).astype(int)
            all_days = np.concatenate([days_power, days_casual])
        elif archetype == 'steady':
            # More uniform, concentrated around 10-15 days
            all_days = np.clip(np.random.normal(12, 5, n_users), 1, 28).astype(int)
        else:
            # Skewed low — most users barely active
            all_days = np.clip(np.random.exponential(4, n_users), 1, 28).astype(int)

        # Create histogram (days 1-28)
        for day in range(1, 29):
            count = (all_days == day).sum()
            pct = count / n_users * 100
            engagement_rows.append({
                'startup_id': sid,
                'snapshot': snapshot_label,
                'snapshot_month': snapshot_month,
                'days_active_l28': day,
                'user_count': count,
                'user_pct': round(pct, 1),
                'total_users': n_users,
            })

        # Also add summary stats
        engagement_rows.append({
            'startup_id': sid,
            'snapshot': snapshot_label,
            'snapshot_month': snapshot_month,
            'days_active_l28': -1,  # sentinel for summary row
            'user_count': n_users,
            'user_pct': 0,
            'total_users': n_users,
        })

engagement = pd.DataFrame(engagement_rows)
engagement.to_csv(f'{OUTPUT_DIR}/engagement_depth.csv', index=False)

# ============================================================
# 5. GROWTH ACCOUNTING (enhanced — per Tribe Capital format)
#    Decompose at startup level, not just portfolio level
# ============================================================

# Per-startup growth accounting
startup_ga_rows = []

for _, s in startups.iterrows():
    sid = s['startup_id']
    usage = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')

    if len(usage) < 2:
        continue

    # Simulate end-customer level growth accounting
    # (Since we have aggregate startup revenue, we decompose it into
    #  new/expansion/contraction/churn components)

    archetype = s['archetype']

    for i in range(1, len(usage)):
        curr_rev = usage.iloc[i]['revenue_usd']
        prev_rev = usage.iloc[i - 1]['revenue_usd']
        month = usage.iloc[i]['month']

        delta = curr_rev - prev_rev

        if archetype == 'rocket':
            # Mostly expansion, small new, minimal contraction
            new_pct = np.random.uniform(0.25, 0.40)
            expansion_pct = np.random.uniform(0.45, 0.65)
            resurrected_pct = np.random.uniform(0.02, 0.08)
            churn_pct = np.random.uniform(0.01, 0.04)
            contraction_pct = np.random.uniform(0.02, 0.06)
        elif archetype == 'steady':
            new_pct = np.random.uniform(0.15, 0.30)
            expansion_pct = np.random.uniform(0.30, 0.50)
            resurrected_pct = np.random.uniform(0.03, 0.08)
            churn_pct = np.random.uniform(0.03, 0.08)
            contraction_pct = np.random.uniform(0.05, 0.12)
        else:  # declining
            new_pct = np.random.uniform(0.05, 0.15)
            expansion_pct = np.random.uniform(0.10, 0.25)
            resurrected_pct = np.random.uniform(0.01, 0.05)
            churn_pct = np.random.uniform(0.10, 0.20)
            contraction_pct = np.random.uniform(0.15, 0.30)

        # Normalise gains
        total_gain_pct = new_pct + expansion_pct + resurrected_pct
        new_pct /= total_gain_pct
        expansion_pct /= total_gain_pct
        resurrected_pct /= total_gain_pct

        # Normalise losses
        total_loss_pct = churn_pct + contraction_pct
        churn_pct /= total_loss_pct
        contraction_pct /= total_loss_pct

        # Scale to actual revenue
        # Gains are a % of current revenue, losses are a % of prior revenue
        gain_base = curr_rev * np.random.uniform(0.08, 0.20) if archetype != 'declining' else curr_rev * np.random.uniform(0.03, 0.08)
        loss_base = prev_rev * np.random.uniform(0.02, 0.08) if archetype != 'declining' else prev_rev * np.random.uniform(0.08, 0.18)

        new_rev = gain_base * new_pct
        expansion_rev = gain_base * expansion_pct
        resurrected_rev = gain_base * resurrected_pct
        churned_rev = loss_base * churn_pct
        contraction_rev = loss_base * contraction_pct

        # Retained = what's left
        retained = prev_rev - churned_rev - contraction_rev

        # Quick ratio
        gains = new_rev + expansion_rev + resurrected_rev
        losses = churned_rev + contraction_rev
        qr = gains / losses if losses > 1 else float('inf')

        # Gross retention
        gross_ret = retained / prev_rev if prev_rev > 0 else 0

        startup_ga_rows.append({
            'startup_id': sid,
            'month': month,
            'months_since_onboard': i,
            'total_revenue': round(curr_rev, 2),
            'retained_revenue': round(retained, 2),
            'new_revenue': round(new_rev, 2),
            'expansion_revenue': round(expansion_rev, 2),
            'resurrected_revenue': round(resurrected_rev, 2),
            'churned_revenue': round(churned_rev, 2),
            'contraction_revenue': round(contraction_rev, 2),
            'quick_ratio': round(min(qr, 20), 2),  # cap at 20 for display
            'gross_retention_pct': round(gross_ret * 100, 1),
            'net_churn_pct': round((losses - gains) / prev_rev * 100, 1) if prev_rev > 0 else 0,
        })

startup_growth_accounting = pd.DataFrame(startup_ga_rows)
startup_growth_accounting.to_csv(f'{OUTPUT_DIR}/startup_growth_accounting.csv', index=False)

# ============================================================
# SUMMARY
# ============================================================

print("=" * 60)
print("TRIBE CAPITAL ANALYSIS TABLES GENERATED")
print("=" * 60)

print(f"\n1. cohort_revenue_ltv.csv: {len(cohort_ltv)} rows")
print(f"   Cohorts per startup: {cohort_ltv.groupby('startup_id')['cohort_month'].nunique().to_dict()}")

print(f"\n2. unit_economics.csv: {len(unit_economics)} rows")
for sid in ['S001', 'S002', 'S003']:
    ue = unit_economics[unit_economics['startup_id'] == sid]
    payback = ue[ue['payback_achieved']].iloc[0]['months_since_onboard'] if ue['payback_achieved'].any() else 'Never'
    name = startups[startups['startup_id'] == sid].iloc[0]['startup_name']
    cac = ue.iloc[0]['cac_credits']
    final_margin = ue.iloc[-1]['contribution_margin']
    print(f"   {name}: CAC=${cac:,.0f}, payback at month {payback}, final margin=${final_margin:,.0f}")

print(f"\n3. revenue_distribution.csv: {len(distribution)} rows")
for sid in ['S001', 'S002', 'S003']:
    d = distribution[(distribution['startup_id'] == sid) & (distribution['snapshot'] == 'latest')]
    if len(d) > 0:
        name = startups[startups['startup_id'] == sid].iloc[0]['startup_name']
        top20_pct = d[d['customer_percentile'] <= 20]['cumulative_revenue_pct'].max()
        n_cust = d.iloc[0]['n_customers']
        print(f"   {name}: {n_cust} customers, top 20% = {top20_pct:.0f}% of revenue")

print(f"\n4. engagement_depth.csv: {len(engagement)} rows")

print(f"\n5. startup_growth_accounting.csv: {len(startup_growth_accounting)} rows")
for sid in ['S001', 'S002', 'S003']:
    ga = startup_growth_accounting[startup_growth_accounting['startup_id'] == sid]
    name = startups[startups['startup_id'] == sid].iloc[0]['startup_name']
    avg_qr = ga['quick_ratio'].mean()
    avg_gross_ret = ga['gross_retention_pct'].mean()
    print(f"   {name}: avg QR={avg_qr:.1f}, avg gross retention={avg_gross_ret:.0f}%")

print(f"\nAll files saved to: {OUTPUT_DIR}/")
