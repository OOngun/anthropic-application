# Measuring What Matters: A Growth Accounting Framework for Anthropic's EMEA Startup Partnerships

*Ongun Ozdemir — March 2026*

---

## What This Is

This document presents an analytical framework for measuring the health and ROI of Anthropic's startup credit program in EMEA. It adapts Tribe Capital's growth accounting methodology — originally designed for assessing product-market fit in SaaS companies — to the specific context of API consumption partnerships.

The accompanying dashboard is a working prototype built with synthetic data. The data is illustrative, not real. The framework is the point.

---

## The Problem

Anthropic's startup partnerships team deploys credits to early-stage companies building on Claude's API. The core question is simple: **is this investment working?**

But "working" has layers:
- Are partners actually using the API, or did they take credits and go quiet?
- Are they growing, or have they plateaued?
- Is growth coming from genuine adoption, or just one developer running a batch job?
- When credits run out, do they convert to paid, or disappear?
- Across the whole portfolio, are we getting better at picking winners?

A single metric can't answer these. Revenue is a lagging indicator. Token volume alone doesn't distinguish between a startup that's scaling and one that's running an inefficient pipeline. Developer count doesn't tell you if those developers are building production features or running experiments.

What we need is a decomposition — a way to break aggregate numbers into their components so we can see what's actually driving change.

---

## The Framework

### Source: Tribe Capital's "Diligence at Social Capital"

Tribe Capital (originally Social Capital) developed a standardised quantitative framework for assessing product-market fit. The framework uses three analyses:

1. **Growth Accounting** — decompose growth into retained, new, resurrected, expanded, contracted, and churned components
2. **Cohort Analysis** — track groups of users/customers over time to measure retention, LTV, and behavioural patterns
3. **Distribution Analysis** — examine concentration and engagement depth across the customer base

The framework's power comes from treating these as **accounting identities**, not models. The components must sum to the total. There's no fudge factor. If growth looks healthy but is entirely driven by one component (e.g. new users masking high churn), the decomposition reveals it immediately.

