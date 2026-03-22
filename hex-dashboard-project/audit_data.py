"""
Comprehensive data integrity audit for hex-dashboard-project.
Checks every data relationship against Tribe Capital growth accounting framework.
READ-ONLY: does not modify any files.
"""

import pandas as pd
import numpy as np
import sys

DATA = '/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/data'

# Load all data
startup_ga = pd.read_csv(f'{DATA}/startup_growth_accounting.csv')
startup_ga['month'] = pd.to_datetime(startup_ga['month'])

monthly_usage = pd.read_csv(f'{DATA}/monthly_usage.csv')
monthly_usage['month'] = pd.to_datetime(monthly_usage['month'])

growth_accounting = pd.read_csv(f'{DATA}/growth_accounting.csv')
growth_accounting['month'] = pd.to_datetime(growth_accounting['month'])

credit_grants = pd.read_csv(f'{DATA}/credit_grants.csv')

cohort_data = pd.read_csv(f'{DATA}/cohort_revenue_ltv.csv')
cohort_data['cohort_month'] = pd.to_datetime(cohort_data['cohort_month'])

unit_economics = pd.read_csv(f'{DATA}/unit_economics.csv')
unit_economics['month'] = pd.to_datetime(unit_economics['month'])

startups = pd.read_csv(f'{DATA}/startups.csv')

# Also recompute dev GA from build_dashboard.py logic
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

# ============================================================
# Audit tracking
# ============================================================
total_pass = 0
total_fail = 0

def report(name, passed, details, rows_checked, failures_list):
    global total_pass, total_fail
    status = "PASS" if passed else "FAIL"
    if passed:
        total_pass += 1
    else:
        total_fail += 1
    print(f"\n{'='*60}")
    print(f"[{name}]")
    print(f"Status: {status}")
    print(f"Details: {details}")
    print(f"Rows checked: {rows_checked}")
    print(f"Failures: {len(failures_list)}")
    if failures_list:
        for f in failures_list[:5]:
            print(f"  - {f}")
        if len(failures_list) > 5:
            print(f"  ... and {len(failures_list) - 5} more")

# ============================================================
# CHECK 1: Revenue Growth Accounting Identity (per startup)
# Revenue(t) = Retained(t) + New(t) + Resurrected(t) + Expansion(t)
# Revenue(t-1) = Retained(t) + Churned(t) + Contraction(t)
# ============================================================

print("\n" + "=" * 60)
print("=== AUDIT REPORT ===")
print("=" * 60)

# --- 1a: Forward identity per startup ---
failures_1a = []
rows_1a = 0
for sid in startup_ga['startup_id'].unique():
    df = startup_ga[startup_ga['startup_id'] == sid].sort_values('month')
    for _, row in df.iterrows():
        rows_1a += 1
        computed = row['retained_revenue'] + row['new_revenue'] + row['expansion_revenue'] + row['resurrected_revenue']
        diff = abs(computed - row['total_revenue'])
        if diff > 1.0:
            failures_1a.append(
                f"{sid} {row['month'].strftime('%Y-%m')}: "
                f"Retained({row['retained_revenue']:.2f}) + New({row['new_revenue']:.2f}) + "
                f"Expansion({row['expansion_revenue']:.2f}) + Resurrected({row['resurrected_revenue']:.2f}) = "
                f"{computed:.2f} vs total_revenue={row['total_revenue']:.2f} (diff={diff:.2f})"
            )

report(
    "1a. Revenue GA Forward Identity (per startup): Rev(t) = Retained + New + Expansion + Resurrected",
    len(failures_1a) == 0,
    "Checks that total_revenue equals sum of components for each startup/month",
    rows_1a,
    failures_1a
)

