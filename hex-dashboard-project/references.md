# Hex Dashboard Project — Reference Sources

## Analytical Frameworks

### Tribe Capital / Social Capital (Jonathan Hsu)

#### 1. A Quantitative Approach to Product-Market Fit
- **URL:** https://tribecap.co/essays/a-quantitative-approach-to-product-market-fit
- **Core idea:** PMF is a spectrum, not binary. Three standardised analyses to measure it.
- **Three analyses:**
  1. **Growth Accounting** — decompose revenue/user changes into: New, Churned, Resurrected, Expansion, Contraction, Retained
  2. **Cohort Analysis** — group by acquisition timing, track LTV, revenue retention, logo retention
  3. **Distribution of PMF** — CDFs plotting customer concentration vs revenue concentration (80/20 analysis)
- **Key metrics:** Gross Retention, Quick Ratio, Net Churn
- **Key formula:** Growth_rate ~ New_rate – Net_churn

#### 2. Unit Economics and the Pursuit of Scale Invariance
- **URL:** https://tribecap.co/essays/unit-economics-and-the-pursuit-of-scale-invariance
- **Core idea:** Find parameters robust to scale. Core equation: **gm × LTV – CAC**
- **Key concept:** Payback period = when gm × LTV_n = CAC
- **Scale invariance:** If payback stays constant as you deploy more capital, you have real PMF
- **Benchmarks:** B2B SaaS under 6 months payback = solid, 2+ years = concerning
- **Key distinction:** Use empirical LTV (observed), not inferred LTV (modelled from churn rates)

#### 3. Diligence at Social Capital — Full 6-Part Series + Epilogue
All by Jonathan Hsu, published on Medium (The Startup):

| Part | Title | URL | Core Content |
|------|-------|-----|-------------|
| 1 | Accounting for User Growth | https://medium.com/swlh/diligence-at-social-capital-part-1-accounting-for-user-growth-4a8a449fddfc | Growth accounting for MAU: new, churned, resurrected. Quick Ratio for users. |
| 2 | Accounting for Revenue Growth | https://medium.com/swlh/diligence-at-social-capital-part-2-accounting-for-revenue-growth-551fa07dd972 | Same framework applied to MRR: MRR(t+1) = MRR(t) + new + expansion - churned - contraction |
| 3 | Cohorts and (Revenue) LTV | https://medium.com/swlh/diligence-at-social-capital-part-3-cohorts-and-revenue-ltv-ab65a07464e1 | Empirical cohort LTV curves. Four types: flat, sub-linear, linear, super-linear. Track cumulative revenue per cohort. LTV weakens as cohorts get bigger = demand elasticity signal. |
| 4 | Cohorts and (Engagement) LTV | https://medium.com/swlh/diligence-at-social-capital-part-4-cohorts-and-engagement-ltv-80b4fa7f8e41 | Same LTV framework applied to engagement (DAU, sessions, actions). Pre-monetisation companies. |
| 5 | Depth of Engagement and Quality of Revenue | https://medium.com/swlh/diligence-at-social-capital-part-5-depth-of-usage-and-quality-of-revenue-b4dd96b47ca6 | Full distribution of engagement depth (not just DAU/MAU ratio). Distribution of contract values (not just ACV). CDFs reveal concentration risk. |
| Epilogue | The 8-Ball and GAAP for Startups | https://medium.com/swlh/diligence-at-social-capital-epilogue-introducing-the-8-ball-and-gaap-for-startups-7ab215c378bc | The "8-ball" = growth accounting + cohort behaviour + distribution of PMF, all measured on the core unit of value. Proposed as GAAP-equivalent for startups. |

**The 8-Ball Framework (summary):**
Three analytical lenses applied to the business's core unit of value:
1. **Growth Accounting** — how is the top-line growing? (Income Statement equivalent)
2. **Cohort Behaviour** — how do customer groups behave over time? (Balance Sheet equivalent)
3. **Distribution of PMF** — how concentrated is value? (quality check)

