# Case Studies: Three Partner Profiles

## 1. WriteFlow — AI Writing Assistant (Customer-Facing)

**Stage:** Series A · **HQ:** London · **Team:** 18 people · **Vertical:** Consumer SaaS

WriteFlow is a browser-based writing assistant that helps users draft emails, blog posts, and social media copy. Users type a prompt, Claude generates a draft, users edit and iterate. The product has a freemium tier (5 generations/day) and a Pro plan ($12/mo, unlimited).

**How they use Claude:** Every time a user clicks "Generate" or "Rewrite," that's an API call. Primarily Haiku for quick drafts, Sonnet for longer-form content. Their 40K monthly active users generate roughly 2M API calls/month.

**Why this profile matters:** Usage is directly tied to consumer behaviour. Students sign up during essay season and disappear. Marketers churn when budgets get cut. New users flood in after a viral TikTok post, then half leave within a month. The GA chart is volatile — high new, high churn, moderate expansion from free-to-paid conversions.

---

## 2. FinLedger — Fintech Startup Using Claude Internally (Developer Tooling)

**Stage:** Seed · **HQ:** Berlin · **Team:** 6 people (4 engineers) · **Vertical:** Fintech

FinLedger builds accounting automation for European SMEs. Their product has nothing to do with AI — it's a bookkeeping tool. But their engineering team uses Claude's API daily: reviewing pull requests, generating unit tests, writing documentation, and debugging. They have 4 API keys (one per engineer).

**How they use Claude:** Engineers paste code into internal tools that call Claude's API. Sonnet for code review (needs reasoning quality), Haiku for test boilerplate. Usage is steady Monday-Friday, drops on weekends. ~50K API calls/month.

**Why this profile matters:** The "users" are the startup's own engineers. Nobody churns unless someone quits. Nobody new joins unless they hire. Expansion only happens when they find a new use case (e.g. adding Claude to their CI pipeline). The GA chart is flat and stable — very high retention, almost no new or churned, slow expansion. Low absolute revenue but extremely sticky.

---

## 3. BrieflyAI — Meeting Summarisation Platform (B2B Embedded)

**Stage:** Series A · **HQ:** Amsterdam · **Team:** 22 people · **Vertical:** Enterprise Productivity

BrieflyAI records and transcribes business meetings, then uses Claude to generate structured summaries with action items, decisions, and follow-ups. Sold to companies on a per-seat basis ($15/seat/month). Their clients are mid-market firms with 20-200 employees.

**How they use Claude:** After every meeting ends, the transcript is sent to Claude (Sonnet for quality). A 30-minute meeting generates roughly 8K tokens of transcript → 2K tokens of structured output. Their 45 enterprise clients run about 3,000 meetings/week through the platform.

**Why this profile matters:** Each enterprise client represents a block of predictable, recurring API usage. When BrieflyAI wins a new client, it shows as a step-function increase in revenue. When a client cancels (rare — the summaries become part of their workflow), it's a visible cliff. The GA chart shows high retained revenue, occasional large expansion events (new client wins), very low churn (sticky B2B contracts), and super-linear LTV curves as existing clients add more seats over time.