# --- 1b: Backward identity per startup ---
# Revenue(t-1) = Retained(t) + Churned(t) + Contraction(t)
failures_1b = []
rows_1b = 0
for sid in startup_ga['startup_id'].unique():
    df = startup_ga[startup_ga['startup_id'] == sid].sort_values('month')
    usage_df = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    # First GA row is month index 1 (months_since_onboard=1), so prior revenue is month 0
    for idx in range(len(df)):
        row = df.iloc[idx]
        # Get prior month revenue
        if idx == 0:
            # Prior month is the first month in monthly_usage (month 0, not in GA)
            prior_months = usage_df[usage_df['month'] < row['month']].sort_values('month')
            if len(prior_months) == 0:
                continue
            prior_rev = prior_months.iloc[-1]['revenue_usd']
        else:
            prior_rev = df.iloc[idx - 1]['total_revenue']

        rows_1b += 1
        computed_prior = row['retained_revenue'] + row['churned_revenue'] + row['contraction_revenue']
        diff = abs(computed_prior - prior_rev)
        if diff > 1.0:
            failures_1b.append(
                f"{sid} {row['month'].strftime('%Y-%m')}: "
                f"Retained({row['retained_revenue']:.2f}) + Churned({row['churned_revenue']:.2f}) + "
                f"Contraction({row['contraction_revenue']:.2f}) = {computed_prior:.2f} "
                f"vs prior_revenue={prior_rev:.2f} (diff={diff:.2f})"
            )

report(
    "1b. Revenue GA Backward Identity (per startup): Rev(t-1) = Retained(t) + Churned(t) + Contraction(t)",
    len(failures_1b) == 0,
    "Checks that prior-period revenue equals Retained + Churned + Contraction for each startup/month",
    rows_1b,
    failures_1b
)

# --- 1c: Forward identity at portfolio aggregate ---
agg = startup_ga.groupby('month').agg(
    total_revenue=('total_revenue', 'sum'),
    retained_revenue=('retained_revenue', 'sum'),
    new_revenue=('new_revenue', 'sum'),
    expansion_revenue=('expansion_revenue', 'sum'),
    resurrected_revenue=('resurrected_revenue', 'sum'),
    churned_revenue=('churned_revenue', 'sum'),
    contraction_revenue=('contraction_revenue', 'sum'),
).reset_index().sort_values('month')

failures_1c = []
rows_1c = 0
for _, row in agg.iterrows():
    rows_1c += 1
    computed = row['retained_revenue'] + row['new_revenue'] + row['expansion_revenue'] + row['resurrected_revenue']
    diff = abs(computed - row['total_revenue'])
    if diff > 1.0:
        failures_1c.append(
            f"Portfolio {row['month'].strftime('%Y-%m')}: sum of components = {computed:.2f} vs total = {row['total_revenue']:.2f} (diff={diff:.2f})"
        )

report(
    "1c. Revenue GA Forward Identity (portfolio aggregate)",
    len(failures_1c) == 0,
    "Checks portfolio-level total_revenue = sum of GA components",
    rows_1c,
    failures_1c
)

# --- 1d: Backward identity at portfolio aggregate ---
failures_1d = []
rows_1d = 0
# Build portfolio-level monthly revenue including month 0 for each startup
portfolio_monthly = monthly_usage.groupby('month')['revenue_usd'].sum().sort_index().reset_index()
portfolio_monthly.columns = ['month', 'portfolio_rev']