These two statements (Growth Accounting + Cohort) are like Income Statement + Balance Sheet — two views of the same business that cross-check each other.

---

### David Sacks (Craft Ventures)

#### 4. The Burn Multiple
- **URL:** https://sacks.substack.com/p/the-burn-multiple-51a7e43cb200
- **Formula:** **Burn Multiple = Net Burn / Net New ARR**
- **Benchmarks:** Seed ~3x, Series A ~2x, Series B+ approaching 1x, goal is 0x (profitable growth)
- **Why it matters:** Catch-all diagnostic — reveals gross margin problems, sales inefficiency, churn, execution gaps
- **Key advantage:** Adjusts to most recent period, doesn't penalise past mistakes

#### 5. The Give-to-Get Model for AI Startups
- **URL:** https://sacks.substack.com/p/the-give-to-get-model-for-ai-startups
- **Core idea:** Users contribute data to platform in exchange for AI-powered services. Creates data flywheel and network effects.
- **Relevance to Anthropic:** This is essentially what the credits program does — give startups free API access (credits) to get usage data, feedback, and eventual paid conversion.

#### 6. What is Bottom-Up SaaS
- **URL:** https://sacks.substack.com/p/what-is-bottom-up-saas
- **Core idea:** Target individual users/teams, not enterprises. Product-led growth → freemium → virality → grassroots adoption → enterprise upsell.
- **6 characteristics:** Product-led growth, freemium/trial, virality & network effects, grassroots adoption, self-service, expansion & upselling
- **Relevance to Anthropic:** Claude API adoption is classic bottom-up SaaS — developers try it, teams adopt it, company scales up.

#### 7. The Pipeline Metrics That Matter
- **URL:** https://sacks.substack.com/p/the-pipeline-metrics-that-matter
- **Three categories:**
  1. **Pipeline Generation:** Opportunities created, pipeline value, win rate (~20% benchmark)
  2. **Pipeline Conversion:** Sales cycle length, cohorted win rates, stage conversion rates, avg time per stage
  3. **Active Pipeline:** Open pipeline by close date, weighted pipeline (ARR × stage probability), pipeline waterfall
- **Stage probabilities:** Discovery 5%, Qualification 20%, Objection Handling 40%, Proposal 60%, Negotiation 80%, Closed-Won 100%

---

---

### Bessemer Venture Partners — Cloud/SaaS Benchmarks

#### 8. Scaling to $100 Million + Cloud Laws + Benchmarks
- **URLs:**
  - https://www.bvp.com/atlas/scaling-to-100-million
  - https://www.bvp.com/atlas/10-laws-of-cloud
  - https://www.bvp.com/atlas/the-cloud-100-benchmarks-report
- **Author:** Byron Deeter, Mary D'Onofrio, Elliott Robinson (BVP cloud team)
- **Key framework: Bessemer Efficiency Score** = Net New ARR / Net Burn
- **"Good Better Best" benchmarks:**
  - CAC Payback: 12-18mo good, 6-12mo better, 0-6mo best
  - Net Revenue Retention: 100% good, 110% better, 120%+ best
  - Gross margin: 65-70% average for cloud
- **G.R.I.T. framework:** Growth, Retention, Income (margins), Throughput
- **Why useful:** Most comprehensive, data-rich SaaS benchmarking in the industry. Gives concrete "good/better/best" tiers for every metric.

---

### Andreessen Horowitz (a16z)

#### 9. 16 Startup Metrics + Marketplace Metrics
- **URLs:**
  - https://a16z.com/16-startup-metrics/
  - https://a16z.com/16-more-startup-metrics/
  - https://a16z.com/13-metrics-for-marketplace-companies/
- **Author:** Jeff Jordan, Li Jin, D'Arcy Coolican, Andrew Chen
- **What it covers:** Precise definitions of ARR/MRR, bookings vs revenue, gross vs net churn, CAC (blended vs paid), LTV. Marketplace: GMV, net revenue, take rate, liquidity, buyer/seller concentration.
- **Why useful:** The definitional reference. Eliminates ambiguity around commonly confused terms.