**Reference implementations:**
- [SQL queries (Social Capital)](https://gist.github.com/hsurreal/4062f2639d4bb6fab6fb)
- [Essay: A Quantitative Approach to Product-Market Fit](https://tribecap.co/essays/a-quantitative-approach-to-product-market-fit)

### Adaptation to API Partnerships

The original framework analyses a company's customers. We're analysing **Anthropic's** customers — startup partners consuming the Claude API. The unit of measurement shifts:

| Tribe Capital (SaaS) | Our Adaptation (API Partnerships) |
|---|---|
| Monthly Active Users | Active Developers (distinct API keys with ≥1 call/30d) |
| Revenue per customer | Revenue per partner (tokens × model pricing) |
| Customer cohorts | Developer cohorts within each partner |
| Churn = customer leaves | Churn = developer stops calling the API |
| Expansion = customer upgrades | Expansion = developer uses more tokens or upgrades model |

**Key difference:** Anthropic's pricing is flat per-token per model. There are no volume discounts at the standard tier. Revenue scales linearly with token consumption for a given model. The non-linearity comes from model choice — Haiku ($1/MTok input) vs Sonnet ($3/MTok) vs Opus ($5/MTok) — not from volume tiers.

This means expansion in revenue comes from three sources:
1. More tokens (more API calls, more features built)
2. Model upgrades (Haiku → Sonnet = 3× price per token)
3. New developers joining (more API keys active)

And contraction comes from:
1. Fewer tokens (reduced usage)
2. Model downgrades (Sonnet → Haiku, often a pre-churn signal)
3. Developers leaving (API keys going inactive)

---

## What We Can Actually Measure

A critical constraint: we only have access to data Anthropic can directly observe. We cannot see partner internals.

**Available:**
| Data | Source |
|---|---|
| Token consumption (input/output, by model) | API logs |
| Revenue per partner per month | Billing |
| API call volume, latency, error rates | API logs |
| Active API keys per partner | API logs |
| Credits granted, consumed, remaining | Credit ledger |
| Workspace members (if using Console) | Console |

**Not available:**
- Partner's ARR, burn rate, runway, headcount
- Their end-user metrics or customer count
- LTV of their customers
- Whether they're also using OpenAI/Google (competitive intel)

This constraint shapes the entire framework. We measure what we can see and avoid pretending we know what we can't.

---

## Dashboard Architecture: Three-Tier Progressive Disclosure

The dashboard is structured in three tiers, each serving a different decision:

### Tier 1: Ecosystem Pulse
**Question:** "Is the overall portfolio healthy this week?"
**Time to answer:** Under 10 seconds.

Four headline metrics:
- **Active Partners** — how many partners called the API in the last 30 days
- **Quick Ratio** — (new + resurrected + expansion) / (churned + contraction). Above 1 = growing.
- **Net API Churn** — are we losing more revenue than we're gaining from existing partners? Negative = good.
- **Gross Retention** — what % of last month's revenue survived without any new business

Plus a growth accounting waterfall showing the latest month's decomposition, and CMGR (Compound Monthly Growth Rate) trailing lines to spot acceleration or deceleration.

**Design principle:** Nothing at Tier 1 that doesn't change a decision at the portfolio level. LTV curves, cohort heatmaps, and per-partner details don't belong here — they're Tier 3.

### Tier 2: Partner List
**Question:** "Which partners need my attention?"
**Purpose:** Navigation layer, not analysis layer.

A sortable, filterable table with one row per partner. Columns: Revenue, Active Developers, ROI, CMGR-3, Quick Ratio, Gross Retention, Last Active. Color-coded cells (green/amber/red) based on thresholds.

Clicking a row navigates to that partner's detail view. The table's job is to route you — it doesn't replace deep analysis.

### Tier 3: Partner Detail
**Question:** "What's happening with this specific partner, and what should I do about it?"

Full drill-down per company, organised in collapsible sections:
1. **Growth Overview** — revenue growth accounting (the Tribe Capital stacked bar), quick ratio, revenue & token trends
2. **Developer Adoption** — developer growth accounting, developer quick ratio, cohort retention
3. **Cohort Analysis** — LTV heatmap (red-to-blue, Tribe Capital style), retention heatmap, LTV curves
4. **Revenue by Model** — model mix evolution, revenue split by Haiku/Sonnet/Opus
5. **Adoption & Reliability** — API calls, latency, error rates

---

## Key Metrics Defined

### CMGR (Compound Monthly Growth Rate)
```
CMGR = (V_end / V_start) ^ (1/n) - 1
```
Trailing 3, 6, and 12-month windows. If CMGR-3 < CMGR-12, growth has decelerated — an important signal to surface.

We use CMGR rather than CAGR because monthly granularity is more honest for early-stage partners. CAGR from a $100 base produces meaninglessly large numbers.

### Growth Accounting Identity
```
Revenue(t) = Retained + New + Expansion + Resurrected
Revenue(t-1) = Retained + Churned + Contraction
```
These are not estimates. They're accounting identities computed from developer-level activity data.

### Quick Ratio
```
QR = (New + Resurrected + Expansion) / (Churned + Contraction)
```
Below 1 = shrinking. 1-2 = moderate. Above 2 = healthy. Above 4 = very strong.

### Gross Retention
```
GR = Retained Revenue / Prior Period Revenue
```
Computed at the developer level within each partner, not at the partner level. This matters — a partner whose total revenue grew can still have poor developer-level retention if new developers are masking churn.

### Active Developers
Defined as distinct API keys with ≥1 API call in the trailing 30 days. This is a simplification — the mapping between API keys and actual developers is ambiguous. We acknowledge this and use it consistently.

---

## The Credit Program as a CAC Play

The startup credit program follows a classic land-and-expand investment thesis:

1. **Land** — deploy credits to remove the cost barrier
2. **Integrate** — startup builds features on Claude's API. Every integration increases switching cost.
3. **Lock-in** — prompts, workflows, and team knowledge are Claude-specific. Migration is painful.
4. **Convert** — credits exhaust, startup starts paying
5. **Expand** — usage scales with the startup's growth. Revenue compounds.

The dashboard measures each stage: activation speed (land), developer growth (integrate), model mix depth (lock-in), credit exhaustion timing (convert), and CMGR trajectory (expand).

---

## Portfolio Composition

The synthetic portfolio models 23 partners with a realistic power-law distribution:

| Archetype | Count | Revenue Share | Behaviour |
|---|---|---|---|
| Star | 1 | ~35% | Exceptional growth, portfolio returner |
| Strong | 2 | ~20% | Solid growth, converting to paid |
| Fine | 9 | ~30% | Using API, not growing much. The long tail. |
| Declining | 3 | ~8% | Were fine, now trending down |
| Churned | 5 | ~5% | Gone — pivoted, ran out of money, or switched provider |
| Minimal | 3 | ~2% | Got credits, barely used them |

This is deliberately realistic. Most startups in a credit program don't become breakout successes — they're the quiet middle that doesn't generate much signal. The dashboard needs to handle this gracefully, surfacing the star while not drowning in noise from the long tail.

---

## Limitations and Honest Gaps

**Synthetic data.** All partner data is generated for demonstration. Real API consumption patterns would differ in texture — more noise, more edge cases, different scale.

**Developer-level decomposition is simulated.** We simulate individual developer activity within each partner to produce realistic GA charts. In production, this would come from actual API key-level logs.

**No competitive signal.** We can't see if a partner is also using OpenAI or Google. A sudden drop in our usage might be competitive displacement, but we can't confirm it from our data alone.

**Token vs Revenue GA not yet separated.** Ideally we'd run growth accounting on both token volume and revenue independently, then compare. The gap reveals model mix effects. Currently only revenue GA is implemented.

**Credit economics are simplified.** In practice, credit grants vary by stage, tier, and negotiation. The dashboard assumes uniform grants for simplicity.

**"Active Developer" is a proxy.** API keys ≠ developers. This is acknowledged throughout and noted in tooltips.

---

## What This Demonstrates

For the Anthropic EMEA Startup Partnerships role, this project demonstrates:

1. **Analytical rigour** — adapting an established VC framework (Tribe Capital) to a novel context (API partnerships), understanding where it applies and where it breaks
2. **Data thinking** — being honest about what data is available vs. what we'd need, and building only on what's real
3. **Dashboard design** — three-tier progressive disclosure, each level serving a different decision, no analytical vanity charts
4. **Product sense** — understanding the credit program as a CAC investment, not a charity programme
5. **Technical execution** — self-contained HTML/JS dashboard with Plotly, pure CSS pulse section, Python data generation, all version-controlled

The framework is the deliverable. The dashboard is evidence that the framework works.

---

## References

- [A Quantitative Approach to Product-Market Fit — Tribe Capital](https://tribecap.co/essays/a-quantitative-approach-to-product-market-fit)
- [Growth Accounting & LTV SQL — Social Capital](https://gist.github.com/hsurreal/4062f2639d4bb6fab6fb)
- [Anthropic API Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