for idx in range(len(agg)):
    row = agg.iloc[idx]
    # Prior month's portfolio revenue
    prior_month_candidates = portfolio_monthly[portfolio_monthly['month'] < row['month']].sort_values('month')
    if len(prior_month_candidates) == 0:
        continue
    prior_rev = prior_month_candidates.iloc[-1]['portfolio_rev']
    # But we also need to handle the case where not all startups are present
    # Backward identity: for startups present this month, their prior rev sums should match
    # Actually the aggregate backward identity should use the prior month's aggregate GA total_revenue
    # For the first aggregate GA row, prior = month 0 total from monthly_usage
    if idx == 0:
        # Sum of month-0 revenue for all startups whose GA starts this month
        # Actually prior = sum of each startup's prior revenue
        # Let's compute per-startup and sum
        prior_sum = 0
        for sid in startup_ga['startup_id'].unique():
            sdf = startup_ga[startup_ga['startup_id'] == sid].sort_values('month')
            udf = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
            if len(sdf) > 0 and sdf.iloc[0]['month'] == row['month']:
                prior_months = udf[udf['month'] < row['month']]
                if len(prior_months) > 0:
                    prior_sum += prior_months.iloc[-1]['revenue_usd']
            elif len(sdf) > 0 and sdf.iloc[0]['month'] < row['month']:
                # This startup already had GA rows before this month
                matching = sdf[sdf['month'] < row['month']]
                if len(matching) > 0:
                    prior_sum += matching.iloc[-1]['total_revenue']
        prior_rev_agg = prior_sum
    else:
        # Prior month: sum of all startups' total_revenue at month t-1
        # But not all startups may have been active at t-1
        prev_month = agg.iloc[idx - 1]['month']
        prior_rev_agg = 0
        for sid in startup_ga['startup_id'].unique():
            sdf = startup_ga[startup_ga['startup_id'] == sid].sort_values('month')
            this_month_rows = sdf[sdf['month'] == row['month']]
            if len(this_month_rows) == 0:
                continue
            this_row = this_month_rows.iloc[0]
            # Find this startup's prior revenue
            prev_rows = sdf[sdf['month'] < row['month']]
            if len(prev_rows) > 0:
                prior_rev_agg += prev_rows.iloc[-1]['total_revenue']
            else:
                # First GA month for this startup; check monthly_usage
                udf = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
                prior_u = udf[udf['month'] < row['month']]
                if len(prior_u) > 0:
                    prior_rev_agg += prior_u.iloc[-1]['revenue_usd']

    rows_1d += 1
    computed_prior = row['retained_revenue'] + row['churned_revenue'] + row['contraction_revenue']
    diff = abs(computed_prior - prior_rev_agg)
    if diff > 1.0:
        failures_1d.append(
            f"Portfolio {row['month'].strftime('%Y-%m')}: Retained+Churned+Contraction = {computed_prior:.2f} "
            f"vs prior_portfolio_revenue = {prior_rev_agg:.2f} (diff={diff:.2f})"
        )

report(
    "1d. Revenue GA Backward Identity (portfolio aggregate)",
    len(failures_1d) == 0,
    "Checks portfolio-level: prior_revenue = Retained(t) + Churned(t) + Contraction(t)",
    rows_1d,
    failures_1d
)

# ============================================================
# CHECK 2: Developer Growth Accounting Identity
# MAU(t) = Retained(t) + New(t) + Resurrected(t)
# MAU(t-1) = Retained(t) + Churned(t)
# ============================================================

failures_2a = []
rows_2a = 0
for sid in dev_ga['startup_id'].unique():
    df = dev_ga[dev_ga['startup_id'] == sid].sort_values('month')
    for _, row in df.iterrows():
        rows_2a += 1
        computed = row['retained_devs'] + row['new_devs'] + row['resurrected_devs']
        diff = abs(computed - row['active_devs'])
        if diff > 0:
            failures_2a.append(
                f"{sid} {row['month'].strftime('%Y-%m')}: "
                f"Retained({row['retained_devs']}) + New({row['new_devs']}) + "
                f"Resurrected({row['resurrected_devs']}) = {computed} "
                f"vs active_devs={row['active_devs']} (diff={diff})"
            )

report(
    "2a. Developer GA Forward Identity: MAU(t) = Retained + New + Resurrected",
    len(failures_2a) == 0,
    "Checks that active_devs = Retained + New + Resurrected for each startup/month",
    rows_2a,
    failures_2a
)

failures_2b = []
rows_2b = 0
for sid in dev_ga['startup_id'].unique():
    df = dev_ga[dev_ga['startup_id'] == sid].sort_values('month').reset_index(drop=True)
    for idx in range(1, len(df)):
        rows_2b += 1
        row = df.iloc[idx]
        prior_devs = df.iloc[idx - 1]['active_devs']
        computed = row['retained_devs'] + row['churned_devs']
        diff = abs(computed - prior_devs)
        if diff > 0:
            failures_2b.append(
                f"{sid} {row['month'].strftime('%Y-%m')}: "
                f"Retained({row['retained_devs']}) + Churned({row['churned_devs']}) = {computed} "
                f"vs prior MAU={prior_devs} (diff={diff})"
            )

report(
    "2b. Developer GA Backward Identity: MAU(t-1) = Retained(t) + Churned(t)",
    len(failures_2b) == 0,
    "Checks that prior-period active_devs = Retained(t) + Churned(t)",
    rows_2b,
    failures_2b
)