#### 10. Retention Benchmarks for AI
- **URL:** https://a16z.com/ai-retention-benchmarks/
- **What it covers:** AI-specific retention benchmarks. Directly relevant to evaluating Claude-powered startups.

---

### Point Nine Capital (Christoph Janz)

#### 11. Five Animals Framework + SaaS Funding Napkin
- **URLs:**
  - http://christophjanz.blogspot.com/2014/10/five-ways-to-build-100-million-business.html
  - https://www.saas.wtf/p/saas-funding-napkin-2023
- **Author:** Christoph Janz, Co-Founder & MP at Point Nine Capital (leading European early-stage SaaS investor)
- **Five Animals:** Maps 5 paths to $100M revenue by customer segment:
  - Flies ($10/yr × 10M users) → Mice ($100/yr × 1M) → Rabbits ($1K/yr × 100K) → Deer ($10K/yr × 10K) → Elephants ($100K/yr × 1K)
- **SaaS Funding Napkin:** Stage-by-stage benchmarks (Pre-Seed → Series C) for ARR, MRR growth, net retention, valuation. Updated annually.
- **Why useful:** Most intuitive framework for understanding ARPA × customer volume × GTM motion relationship. Funding Napkin = what VCs expect at each stage.

---

### Lenny Rachitsky — Retention Benchmarks

#### 12. What Is Good Retention
- **URL:** https://www.lennysnewsletter.com/p/what-is-good-retention-issue-29
- **Author:** Lenny Rachitsky (ex-Airbnb Product Lead) + Casey Winters (ex-Pinterest/Grubhub Growth Lead)
- **User Retention at 6 months:**
  - Consumer SaaS: ~40% good, ~70% great
  - SMB/Mid-Market SaaS: ~60% good, ~80% great
  - Enterprise SaaS: ~70% good, ~90% great
- **Net Revenue Retention at 12 months:**
  - Bottom-Up SaaS: ~100% good, ~120% great
  - Enterprise SaaS: ~110% good, ~130% great
- **Why useful:** Most specific, practitioner-validated retention benchmarks publicly available, broken down by business model. The benchmark VCs actually reference.

---

### Battery Ventures (Neeraj Agrawal) — T2D3

#### 13. Triple Triple Double Double Double
- **URL:** https://www.battery.com/blog/a-mantra-for-saas-success-triple-triple-double-double-double/
- **Author:** Neeraj Agrawal, GP at Battery Ventures
- **Framework:** After PMF (~$2M ARR), growth trajectory should be:
  - Year 1: 3× ($2M → $6M)
  - Year 2: 3× ($6M → $18M)
  - Year 3: 2× ($18M → $36M)
  - Year 4: 2× ($36M → $72M)
  - Year 5: 2× ($72M → $144M)
- **Proven by:** Marketo, NetSuite, Salesforce, ServiceNow, Workday, Zendesk
- **Why useful:** The standard revenue growth trajectory benchmark. When asking "is this startup growing fast enough to invest time in?" — T2D3 is the reference frame.

---

### Mamoon Hamid / Social Capital — SaaS Quick Ratio

#### 14. Numbers That Actually Matter
- **URL:** https://www.saastr.com/mamoon-hamid-social-capital-numbers-actually-matter-founders-video-transcript/
- **Author:** Mamoon Hamid (Social Capital → Kleiner Perkins, led investments in Slack, Box)
- **Formula:** Quick Ratio = (New MRR + Expansion MRR) / (Churned MRR + Contraction MRR)
- **Benchmark:** >4.0 is investable
- **Why useful:** Elegantly exposes "leaky bucket" companies. A company adding $100K MRR but churning $50K (QR = 2.0) is far worse than one adding $80K and churning $10K (QR = 8.0).

---

### Reforge — Growth Systems

#### 15. Growth Loops + Retention Lifecycle
- **URLs:**
  - https://www.reforge.com/blog/growth-loops
  - https://www.reforge.com/blog/growth-wins
