# Data Generation Plan — Realistic Synthetic Startup Partners

## Objective

Generate 20 additional startup partners with realistic API usage time series that simulate how real startups actually behave when given API credits. The data should produce a portfolio that follows power law dynamics — most partners generate minimal value, 1-2 generate disproportionate returns.

## Guiding Principles

1. **Startups mostly fail.** The default outcome is not growth — it's stagnation or churn. The data should reflect this.
2. **Usage is lumpy, not smooth.** Real API usage has spikes (demo day, launch, investor meeting), dips (team holidays, pivots, rewrites), and plateaus (waiting for funding, hiring).
3. **Model choice tells a story.** A startup on 100% Haiku is running a cost-sensitive batch job. One mixing Sonnet + Opus is building something complex. One that migrates FROM Opus TO Haiku is optimising costs (good sign — they're scaling). One that migrates from Sonnet to nothing churned.
4. **Developer count is a leading indicator.** Devs joining = building more features. Devs leaving = the project is deprioritised. Dev count often leads revenue by 1-2 months.
5. **Credit exhaustion is a decision point.** When credits run out, the startup either converts to paid (they value Claude) or goes silent (they don't). This moment should be visible in the data.

## The 23-Partner Portfolio

All partners onboard in **Jan 2024**. Same 24-month window (Jan 2024 – Dec 2025). This makes cohort analysis clean.

### Distribution

| # | Archetype | Partners | Portfolio revenue share |
|---|---|---|---|
| 1 | Star | 1 | ~35-40% |
| 2 | Strong | 2 | ~20-25% |
| 3 | Steady | 3 | ~15% |
| 4 | Flat | 4 | ~10% |
| 5 | Declining | 4 | ~5% |
| 6 | Churned | 5 | ~3% |
| 7 | Minimal | 4 | ~2% |

### Archetype Specifications

#### 1. STAR (1 partner) — "NovaMed AI"
**Narrative:** AI-powered clinical trial matching. Found PMF around month 6. Raised Series A at month 10 which accelerated hiring. Now their largest product feature runs entirely on Claude.

- **Token trajectory:** Starts at ~50K tokens/mo. Slow for 5 months (experimenting). Inflection at month 6. Exponential from month 6-18. Slight plateau months 19-24 as they hit infrastructure scaling limits then resume.
- **Revenue:** Follows tokens. Should reach $30-40K/mo by month 24.
- **CMGR-3:** Should be 12-18% in recent months.
- **Model mix:** Starts 80% Haiku / 20% Sonnet. By month 12: 40% Sonnet / 30% Opus / 30% Haiku. By month 24: 50% Sonnet / 35% Opus / 15% Haiku. The shift to Opus signals they're doing complex medical reasoning tasks.
- **Developers:** 2 → 5 → 12 → 18 → 22. Steady climb with a jump at Series A (month 10).
- **Credits:** $50K grant. Exhausted at month 14. Converted to paid immediately — no gap.
- **API calls:** High and growing. 500K+/mo by end.
- **Events:** Spike at month 8 (launched beta). Dip at month 15 (migrating infrastructure). Resume growth month 16.

#### 2. STRONG (2 partners)

**Partner A — "LegalLens"**
**Narrative:** Contract analysis tool for law firms. Steady growth, not explosive. Very consistent daily usage (production integration). Conservative model choices.

- Tokens: 20K → 150K → grows to ~$12-15K/mo revenue
- CMGR-3: 6-9%
- Model: 70% Sonnet throughout. They found what works and stuck with it.
- Devs: 3 → 8 → 10. Slow steady growth.
- Credits: $25K. Exhausted month 18. Converted.
- Notable: Very low error rate. Very consistent daily volume (weekday-heavy, drops on weekends — they're a B2B tool).

**Partner B — "SupplyChainIQ"**
**Narrative:** Logistics optimisation. Started slow, then landed a large customer at month 9 that drove significant expansion. Growth is customer-driven, not organic.

- Tokens: Low for 8 months. Step-change at month 9. Another step at month 16.
- Revenue: $500/mo for months 1-8. Jumps to $5K at month 9. $10K by month 24.
- CMGR-3: Variable — high during step-changes, flat between.
- Model: Haiku-heavy (batch processing logistics data). Some Sonnet for summarisation.
- Devs: 2 → 3 → 6 → 8. Grows in steps matching their customer wins.
- Credits: $25K. Still on credits at month 24 (Haiku is cheap — credits last longer).

#### 3. STEADY (3 partners)

**Partner C — "TutorBot"**
Education AI tutor. Moderate consistent growth. Seasonal pattern — usage drops in summer (European school calendar: Jul-Aug dip).
- Revenue: $200 → $3-4K/mo
- CMGR-3: 4-6%
- Model: 90% Sonnet. Education needs quality, not speed.
- Devs: 2 → 5. Stable.
- August dips are visible and consistent across both years.

**Partner D — "CodeReview.ai"**
Developer tool. Usage correlates with developer hiring cycles. Grows with the market.
- Revenue: $300 → $2-3K/mo
- CMGR-3: 3-5%
- Model: Mixed — Haiku for linting, Sonnet for explanations.
- Devs: 3 → 4 → 5. Barely growing but very stable.

**Partner E — "RetailPulse"**
Retail analytics. Seasonal — Q4 spike (Black Friday prep), Q1 dip. Otherwise flat-ish growth.
- Revenue: $400 → $2K/mo with Q4 spikes to $4K
- Clear seasonal pattern in the data.
- Model: Haiku-heavy (data processing).

#### 4. FLAT (4 partners)

These partners got credits, built something, but never really grew. They're using Claude but it's not central to their product.

**Partner F — "ChatAssist"** — Customer support chatbot. $500-800/mo. Flat for 18 months. 2 devs. 100% Haiku.
**Partner G — "DataClean"** — Data cleaning tool. $300-500/mo. Flat. 1-2 devs. Haiku only.
**Partner H — "SalesBot"** — Sales email generator. $400-600/mo. Slight decline. 2 devs. Sonnet.
**Partner I — "DocuSign AI"** — Document automation. $200-400/mo. Flat with noise. 1 dev.

These should all feel "meh" — not failing, but not winning either. Credits still have balance remaining because usage is so low.

#### 5. DECLINING (4 partners)

These were promising early on but something went wrong — lost a key developer, product pivot, competitive pressure.

**Partner J — "VoiceAI"** — Voice transcription. Grew to $2K/mo, then declined to $400/mo over 6 months. Lost to Whisper/OpenAI. Model mix shifted from Sonnet to Haiku before decline (cost-cutting signal before churn).
**Partner K — "MarketingGPT"** — Content generation. Early excitement ($1.5K/mo), then steady decline. The space got commoditised.
**Partner L — "FinBot"** — Financial analysis. Grew to $1K/mo, then flat, then declining. Regulatory concerns slowed their roadmap.
**Partner M — "HealthChat"** — Patient chatbot. $800/mo peak, now $200/mo. Lost their main customer.

Key pattern: declining partners often show **model downgrade before volume decline**. They move from Sonnet/Opus to Haiku, then eventually to nothing. Developer count drops 1-2 months before revenue drops.

#### 6. CHURNED (5 partners)

Completely stopped using the API. Various churn patterns:

**Partner N — "QuickDraft"** — Content tool. Active for 8 months, then cliff-edge churn at month 9. Zero usage from month 9 onwards. Classic "switched to competitor" pattern.
**Partner O — "AIRecruiter"** — Hiring tool. Gradual decline over 4 months, then zero. Slow death — probably deprioritised the AI feature.
**Partner P — "TravelBot"** — Travel booking. Active 6 months, sporadic for 2, then gone. Startup likely ran out of funding.
**Partner Q — "FoodTech"** — Recipe/meal planning. Active 4 months, churned. Very low usage throughout — never really integrated deeply.
**Partner R — "PropTech AI"** — Real estate. Active for 10 months with decent growth, then sudden cliff. Interesting case — they were growing, something external happened (acquisition? pivot? lost funding?).

Churn patterns should vary:
- Cliff (N, R): last month has normal usage, next month is zero
- Gradual (O, M): 3-4 months of declining before hitting zero
- Sporadic death (P): intermittent usage getting less frequent before stopping

#### 7. MINIMAL (4 partners)

Got credits, barely used them. These are the "signed up but never really built anything" partners.

**Partner S — "NoteAI"** — Made 3 API calls in month 1. 1 call in month 2. Nothing since. $2 total revenue.
**Partner T — "SketchAI"** — Used the API for a hackathon (month 3 spike), never came back. $50 total.
**Partner U — "GreenTech"** — Sporadic: a few calls every other month. Someone is testing but never shipping. $100 total.
**Partner V — "EduQuiz"** — Month 1: moderate usage. Month 2: half. Month 3: nothing. Classic evaluation that didn't convert.

## Per-Partner Data to Generate

For each of the 20 new partners, Claude should generate:

### 1. startups.csv row
```
startup_id, name, vertical, stage, location, total_employees, description
```
- IDs: S004 through S023
- Locations spread across EMEA: London, Paris, Berlin, Amsterdam, Stockholm, Tel Aviv, Dublin, Zurich, Barcelona, Lagos
- Stages: Seed (minimal/churned), Series A (flat/steady), Series B (strong/star)
- Verticals: HealthTech, LegalTech, EdTech, FinTech, DevTools, Logistics, Marketing, HR, Retail, PropTech, FoodTech, CleanTech, Travel

### 2. monthly_usage.csv rows (24 rows per partner)
```
startup_id, month, total_tokens, api_calls, revenue_usd, sonnet_pct, opus_pct, haiku_pct, unique_use_cases, active_developers, avg_latency_ms, error_rate
```

**Critical constraints:**
- `sonnet_pct + opus_pct + haiku_pct = 1.0` (must sum to exactly 1)
- `revenue_usd` should be derived from tokens × blended price (not random). Use: `revenue = tokens × (sonnet_pct × $15 + opus_pct × $75 + haiku_pct × $1) / 1_000_000` for input tokens (approximate)
- `api_calls` should correlate with tokens (avg ~1000-3000 tokens per call)
- `active_developers` should never exceed `total_employees`
- `avg_latency_ms` should be 350-550ms range (realistic for Claude API)
- `error_rate` should be 0.01-0.03 (1-3%)
- Churned months should have ALL ZEROS (tokens, calls, revenue, devs all 0)
- For minimal partners, most months should be zeros or near-zeros

### 3. credit_grants.csv rows
```
startup_id, grant_date, amount_usd, program_tier
```
- Stars/Strong: $50-100K, growth tier
- Steady: $25-50K, growth tier
- Flat/Declining: $10-25K, standard tier
- Churned/Minimal: $10-15K, standard tier
- grant_date: 2024-01-01 for all (same cohort)

### 4. DO NOT generate separate GA CSVs
Growth accounting will be computed at build time from monthly_usage.csv. This guarantees the identity holds.

## Validation Checklist

After generation, verify:
- [ ] All model percentages sum to 1.0 per row
- [ ] Revenue ≈ tokens × blended price (within 10%)
- [ ] Churned partners have zero rows after churn month
- [ ] Developer count ≤ total_employees
- [ ] No negative values anywhere
- [ ] Portfolio follows power law: top 3 partners = 50-60% of total revenue
- [ ] Seasonal patterns are visible (Aug dip for education, Q4 spike for retail)
- [ ] Credit exhaustion timing is realistic (high-usage partners exhaust faster)
- [ ] CMGR-3 values are in reasonable ranges (-20% to +30%)
- [ ] The partner list has a mix of green/amber/red when colour-coded

## Generation Strategy

1. Generate partner metadata first (names, verticals, stages, locations)
2. For each partner, generate the 24-month time series one at a time, following the archetype narrative
3. Validate each partner's data against constraints before moving on
4. After all 20 are generated, run portfolio-level validation
5. Append to existing CSVs (don't overwrite S001-S003)
6. Rebuild dashboard and verify visually