# ============================================================
# CHECK 3: Quick Ratio Consistency
# QR = (New + Resurrected + Expansion) / (Churned + Contraction)
# ============================================================

failures_3 = []
rows_3 = 0
for _, row in startup_ga.iterrows():
    rows_3 += 1
    gains = row['new_revenue'] + row['resurrected_revenue'] + row['expansion_revenue']
    losses = row['churned_revenue'] + row['contraction_revenue']
    if losses > 0:
        expected_qr = round(gains / losses, 2)
    else:
        # If losses are 0, QR should be very large or inf
        expected_qr = None

    stored_qr = row['quick_ratio']

    if expected_qr is not None:
        diff = abs(expected_qr - stored_qr)
        if diff > 0.1:
            failures_3.append(
                f"{row['startup_id']} {row['month'].strftime('%Y-%m')}: "
                f"computed QR = {expected_qr:.2f} vs stored = {stored_qr:.2f} (diff={diff:.2f})"
            )
    else:
        # losses = 0, QR should be very high
        if stored_qr < 100:
            failures_3.append(
                f"{row['startup_id']} {row['month'].strftime('%Y-%m')}: "
                f"losses=0 but QR={stored_qr} (expected very high)"
            )

report(
    "3. Quick Ratio Consistency: QR = (New + Resurrected + Expansion) / (Churned + Contraction)",
    len(failures_3) == 0,
    "Verifies quick_ratio column matches formula for every row",
    rows_3,
    failures_3
)

# ============================================================
# CHECK 4: Gross Retention Consistency
# Gross Retention = Retained / Prior Period Revenue
# ============================================================

failures_4 = []
rows_4 = 0
for sid in startup_ga['startup_id'].unique():
    df = startup_ga[startup_ga['startup_id'] == sid].sort_values('month').reset_index(drop=True)
    udf = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    for idx in range(len(df)):
        row = df.iloc[idx]
        if idx == 0:
            prior_u = udf[udf['month'] < row['month']].sort_values('month')
            if len(prior_u) == 0:
                continue
            prior_rev = prior_u.iloc[-1]['revenue_usd']
        else:
            prior_rev = df.iloc[idx - 1]['total_revenue']

        rows_4 += 1
        if prior_rev > 0:
            expected_gr = round(row['retained_revenue'] / prior_rev * 100, 1)
        else:
            expected_gr = 0

        stored_gr = row['gross_retention_pct']
        diff = abs(expected_gr - stored_gr)
        if diff > 0.5:
            failures_4.append(
                f"{sid} {row['month'].strftime('%Y-%m')}: "
                f"computed GR = {expected_gr:.1f}% vs stored = {stored_gr:.1f}% "
                f"(prior_rev={prior_rev:.2f}, retained={row['retained_revenue']:.2f}, diff={diff:.1f})"
            )

report(
    "4. Gross Retention Consistency: GR = Retained / Prior Revenue * 100",
    len(failures_4) == 0,
    "Verifies gross_retention_pct matches formula for every row",
    rows_4,
    failures_4
)

# ============================================================
# CHECK 5: Net Churn Consistency
# Net Churn = (Churned + Contraction - Resurrected - Expansion) / Prior Revenue
# ============================================================

failures_5 = []
rows_5 = 0
for sid in startup_ga['startup_id'].unique():
    df = startup_ga[startup_ga['startup_id'] == sid].sort_values('month').reset_index(drop=True)
    udf = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    for idx in range(len(df)):
        row = df.iloc[idx]
        if idx == 0:
            prior_u = udf[udf['month'] < row['month']].sort_values('month')
            if len(prior_u) == 0:
                continue
            prior_rev = prior_u.iloc[-1]['revenue_usd']
        else:
            prior_rev = df.iloc[idx - 1]['total_revenue']

        rows_5 += 1
        if prior_rev > 0:
            expected_nc = round((row['churned_revenue'] + row['contraction_revenue']
                               - row['resurrected_revenue'] - row['expansion_revenue'])
                              / prior_rev * 100, 1)
        else:
            expected_nc = 0

        stored_nc = row['net_churn_pct']
        diff = abs(expected_nc - stored_nc)
        if diff > 0.5:
            failures_5.append(
                f"{sid} {row['month'].strftime('%Y-%m')}: "
                f"computed NC = {expected_nc:.1f}% vs stored = {stored_nc:.1f}% "
                f"(prior_rev={prior_rev:.2f}, diff={diff:.1f})"
            )