- **Authors:** Brian Balfour (CEO Reforge, ex-VP Growth HubSpot), Casey Winters, Andrew Chen
- **Key concepts:**
  - **Growth Loops vs Funnels:** Funnels are linear and leak; loops are compounding. "How does one cohort of users lead to another?"
  - **Retention Lifecycle:** Three inputs: Activation (new → core value), Engagement (deepen usage), Resurrection (reactivate churned)
- **Why useful:** Operator-level mental models. Unlike VC frameworks that tell you what to measure, Reforge tells you how to improve it.

---

### Sarah Tavel / Benchmark — Hierarchy of Engagement

#### 16. Hierarchy of Engagement
- **URL:** https://www.slideshare.net/greylockpartners/the-hierarchy-of-engagement
- **Author:** Sarah Tavel, GP at Benchmark (ex-Greylock, early PM at Pinterest)
- **Three levels:**
  1. **Growing Engaged Users** — measure core action, not MAU
  2. **Retaining Users (Accruing Benefits)** — product gets better with use, switching costs build
  3. **Self-Perpetuating** — engaged users create loops that grow the product
- **Why useful:** Level 2 (accruing benefits) is the concept most founders miss. It's the mechanism that turns usage into defensibility. Directly relevant to evaluating Claude-powered startups.

---

### OpenView Partners — Product-Led Growth

#### 17. PLG Metrics + Natural Rate of Growth
- **URLs:**
  - https://openviewpartners.com/2023-saas-benchmarks-report/
  - https://openviewpartners.com/2023-product-benchmarks/
- **Author:** Kyle Poyar, Liz Cain (OpenView team, pioneers of PLG category)
- **Key metrics:**
  - **Natural Rate of Growth (NRG):** Organic growth before layering S&M. Critical for PLG.
  - **ARR per FTE:** Emerging north star for operational efficiency
  - **Product-Qualified Leads (PQLs):** 61% more likely to achieve fast growth
- **Why useful:** Claude API adoption IS product-led growth. NRG separates organic product pull from paid push — essential for understanding Anthropic's startup adoption.

---

### ICONIQ Capital — Enterprise Five

#### 18. Growth Resiliency + Enterprise Five + AI Benchmarks
- **URLs:**
  - https://www.iconiqcapital.com/growth/insights/iconiq-growth-resiliency-rubric
  - https://compass.iconiqgrowth.com/
- **Author:** ICONIQ Growth team (portfolio: Datadog, GitLab, Snowflake)
- **Enterprise Five:** ARR Growth, Net Dollar Retention, Rule of 40, Net Magic Number, ARR per FTE
- **AI-native finding:** AI-native companies growing 2-3× faster than top-quartile SaaS, with stronger burn multiples
- **Why useful:** Real benchmark data from 100+ enterprise SaaS companies. Their finding that AI-native companies outperform on burn multiples directly validates the startup partnerships thesis.

---

### Rule of 40 (Brad Feld / Fred Wilson)

#### 19. Rule of 40
- **URL:** https://feld.com/archives/2015/02/rule-40-healthy-saas-company/
- **Formula:** Revenue Growth Rate + Profit Margin ≥ 40%
- **Why useful:** The single most widely cited health metric for SaaS at scale. Forces the growth-profitability tradeoff into one number.

---

### Scale Venture Partners — Four Vital Signs

#### 20. Four Vital Signs of SaaS
- **URL:** https://www.scalevp.com/insights/four-vital-signs-of-saas/
- **The four:** Revenue Growth, Sales Efficiency (Magic Number), Revenue Churn, Cash Burn
- **Why useful:** Most parsimonious SaaS health-check. Reduces complexity to four numbers.

---

### Tomasz Tunguz / Theory Ventures — NDR Deep Dive

#### 21. Simpson's Paradox in NDR + SaaS Strategy
- **URLs:**
  - https://tomtunguz.com/simpsons-paradox-ndr/
  - https://tomtunguz.com/saas-strategy-guide/
