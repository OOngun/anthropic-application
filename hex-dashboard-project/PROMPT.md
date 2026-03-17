# Hex Dashboard Project — Anthropic Startup Partnerships EMEA

## Context

I'm applying for the **Startup Partnerships - EMEA** role at Anthropic (London, £160K-£215K). The job description requires **"SQL proficiency and ability to build Hex dashboards independently"** and includes responsibilities like **"Design Hex dashboards and SQL queries for analytics and ROI measurement."**

## What the Role Actually Needs

In this role, I'd be analyzing **individual startup partners** to prioritize which partnerships drive the most Claude usage/revenue. The Hex dashboards are operational tools for:
- Tracking startup growth metrics (MRR, usage, API consumption)
- Cohort analysis (retention, churn, expansion)
- Identifying which startups to invest time in vs. deprioritize
- Measuring ROI of partnership programs

This is **NOT** about mapping the entire EMEA ecosystem. It's about showing I can build the kind of dashboard a Startup Partnerships person would use day-to-day to manage their book of startup accounts.

## Goal

Build a Hex dashboard that analyzes a **single startup's growth data** — the way I would in the role to evaluate whether a startup partner is worth deepening the relationship with. This proves:
1. I can build Hex dashboards with SQL (they asked for it)
2. I understand the analytical lens of the role (growth, churn, usage, cohort analysis)
3. I can work with data independently

## What is Hex?

Hex (hex.tech) is a collaborative data workspace used by Anthropic's GTM team. It combines:
- SQL queries against connected databases
- Python/pandas cells for transformation
- Built-in charts, tables, and layout tools
- Interactive filters (dropdowns, date pickers, etc.)
- Shareable dashboard views

Hex has a **free tier** and built-in templates including a cohort analysis template at hex.tech/templates/reporting/cohort-analysis/

## Data Source

### Option: RavenStack SaaS Dataset (Kaggle — FREE, MIT License)
**URL:** https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset

A synthetic but realistic SaaS startup dataset simulating an AI-powered collaboration platform. Perfect fit because:
- It represents a **single startup** (exactly what we need)
- 5 CSV files with rich, joinable data
- Covers all the metrics a Startup Partnerships person would analyze

#### Files included:
| File | What it covers |
|------|---------------|
| `accounts.csv` | Customer metadata (company info, plan, signup date) |
| `subscriptions.csv` | Subscription lifecycles, revenue, upgrades/downgrades |
| `feature_usage.csv` | Daily product interaction logs (API usage proxy) |
| `support_tickets.csv` | Support activity and satisfaction scores |
| `churn_events.csv` | Churn dates, reasons, refund behaviors |

#### Key analyses this enables:
- MRR growth over time
- Trial-to-paid conversion rates
- Cohort retention curves
- Churn analysis (why, when, which segments)
- Feature adoption patterns
- Revenue expansion vs. contraction
- Customer segmentation by plan/usage

### Why this works
- I have access to private startup growth data through my VC work, but can't share it
- This synthetic dataset is realistic and purpose-built for exactly this kind of analysis
- It lets me demonstrate the analytical skills without needing proprietary data
- The dashboard itself is the proof of skill — the data just needs to be realistic

## Dashboard Structure (3-4 Pages)

### Page 1: Startup Health Overview
- **KPI cards**: Total MRR, Active accounts, Churn rate, Net Revenue Retention
- **Line chart**: MRR growth over time
- **Bar chart**: New vs. churned accounts by month
- **Filter bar**: Date range, Plan type

### Page 2: Cohort Analysis & Retention
- **Cohort heatmap**: Monthly retention by signup cohort
- **Line chart**: Retention curves by plan tier
- **Table**: Cohort-level metrics (size, retention at M3/M6/M12, LTV)
- **SQL showcase**: The cohort query demonstrates intermediate-to-advanced SQL (window functions, date math, pivoting)

### Page 3: Usage & Expansion Signals
- **Feature adoption chart**: Which features correlate with retention
- **Scatter plot**: Usage intensity vs. revenue (identifies expansion candidates)
- **Table**: Top accounts by usage growth (these are the ones to double down on)
- **Churn risk flags**: Accounts with declining usage

### Page 4: Strategic Recommendations
- **Tiered segmentation**: High-value / Growth / At-risk accounts
- **Churn driver analysis**: Top reasons for churn by segment
- **Expansion opportunity**: Accounts ripe for upsell based on usage patterns
- **Methodology notes**: SQL queries used, data sources, limitations

## SQL Queries to Write (Show Skill)