report(
    "5. Net Churn Consistency: NC = (Churned + Contraction - Resurrected - Expansion) / Prior Revenue * 100",
    len(failures_5) == 0,
    "Verifies net_churn_pct matches formula for every row",
    rows_5,
    failures_5
)

# ============================================================
# CHECK 6: Revenue vs Monthly Usage
# total_revenue in startup_ga matches revenue_usd in monthly_usage
# ============================================================

failures_6 = []
rows_6 = 0
for _, ga_row in startup_ga.iterrows():
    sid = ga_row['startup_id']
    month = ga_row['month']
    usage_match = monthly_usage[(monthly_usage['startup_id'] == sid) & (monthly_usage['month'] == month)]
    rows_6 += 1
    if len(usage_match) == 0:
        failures_6.append(f"{sid} {month.strftime('%Y-%m')}: no matching row in monthly_usage")
    else:
        usage_rev = usage_match.iloc[0]['revenue_usd']
        diff = abs(ga_row['total_revenue'] - usage_rev)
        if diff > 0.01:
            failures_6.append(
                f"{sid} {month.strftime('%Y-%m')}: GA total_revenue={ga_row['total_revenue']:.2f} "
                f"vs usage revenue_usd={usage_rev:.2f} (diff={diff:.2f})"
            )

report(
    "6. Revenue Cross-Check: startup_growth_accounting.total_revenue vs monthly_usage.revenue_usd",
    len(failures_6) == 0,
    "Checks that revenue figures match between the two tables for each startup/month",
    rows_6,
    failures_6
)

# ============================================================
# CHECK 7: Credit Economics
# ============================================================

failures_7 = []
rows_7 = 0
print_lines_7 = []
for sid in startups['startup_id'].unique():
    rows_7 += 1
    total_credits = credit_grants[credit_grants['startup_id'] == sid]['amount_usd'].sum()
    total_rev = monthly_usage[monthly_usage['startup_id'] == sid]['revenue_usd'].sum()
    roi = total_rev / total_credits if total_credits > 0 else 0
    print_lines_7.append(f"  {sid}: credits=${total_credits:,.0f}, total_rev=${total_rev:,.2f}, ROI={roi:.2f}x")

    if roi < 0.01:
        failures_7.append(f"{sid}: ROI={roi:.4f}x seems unreasonably low")
    elif roi > 100:
        failures_7.append(f"{sid}: ROI={roi:.2f}x seems unreasonably high")

detail_7 = "Credit economics summary:\n" + "\n".join(print_lines_7)
report(
    "7. Credit Economics: ROI = total_revenue / total_credits",
    len(failures_7) == 0,
    detail_7,
    rows_7,
    failures_7
)

# ============================================================
# CHECK 8: Token-Revenue Consistency
# Revenue ~= tokens * $10/1M (blended price)
# ============================================================

failures_8 = []
rows_8 = 0
for _, row in monthly_usage.iterrows():
    rows_8 += 1
    expected_rev = row['total_tokens'] * 10 / 1_000_000
    actual_rev = row['revenue_usd']
    if expected_rev > 0:
        ratio = actual_rev / expected_rev
        # Allow generous tolerance: 0.5x to 2.0x given model mix variation
        if ratio < 0.5 or ratio > 2.0:
            failures_8.append(
                f"{row['startup_id']} {row['month'].strftime('%Y-%m')}: "
                f"tokens={row['total_tokens']:,.0f}, expected_rev~${expected_rev:,.2f}, "
                f"actual=${actual_rev:,.2f}, ratio={ratio:.2f}"
            )
    elif actual_rev > 1:
        failures_8.append(
            f"{row['startup_id']} {row['month'].strftime('%Y-%m')}: "
            f"zero tokens but revenue=${actual_rev:.2f}"
        )