- **Author:** Tomasz Tunguz, GP at Theory Ventures (ex-Redpoint, invested in Looker, Expensify)
- **Key insight:** Aggregate NDR can look healthy while individual segments are declining (Simpson's Paradox). Must segment by customer size, industry, acquisition channel.
- **Why useful:** Shows why aggregate metrics are dangerous. Directly applicable: "overall startup portfolio NRR looks fine but EMEA seed-stage startups are churning."

---

### Daniel McCarthy & Peter Fader — Customer-Based Corporate Valuation

#### 22. CBCV
- **URL:** https://hbr.org/2020/01/how-to-value-a-company-by-analyzing-its-customers
- **Authors:** Daniel McCarthy (U of Maryland), Peter Fader (Wharton). Co-founded Theta (sold to Nike).
- **What it is:** Statistical methodology linking customer-level behaviour (acquisition, retention, spend) to corporate valuation through four interlocking submodels.
- **Why useful:** Most academically rigorous framework. Predicted Blue Apron and Wayfair trajectories publicly. Could frame the dashboard as a simplified CBCV lens on startup partners.

---

## How These Apply to the Anthropic Startup Partnerships Role

| Framework | Application to Role |
|-----------|-------------------|
| **Growth Accounting** | Decompose startup portfolio revenue: new partners, expansion (usage growth), churn, contraction. Calculate Quick Ratio for the startup program. |
| **Cohort Analysis** | Track monthly signup cohorts of startup partners. Do Q1 2025 signups retain better than Q3 2024? Do VC-sourced startups retain better than event-sourced? |
| **Revenue LTV** | Empirical LTV curves per startup cohort. Are they super-linear (expanding usage) or sub-linear (fading)? |
| **Distribution of PMF** | CDF of API usage across startup portfolio. Is 80% of revenue from 3 accounts? Or healthy distribution? |
| **Unit Economics / Payback** | Credits granted (= CAC) vs. revenue generated (= LTV). Payback period per startup. Scale invariance = does payback hold as you onboard more startups? |
| **Burn Multiple** | For evaluating startup partners themselves: how efficiently are they growing? High burn multiple = risky partner to invest time in. |
| **Bottom-Up SaaS** | The entire Claude adoption model. Developer tries API → team adopts → company scales. Track this funnel per startup. |
| **Pipeline Metrics** | Partnership pipeline: VC intro → first meeting → credits granted → first API call → meaningful usage → enterprise contract. Win rates and conversion by stage. |
| **Give-to-Get** | Credits program concept — but note: Anthropic does NOT train on customer data. The "get" is revenue, product feedback, market signal, and ecosystem lock-in — not training data. |
| **Quick Ratio** | (New MRR + Expansion MRR) / (Churned MRR + Contraction MRR) for the startup portfolio. >4.0 = healthy program. |
| **T2D3** | Benchmark for evaluating whether a startup partner is on a venture-scale trajectory. Helps prioritise: invest time in T2D3-trajectory startups, not lifestyle businesses. |
| **Retention Benchmarks (Lenny)** | "Is this startup's retention good?" — compare against Lenny's benchmarks for their category. Bottom-up SaaS NRR: 100% good, 120% great. |
| **Bessemer Efficiency Score** | Net New ARR / Net Burn for each startup partner. Healthy partners = efficient growers. |
| **Five Animals (Janz)** | Which animal is each startup? Determines expected usage pattern. An "Elephant" startup ($100K/yr × 1K customers) uses Claude differently than a "Fly" ($10/yr × 10M users). |
| **PLG / NRG (OpenView)** | Claude API adoption IS product-led growth. Natural Rate of Growth measures organic pull vs. paid push. |
| **Hierarchy of Engagement (Tavel)** | Is the startup building accruing benefits on Claude? (Level 2 = switching costs build with usage.) Higher level = stickier partner. |
| **Simpson's Paradox (Tunguz)** | Don't just look at aggregate portfolio NRR. Segment by stage, region, acquisition channel. "EMEA seed-stage startups are churning" could be hidden by healthy growth-stage numbers. |
| **Rule of 40** | Quick health check on startup partners at scale: growth rate + margin ≥ 40% = healthy business worth deepening. |