```sql
-- 1. Monthly Recurring Revenue trend
SELECT
  DATE_TRUNC('month', subscription_start) AS month,
  SUM(monthly_revenue) AS mrr,
  COUNT(DISTINCT account_id) AS active_accounts
FROM subscriptions
WHERE status = 'active'
GROUP BY 1
ORDER BY 1;

-- 2. Cohort retention analysis (window functions)
WITH cohorts AS (
  SELECT
    account_id,
    DATE_TRUNC('month', first_subscription_date) AS cohort_month,
    DATE_TRUNC('month', activity_date) AS active_month
  FROM feature_usage f
  JOIN accounts a USING (account_id)
),
cohort_sizes AS (
  SELECT cohort_month, COUNT(DISTINCT account_id) AS cohort_size
  FROM cohorts
  GROUP BY 1
)
SELECT
  c.cohort_month,
  cs.cohort_size,
  EXTRACT(MONTH FROM AGE(c.active_month, c.cohort_month)) AS months_since_signup,
  COUNT(DISTINCT c.account_id) AS retained,
  ROUND(COUNT(DISTINCT c.account_id)::NUMERIC / cs.cohort_size * 100, 1) AS retention_pct
FROM cohorts c
JOIN cohort_sizes cs ON c.cohort_month = cs.cohort_month
GROUP BY 1, 2, 3
ORDER BY 1, 3;

-- 3. Churn analysis by reason and plan
SELECT
  s.plan_type,
  ce.churn_reason,
  COUNT(*) AS churned_accounts,
  ROUND(AVG(s.monthly_revenue), 2) AS avg_revenue_lost,
  ROUND(AVG(DATE_PART('day', ce.churn_date - s.subscription_start)), 0) AS avg_days_active
FROM churn_events ce
JOIN subscriptions s USING (account_id)
GROUP BY 1, 2
ORDER BY churned_accounts DESC;

-- 4. Usage-based expansion signals
SELECT
  a.account_id,
  a.company_name,
  s.plan_type,
  s.monthly_revenue,
  COUNT(f.event_id) AS total_events_30d,
  LAG(COUNT(f.event_id)) OVER (
    PARTITION BY a.account_id
    ORDER BY DATE_TRUNC('month', f.activity_date)
  ) AS prev_month_events,
  ROUND(
    (COUNT(f.event_id)::NUMERIC /
     NULLIF(LAG(COUNT(f.event_id)) OVER (
       PARTITION BY a.account_id
       ORDER BY DATE_TRUNC('month', f.activity_date)
     ), 0) - 1) * 100, 1
  ) AS usage_growth_pct
FROM accounts a
JOIN subscriptions s USING (account_id)
JOIN feature_usage f USING (account_id)
WHERE f.activity_date >= CURRENT_DATE - INTERVAL '60 days'
GROUP BY 1, 2, 3, 4, DATE_TRUNC('month', f.activity_date)
HAVING COUNT(f.event_id) > 10
ORDER BY usage_growth_pct DESC NULLS LAST;

-- 5. Net Revenue Retention by cohort
WITH monthly_revenue AS (
  SELECT
    DATE_TRUNC('month', a.created_at) AS cohort_month,
    DATE_TRUNC('month', s.billing_date) AS revenue_month,
    SUM(s.monthly_revenue) AS revenue
  FROM accounts a
  JOIN subscriptions s USING (account_id)
  GROUP BY 1, 2
)
SELECT
  cohort_month,
  revenue_month,
  revenue,
  FIRST_VALUE(revenue) OVER (PARTITION BY cohort_month ORDER BY revenue_month) AS initial_revenue,
  ROUND(revenue / FIRST_VALUE(revenue) OVER (PARTITION BY cohort_month ORDER BY revenue_month) * 100, 1) AS nrr_pct
FROM monthly_revenue
ORDER BY cohort_month, revenue_month;
```

## Step-by-Step Build Plan

### Phase 1: Data Setup (30 min)
- [ ] Download RavenStack dataset from Kaggle
- [ ] Review CSV structures and column names
- [ ] Adjust SQL queries to match actual column names

### Phase 2: Hex Setup (30 min)
- [ ] Create free Hex account (hex.tech)
- [ ] Upload CSVs as data sources
- [ ] Familiarise with Hex interface (SQL cells, chart cells, layout)
- [ ] Check out the built-in cohort analysis template for inspiration

### Phase 3: Build Dashboard (2-3 hours)
- [ ] Page 1: Startup health overview with KPI cards and MRR chart
- [ ] Page 2: Cohort analysis with retention heatmap
- [ ] Page 3: Usage analysis and expansion signals
- [ ] Page 4: Strategic recommendations and methodology

### Phase 4: Polish (1 hour)
- [ ] Clean design (Anthropic aesthetic — minimal, clear)
- [ ] Add insight callouts ("This cohort shows X, suggesting Y")
- [ ] Add narrative context: "As a Startup Partnerships lead, I'd use this to..."
- [ ] Test all filters and interactions
- [ ] Create shareable link

## How to Reference in Application

> "To demonstrate my Hex and SQL capabilities, I built a startup analytics dashboard — the kind of tool I'd use in the role to evaluate and prioritize startup partnerships. It tracks MRR growth, cohort retention, churn drivers, and usage-based expansion signals. I used a synthetic SaaS dataset since real portfolio data is confidential, but the analytical framework reflects how I'd approach partnership prioritization at Anthropic. Here's the link: [hex.tech/...]"

This shows:
1. SQL proficiency with real analytical queries (cohorts, window functions, CTEs)
2. Hex dashboard skills (they asked for it)
3. Understanding of what the role actually involves day-to-day
4. VC-trained analytical lens (growth metrics, retention, unit economics)
5. Professional judgment (synthetic data because real data is confidential)