report(
    "8. Token-Revenue Consistency: revenue ~= tokens * $10/1M (within 0.5x-2.0x)",
    len(failures_8) == 0,
    "Checks that revenue is approximately tokens * blended price",
    rows_8,
    failures_8
)

# ============================================================
# CHECK 9: Model Mix Percentages
# sonnet_pct + opus_pct + haiku_pct = 1.0
# ============================================================

failures_9 = []
rows_9 = 0
for _, row in monthly_usage.iterrows():
    rows_9 += 1
    total_pct = row['sonnet_pct'] + row['opus_pct'] + row['haiku_pct']
    diff = abs(total_pct - 1.0)
    if diff > 0.001:
        failures_9.append(
            f"{row['startup_id']} {row['month'].strftime('%Y-%m')}: "
            f"sonnet={row['sonnet_pct']}, opus={row['opus_pct']}, haiku={row['haiku_pct']}, "
            f"sum={total_pct:.6f} (diff={diff:.6f})"
        )

report(
    "9. Model Mix: sonnet_pct + opus_pct + haiku_pct = 1.0",
    len(failures_9) == 0,
    "Checks that model mix percentages sum to 1.0 for every row in monthly_usage",
    rows_9,
    failures_9
)

# ============================================================
# CHECK 10: CMGR Computation
# CMGR_N = (end / start)^(1/N) - 1
# ============================================================

# Portfolio-level token consumption series
portfolio_tokens = monthly_usage.groupby('month')['total_tokens'].sum().sort_index()

def cmgr_calc(series, months):
    if len(series) <= months:
        return None
    end = series.iloc[-1]
    start = series.iloc[-(months + 1)]
    return (end / start) ** (1 / months) - 1 if start > 0 else 0

failures_10 = []
rows_10 = 0

for n, label in [(3, 'CMGR3'), (6, 'CMGR6'), (12, 'CMGR12')]:
    rows_10 += 1
    val = cmgr_calc(portfolio_tokens, n)
    if val is not None:
        end_val = portfolio_tokens.iloc[-1]
        start_val = portfolio_tokens.iloc[-(n + 1)]
        expected = (end_val / start_val) ** (1 / n) - 1
        diff = abs(val - expected)
        if diff > 0.0001:
            failures_10.append(f"{label}: computed={val:.6f} vs expected={expected:.6f} (diff={diff:.6f})")
        else:
            pass  # Computation is consistent
    else:
        failures_10.append(f"{label}: not enough data to compute (need > {n} months)")

# Also verify per-startup CMGR makes sense
for sid in ['S001', 'S002', 'S003']:
    u = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    tokens = u['total_tokens']
    for n, label in [(3, 'CMGR3'), (6, 'CMGR6'), (12, 'CMGR12')]:
        rows_10 += 1
        if len(tokens) > n:
            end_v = tokens.iloc[-1]
            start_v = tokens.iloc[-(n + 1)]
            if start_v > 0:
                val = (end_v / start_v) ** (1 / n) - 1
                # Sanity: CMGR should be between -50% and +200%
                if val < -0.5 or val > 2.0:
                    failures_10.append(
                        f"{sid} {label}: CMGR={val:.4f} ({val*100:.1f}%) seems extreme "
                        f"(start={start_v:,.0f}, end={end_v:,.0f})"
                    )

report(
    "10. CMGR Computation: CMGR_N = (end/start)^(1/N) - 1",
    len(failures_10) == 0,
    "Verifies CMGR formula is correctly computed and values are reasonable",
    rows_10,
    failures_10
)

# ============================================================
# CHECK 11: Cohort Data
# - Retention at month 0 = 100%
# - Retention never exceeds 100%
# - Cohort sizes consistent
# ============================================================

# 11a: Revenue retention at age 0
failures_11a = []
rows_11a = 0
for _, row in cohort_data[cohort_data['age_months'] == 0].iterrows():
    rows_11a += 1
    # logo_retention_pct at age 0 should be 100%
    if abs(row['logo_retention_pct'] - 100.0) > 0.5:
        failures_11a.append(
            f"{row['startup_id']} cohort {row['cohort_month']}: "
            f"logo_retention at month 0 = {row['logo_retention_pct']}% (expected 100%)"
        )

report(
    "11a. Cohort: Logo retention at month 0 = 100%",
    len(failures_11a) == 0,
    "Checks that logo_retention_pct is 100% at age_months=0",
    rows_11a,
    failures_11a
)

# 11b: Revenue retention at age 0 (revenue_retention_pct)
failures_11b = []
rows_11b = 0
for _, row in cohort_data[cohort_data['age_months'] == 0].iterrows():
    rows_11b += 1
    # revenue_retention_pct at age 0 should be ~100%
    if row['revenue_retention_pct'] > 110:
        failures_11b.append(
            f"{row['startup_id']} cohort {row['cohort_month']}: "
            f"revenue_retention at month 0 = {row['revenue_retention_pct']}% (exceeds 110%)"
        )

report(
    "11b. Cohort: Revenue retention at month 0 is reasonable",
    len(failures_11b) == 0,
    "Checks that revenue_retention_pct at age_months=0 does not wildly exceed 100%",
    rows_11b,
    failures_11b
)

# 11c: Logo retention should not exceed 100%
failures_11c = []
rows_11c = 0
for _, row in cohort_data.iterrows():
    rows_11c += 1
    if row['logo_retention_pct'] > 100.5:
        failures_11c.append(
            f"{row['startup_id']} cohort {row['cohort_month']} age {row['age_months']}: "
            f"logo_retention = {row['logo_retention_pct']}% (exceeds 100%)"
        )

report(
    "11c. Cohort: Logo retention never exceeds 100%",
    len(failures_11c) == 0,
    "Checks no logo_retention_pct row exceeds 100%",
    rows_11c,
    failures_11c
)

# 11d: Cohort sizes consistent within same startup/cohort_month
failures_11d = []
rows_11d = 0
cohort_groups = cohort_data.groupby(['startup_id', 'cohort_month'])
for (sid, cm), group in cohort_groups:
    rows_11d += 1
    sizes = group['cohort_size'].unique()
    if len(sizes) > 1:
        failures_11d.append(
            f"{sid} cohort {cm}: multiple cohort_size values: {list(sizes)}"
        )

report(
    "11d. Cohort: Cohort sizes are consistent within groups",
    len(failures_11d) == 0,
    "Checks that cohort_size doesn't vary within the same startup/cohort_month",
    rows_11d,
    failures_11d
)

# 11e: active_users at age 0 should equal cohort_size
failures_11e = []
rows_11e = 0
for _, row in cohort_data[cohort_data['age_months'] == 0].iterrows():
    rows_11e += 1
    if row['active_users'] != row['cohort_size']:
        failures_11e.append(
            f"{row['startup_id']} cohort {row['cohort_month']}: "
            f"active_users={row['active_users']} vs cohort_size={row['cohort_size']} at age 0"
        )

report(
    "11e. Cohort: active_users equals cohort_size at month 0",
    len(failures_11e) == 0,
    "Checks that at age_months=0, active_users == cohort_size",
    rows_11e,
    failures_11e
)

# ============================================================
# CHECK 12: Time Series Continuity
# - No gaps in monthly data
# - All startups have same date range
# - Months are sequential
# ============================================================

failures_12a = []
rows_12a = 0
for sid in monthly_usage['startup_id'].unique():
    df = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    months = df['month'].tolist()
    rows_12a += len(months)
    for i in range(1, len(months)):
        expected = months[i - 1] + pd.DateOffset(months=1)
        if months[i] != expected:
            failures_12a.append(
                f"{sid}: gap between {months[i-1].strftime('%Y-%m')} and {months[i].strftime('%Y-%m')} "
                f"(expected {expected.strftime('%Y-%m')})"
            )

report(
    "12a. Time Series: No gaps in monthly_usage",
    len(failures_12a) == 0,
    "Checks that each startup has consecutive monthly data with no gaps",
    rows_12a,
    failures_12a
)

# 12b: Check if startups have the same date range
failures_12b = []
rows_12b = 0
date_ranges = {}
for sid in monthly_usage['startup_id'].unique():
    df = monthly_usage[monthly_usage['startup_id'] == sid].sort_values('month')
    rows_12b += 1
    first = df['month'].min()
    last = df['month'].max()
    n_months = len(df)
    date_ranges[sid] = (first, last, n_months)

# Check all have same end date (they may have different start dates due to onboarding)
end_dates = set(v[1] for v in date_ranges.values())
if len(end_dates) > 1:
    failures_12b.append(f"Different end dates across startups: {dict((k, v[1].strftime('%Y-%m')) for k, v in date_ranges.items())}")

detail_12b = "Date ranges per startup:\n"
for sid, (first, last, n) in date_ranges.items():
    detail_12b += f"  {sid}: {first.strftime('%Y-%m')} to {last.strftime('%Y-%m')} ({n} months)\n"

report(
    "12b. Time Series: All startups have same end date",
    len(failures_12b) == 0,
    detail_12b.strip(),
    rows_12b,
    failures_12b
)

# 12c: GA months match usage months (minus month 0)
failures_12c = []
rows_12c = 0
for sid in startup_ga['startup_id'].unique():
    ga_months = set(startup_ga[startup_ga['startup_id'] == sid]['month'])
    usage_months = set(monthly_usage[monthly_usage['startup_id'] == sid]['month'])
    # GA should have all usage months except the first one
    first_usage = min(usage_months)
    expected_ga_months = usage_months - {first_usage}
    rows_12c += 1
    missing_in_ga = expected_ga_months - ga_months
    extra_in_ga = ga_months - expected_ga_months
    if missing_in_ga:
        failures_12c.append(f"{sid}: months in usage but not in GA: {sorted([m.strftime('%Y-%m') for m in missing_in_ga])}")
    if extra_in_ga:
        failures_12c.append(f"{sid}: months in GA but not in usage: {sorted([m.strftime('%Y-%m') for m in extra_in_ga])}")

report(
    "12c. Time Series: GA months = Usage months minus month 0",
    len(failures_12c) == 0,
    "Checks that startup_growth_accounting has rows for all non-first usage months",
    rows_12c,
    failures_12c
)

# ============================================================
# CHECK BONUS: Portfolio growth_accounting.csv consistency
# Verify it matches aggregated startup_growth_accounting.csv
# ============================================================

failures_bonus = []
rows_bonus = 0

# The growth_accounting.csv appears to be portfolio-level GA
# Check if its values match the aggregated startup_ga
agg_for_check = startup_ga.groupby('month').agg(
    new_revenue=('new_revenue', 'sum'),
    expansion_revenue=('expansion_revenue', 'sum'),
    contraction_revenue=('contraction_revenue', 'sum'),
    churned_revenue=('churned_revenue', 'sum'),
    resurrected_revenue=('resurrected_revenue', 'sum'),
).reset_index()

for _, ga_row in growth_accounting.iterrows():
    month = ga_row['month']
    rows_bonus += 1
    agg_match = agg_for_check[agg_for_check['month'] == month]
    if len(agg_match) == 0:
        failures_bonus.append(f"{month.strftime('%Y-%m')}: no matching aggregated data")
        continue
    agg_r = agg_match.iloc[0]
    for col in ['new_revenue', 'expansion_revenue', 'contraction_revenue', 'churned_revenue', 'resurrected_revenue']:
        diff = abs(ga_row[col] - agg_r[col])
        if diff > 1.0:
            failures_bonus.append(
                f"{month.strftime('%Y-%m')} {col}: growth_accounting.csv={ga_row[col]:.2f} "
                f"vs aggregated startup_ga={agg_r[col]:.2f} (diff={diff:.2f})"
            )

report(
    "BONUS. Portfolio growth_accounting.csv vs aggregated startup_growth_accounting.csv",
    len(failures_bonus) == 0,
    "Checks that growth_accounting.csv matches the sum of startup_growth_accounting.csv",
    rows_bonus,
    failures_bonus
)

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("=== SUMMARY ===")
print("=" * 60)
print(f"Total checks: {total_pass + total_fail}")
print(f"PASSED: {total_pass}")
print(f"FAILED: {total_fail}")
if total_fail == 0:
    print("\nAll data integrity checks passed.")
else:
    print(f"\n{total_fail} check(s) have integrity issues that need investigation.")
print("=" * 60)
