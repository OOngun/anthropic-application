const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak, LevelFormat, ExternalHyperlink } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function heading(text, level) {
    return new Paragraph({ heading: level, children: [new TextRun({ text, bold: true })] });
}

function para(text, opts = {}) {
    return new Paragraph({
        spacing: { after: 120 },
        ...opts,
        children: [new TextRun({ text, size: 22, font: "Arial", ...opts.run })]
    });
}

function boldPara(label, text) {
    return new Paragraph({
        spacing: { after: 100 },
        children: [
            new TextRun({ text: label, bold: true, size: 22, font: "Arial" }),
            new TextRun({ text, size: 22, font: "Arial" })
        ]
    });
}

function bullet(text) {
    return new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        spacing: { after: 60 },
        children: [new TextRun({ text, size: 22, font: "Arial" })]
    });
}

function benchmarkTable(rows) {
    return new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2800, 2200, 4360],
        rows: [
            new TableRow({
                children: ["Metric", "Expected Range", "Source"].map(h =>
                    new TableCell({
                        borders,
                        width: { size: h === "Source" ? 4360 : h === "Metric" ? 2800 : 2200, type: WidthType.DXA },
                        shading: { fill: "2B3544", type: ShadingType.CLEAR },
                        margins: { top: 60, bottom: 60, left: 100, right: 100 },
                        children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 20, font: "Arial", color: "FFFFFF" })] })]
                    })
                )
            }),
            ...rows.map(r =>
                new TableRow({
                    children: r.map((cell, i) =>
                        new TableCell({
                            borders,
                            width: { size: i === 2 ? 4360 : i === 0 ? 2800 : 2200, type: WidthType.DXA },
                            margins: { top: 50, bottom: 50, left: 100, right: 100 },
                            children: [new Paragraph({ children: [new TextRun({ text: cell, size: 20, font: "Arial" })] })]
                        })
                    )
                })
            )
        ]
    });
}

function sectionBreak() {
    return new Paragraph({ spacing: { before: 200, after: 200 }, children: [] });
}

const doc = new Document({
    styles: {
        default: { document: { run: { font: "Arial", size: 22 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 36, bold: true, font: "Arial", color: "1A1A2E" },
              paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 28, bold: true, font: "Arial", color: "2B3544" },
              paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
            { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 24, bold: true, font: "Arial", color: "475569" },
              paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
        ]
    },
    numbering: {
        config: [
            { reference: "bullets",
              levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
                style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        ]
    },
    sections: [{
        properties: {
            page: {
                size: { width: 11906, height: 16838 },
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
            }
        },
        headers: {
            default: new Header({
                children: [new Paragraph({
                    alignment: AlignmentType.RIGHT,
                    children: [new TextRun({ text: "Anthropic EMEA Startup Partnerships \u2014 Analytical Framework", size: 16, font: "Arial", color: "94A3B8", italics: true })]
                })]
            })
        },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({ text: "Page ", size: 16, font: "Arial", color: "94A3B8" }),
                        new TextRun({ children: [PageNumber.CURRENT], size: 16, font: "Arial", color: "94A3B8" })
                    ]
                })]
            })
        },
        children: [
            // ============ TITLE ============
            new Paragraph({
                alignment: AlignmentType.LEFT,
                spacing: { after: 80 },
                children: [new TextRun({ text: "Measuring What Matters", size: 48, bold: true, font: "Arial", color: "1A1A2E" })]
            }),
            new Paragraph({
                spacing: { after: 200 },
                children: [new TextRun({ text: "A Growth Accounting Framework for Anthropic\u2019s Startup Partnerships", size: 28, font: "Arial", color: "475569" })]
            }),
            new Paragraph({
                spacing: { after: 100 },
                border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "3B82F6", space: 1 } },
                children: [new TextRun({ text: "Ongun Ozdemir \u00B7 March 2026", size: 20, font: "Arial", color: "64748B" })]
            }),

            sectionBreak(),

            // ============ FOREWORD ============
            heading("Foreword", HeadingLevel.HEADING_1),

            para("All data in this dashboard is synthetic and for demonstrative purposes."),

            para("In this model, I\u2019ve taken an approach which focuses on direct API usage, while ignoring enterprise agreements, Pro/Max subscriptions, and other consumption channels. By scoping to direct API partners only, the model stays clean with synthetic data and reflects the primary revenue channel that a startup partnerships role would manage."),

            para("We have applied early and growth-stage growth accounting analyses utilised by top-tier VC firms to evaluate product-market fit within a partnership portfolio. These frameworks take different approaches and place different importance on metrics depending on the partner\u2019s use case and stage, as we highlight in the accompanying case studies."),

            para("The core analytical framework is adapted from Tribe Capital\u2019s \u201CA Quantitative Approach to Product-Market Fit\u201D and the accompanying SQL implementation by Jonathan Hsu at Social Capital. The framework decomposes growth into its constituent components \u2014 retained, new, expansion, resurrected, contraction, and churned \u2014 to reveal the quality of growth, not just its rate."),

            para("The dashboard operates on three tiers:"),

            boldPara("Pulse", " \u2014 the ecosystem health check. Four headline metrics, a growth accounting waterfall with selectable time periods and scopes, a combined GA + CMGR chart, and a portfolio revenue share visualisation. This answers \u201Cis the portfolio healthy this week?\u201D in under ten seconds."),

            boldPara("Partners", " \u2014 the navigation layer. Every partner in a sortable, colour-coded scoreboard with a Power Law Tracker ranking partners by projected scale. This answers \u201Cwho needs my attention?\u201D and routes you to the detail view."),

            boldPara("Company Detail", " \u2014 the full drill-down. Growth accounting, cohort LTV curves and heatmaps, developer retention, model mix evolution. This answers \u201Cwhy is this partner behaving the way it is, and what should I do about it?\u201D"),

            sectionBreak(),

            // ============ ANALYTICAL APPROACH ============
            heading("Analytical Approach", HeadingLevel.HEADING_1),

            para("The growth accounting identity is not a model \u2014 it\u2019s an accounting framework. Every period, the active revenue base decomposes into mutually exclusive categories that must balance:"),

            para("Revenue(t) = Retained + New + Expansion + Resurrected", { run: { font: "Courier New", size: 20 }, alignment: AlignmentType.CENTER }),
            para("Revenue(t-1) = Retained + Churned + Contraction", { run: { font: "Courier New", size: 20 }, alignment: AlignmentType.CENTER }),

            para("From these components we derive three key metrics:"),

            sectionBreak(),

            // QUICK RATIO formula block
            new Paragraph({
                spacing: { before: 80, after: 40 },
                children: [new TextRun({ text: "Quick Ratio", bold: true, size: 22, font: "Arial" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 60, after: 20 },
                border: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.SINGLE, size: 3, color: "3B82F6", space: 8 } },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "New  +  Resurrected  +  Expansion", font: "Cambria Math", size: 22, color: "1E293B" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 0, after: 0 },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500", font: "Cambria Math", size: 18, color: "94A3B8" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 0, after: 40 },
                border: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.SINGLE, size: 3, color: "3B82F6", space: 8 } },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "Churned  +  Contraction", font: "Cambria Math", size: 22, color: "1E293B" })]
            }),
            new Paragraph({
                spacing: { after: 160 },
                indent: { left: 360 },
                children: [new TextRun({ text: "Measures growth efficiency. How many units gained for every unit lost. >4x = very healthy, <1x = shrinking.", size: 20, font: "Arial", color: "64748B", italics: true })]
            }),

            // GROSS RETENTION formula block
            new Paragraph({
                spacing: { before: 80, after: 40 },
                children: [new TextRun({ text: "Gross Dollar Retention (GDR)", bold: true, size: 22, font: "Arial" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 60, after: 20 },
                border: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.SINGLE, size: 3, color: "16A34A", space: 8 } },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "Retained Revenue", font: "Cambria Math", size: 22, color: "1E293B" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 0, after: 0 },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500", font: "Cambria Math", size: 18, color: "94A3B8" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 0, after: 40 },
                border: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.SINGLE, size: 3, color: "16A34A", space: 8 } },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "Prior Period Revenue", font: "Cambria Math", size: 22, color: "1E293B" })]
            }),
            new Paragraph({
                spacing: { after: 160 },
                indent: { left: 360 },
                children: [new TextRun({ text: "The floor \u2014 how much revenue survives month-to-month without any new business. Caps at 100%. B2B SaaS median: 91%.", size: 20, font: "Arial", color: "64748B", italics: true })]
            }),

            // NET DOLLAR RETENTION formula block
            new Paragraph({
                spacing: { before: 80, after: 40 },
                children: [new TextRun({ text: "Net Dollar Retention (NDR)", bold: true, size: 22, font: "Arial" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 60, after: 20 },
                border: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.SINGLE, size: 3, color: "D97706", space: 8 } },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "Retained  +  Expansion  +  Resurrected", font: "Cambria Math", size: 22, color: "1E293B" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 0, after: 0 },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500", font: "Cambria Math", size: 18, color: "94A3B8" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 0, after: 40 },
                border: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.SINGLE, size: 3, color: "D97706", space: 8 } },
                indent: { left: 1440, right: 1440 },
                children: [new TextRun({ text: "Prior Period Revenue", font: "Cambria Math", size: 22, color: "1E293B" })]
            }),
            new Paragraph({
                spacing: { after: 160 },
                indent: { left: 360 },
                children: [new TextRun({ text: "Whether the existing base is growing or shrinking. >100% = expansion exceeds losses (the goal). Enterprise B2B SaaS median: 110\u2013118%.", size: 20, font: "Arial", color: "64748B", italics: true })]
            }),

            para("Critically, the same Quick Ratio can mean very different things depending on the partner\u2019s use case. A consumer product with QR 2.0x (high churn offset by high new) is healthy. A B2B enterprise product with QR 2.0x (moderate churn, moderate new) may be concerning. The case studies below demonstrate this principle."),

            sectionBreak(),

            // ============ PULSE SECTION DETAIL ============
            heading("Pulse Section: Key Visualisations", HeadingLevel.HEADING_1),

            heading("Compound Monthly Growth Rate (CMGR)", HeadingLevel.HEADING_2),

            para("CMGR measures the smoothed monthly growth rate over trailing windows \u2014 3, 6, and 12 months. We show all three simultaneously because the relationship between them tells a story that no single number can."),

            para("When CMGR-3 leads CMGR-12 (short-term growth exceeds long-term average), the portfolio is accelerating. When CMGR-3 trails CMGR-12, growth has decelerated \u2014 recent months are underperforming the historical trend. This spread is surfaced as an explicit callout in the Pulse section because it\u2019s the earliest signal of a structural slowdown versus a seasonal dip."),

            para("For a startup partnerships portfolio, CMGR is more useful than annualised CAGR because the time horizons are short (12\u201324 months of partner history) and the growth rates are volatile. A partner showing 1,500% CAGR from a $100 base is mathematically correct but operationally meaningless. CMGR-3 of 8% tells you they\u2019re compounding steadily right now, which is actionable."),

            heading("Portfolio Revenue Share", HeadingLevel.HEADING_2),

            para("The stacked area chart shows each partner\u2019s proportional share of total portfolio revenue over time. Partners below a significance threshold are grouped into \u201COthers\u201D to keep the visual clean \u2014 we care about who\u2019s winning, not the long tail of minimal contributors."),

            para("This view naturally surfaces the power law. In our synthetic portfolio, MedScribe AI, NovaMed AI, BrieflyAI, and Eigen Technologies emerge as the clear top performers, collectively accounting for the majority of portfolio revenue. The remaining partners contribute individually small amounts."),

            para("The practical implication: these top performers are the candidates to watch most closely and allocate more resources to. Depending on internal policies and thresholds, they would be the first candidates to transition from the partnerships team to dedicated account management \u2014 or to hand over to account executives for deeper commercial relationships. They represent the portfolio\u2019s future revenue base, and their retention is disproportionately important to the programme\u2019s overall ROI."),

            para("The \u201COthers\u201D band is equally informative. If it\u2019s growing as a proportion, the portfolio is diversifying \u2014 more partners are contributing meaningfully. If it\u2019s shrinking, concentration risk is increasing and the portfolio\u2019s health depends on fewer bets."),

            heading("Revenue Distribution", HeadingLevel.HEADING_2),

            para("The revenue distribution chart shows the shape of revenue across the entire partner portfolio. Two views are provided:"),

            bullet("Power Law / Pareto: a horizontal bar chart of each partner\u2019s monthly revenue (sorted high to low) with a cumulative percentage line. This immediately reveals whether the portfolio follows a power law distribution \u2014 in a typical startup portfolio, the top 3\u20135 partners will generate 50\u201370% of total revenue."),

            bullet("Histogram: groups partners into revenue buckets ($0, $0\u2013500, $500\u20132K, $2K\u201310K, $10K+) showing how many partners fall into each tier. A healthy portfolio has a few partners in the high buckets and a long tail of smaller ones \u2014 not a uniform distribution."),

            para("This visualisation directly informs resource allocation. If your top 3 partners account for 65% of portfolio revenue, those relationships need disproportionate attention. If the distribution is flatter, the portfolio is more resilient but may lack breakout performers."),

            new Paragraph({ children: [new PageBreak()] }),

            // ============ CASE STUDY 1: WRITEFLOW ============
            heading("Case Study 1: WriteFlow \u2014 Consumer AI Writing Assistant", HeadingLevel.HEADING_1),

            boldPara("Stage: ", "Series A \u00B7 HQ: London \u00B7 Team: 18 people \u00B7 Vertical: Consumer SaaS"),

            sectionBreak(),

            heading("Company Profile", HeadingLevel.HEADING_2),

            para("WriteFlow is a browser-based writing assistant that helps users draft emails, blog posts, and social media copy. Users type a prompt, Claude generates a draft, users edit and iterate. The product has a freemium tier (5 generations/day) and a Pro plan (\u00A312/mo, unlimited)."),

            para("Every time a user clicks \u201CGenerate\u201D or \u201CRewrite,\u201D that\u2019s an API call. Primarily Haiku for quick drafts, Sonnet for longer-form content. Their 40K monthly active users generate roughly 2M API calls per month."),

            heading("Expected Growth Accounting Profile", HeadingLevel.HEADING_2),

            para("Usage is directly tied to consumer behaviour. Students sign up during essay season and disappear. Marketers churn when budgets get cut. New users flood in after a viral TikTok post, then half leave within a month. The GA chart should be volatile \u2014 high new, high churn, with growth driven by acquisition, not retention."),

            heading("Benchmarks", HeadingLevel.HEADING_3),

            benchmarkTable([
                ["Gross Retention", "23\u201370%", "ChartMogul: AI products <$50/mo show 23% GRR"],
                ["Net Dollar Retention", "32\u201385%", "ChartMogul: median AI-native NDR is 48%"],
                ["Quick Ratio", "1.5\u20132.5x", "Tribe Capital: consumer discretionary below 2.0x typical"],
                ["Monthly Churn", "4\u20138%", "Arcade.dev: B2C AI services average 4.04%"],
                ["LTV Curve Shape", "Sub-linear", "Tribe Capital: customers pay less in later months"],
            ]),

            sectionBreak(),

            heading("What to Watch", HeadingLevel.HEADING_2),

            bullet("Churn rate vs new acquisition rate. If churn exceeds new for 2+ consecutive months, the product is losing PMF."),
            bullet("M3-to-M12 retention: a16z\u2019s framework argues that measuring from Month 3 (not Month 0) removes \u201CAI tourists\u201D and gives a truer picture of product-market fit."),
            bullet("Free-to-paid conversion above 3% is a positive signal (Arcade.dev: only 3% convert globally for ChatGPT)."),
            bullet("Model mix shift toward Sonnet signals premium feature adoption and higher revenue per user."),
            bullet("DAU/MAU above 30% indicates genuine daily engagement (ChatGPT is at 36% per Arcade.dev)."),

            heading("Red Flags", HeadingLevel.HEADING_3),
            bullet("GRR below 30% \u2014 most users churning within first 3 months"),
            bullet("Quick Ratio below 1.5 \u2014 revenue declining or barely growing"),
            bullet("Growth entirely dependent on new acquisition with no retained base"),
            bullet("NDR below 40% at any price point"),

            new Paragraph({ children: [new PageBreak()] }),

            // ============ CASE STUDY 2: FINLEDGER ============
            heading("Case Study 2: FinLedger \u2014 Internal Developer Tooling", HeadingLevel.HEADING_1),

            boldPara("Stage: ", "Seed \u00B7 HQ: Berlin \u00B7 Team: 6 people (4 engineers) \u00B7 Vertical: Fintech"),

            sectionBreak(),

            heading("Company Profile", HeadingLevel.HEADING_2),

            para("FinLedger builds accounting automation for European SMEs. Their product has nothing to do with AI \u2014 it\u2019s a bookkeeping tool. But their engineering team uses Claude\u2019s API daily: reviewing pull requests, generating unit tests, writing documentation, and debugging. They have 4 API keys (one per engineer)."),

            para("Engineers paste code into internal tools that call Claude\u2019s API. Sonnet for code review (needs reasoning quality), Haiku for test boilerplate. Usage is steady Monday\u2013Friday, drops on weekends. Approximately 50K API calls per month."),

            heading("Why Traditional GA Doesn\u2019t Fully Apply", HeadingLevel.HEADING_2),

            para("With 3\u201310 users, standard growth accounting metrics produce statistically meaningless noise. There\u2019s no distribution of customers sufficient for cohort analysis. Retention is binary \u2014 either the team uses it or they switch tools entirely."),

            para("The value story for FinLedger is better told through the revenue trend line (flat and sticky) and the step-function expansions when they adopt a new Claude use case (CI pipeline at month 9, documentation generation at month 16)."),

            heading("What to Measure Instead", HeadingLevel.HEADING_3),

            benchmarkTable([
                ["API calls/dev/week", "Increasing trend", "Usage intensity = engagement proxy"],
                ["% of team active", "80\u2013100%", "GitHub Copilot: 96% same-day retention"],
                ["Week-over-week trend", "Flat or growing", "Equivalent to QR for small teams"],
                ["Usage concentration", "Distributed", "Single-dev dependency = bus factor risk"],
                ["Monthly spend growth", "5\u201315% MoM", "Twilio historical NDR: 136\u2013140%"],
            ]),

            sectionBreak(),

            heading("What to Watch", HeadingLevel.HEADING_2),

            bullet("Step-function jumps in usage = new use case adopted. This is the primary expansion signal."),
            bullet("Active developer ratio dropping below 50% = half the team stopped using it."),
            bullet("Usage concentrated in a single developer = bus factor risk, not genuine team adoption."),
            bullet("Team experimenting with alternative tools (GitHub Copilot, Cursor) = competitive pressure."),
            bullet("Cost per useful output rising = more API calls needed for same result, efficiency declining."),

            heading("Green Flags", HeadingLevel.HEADING_3),
            bullet("All team members making API calls weekly (100% activation)"),
            bullet("New use cases emerging organically (started with code review, now docs + tests)"),
            bullet("Tool integrated into CI/CD pipelines (systematic, not ad-hoc)"),
            bullet("Team requesting budget increases for higher API tier"),

            new Paragraph({ children: [new PageBreak()] }),

            // ============ CASE STUDY 3: BRIEFLYAI ============
            heading("Case Study 3: BrieflyAI \u2014 B2B Meeting Summarisation", HeadingLevel.HEADING_1),

            boldPara("Stage: ", "Series A \u00B7 HQ: Amsterdam \u00B7 Team: 22 people \u00B7 Vertical: Enterprise Productivity"),

            sectionBreak(),

            heading("Company Profile", HeadingLevel.HEADING_2),

            para("BrieflyAI records and transcribes business meetings, then uses Claude to generate structured summaries with action items, decisions, and follow-ups. Sold to companies on a per-seat basis (\u00A315/seat/month). Their clients are mid-market firms with 20\u2013200 employees. 45 enterprise clients running approximately 3,000 meetings per week."),

            para("After every meeting ends, the transcript is sent to Claude (Sonnet for quality). A 30-minute meeting generates roughly 8K tokens of transcript producing 2K tokens of structured output."),

            heading("Expected Growth Accounting Profile", HeadingLevel.HEADING_2),

            para("Each enterprise client represents a block of predictable, recurring API usage. When BrieflyAI wins a new client, it shows as a step-function increase in revenue. When a client cancels (rare \u2014 the summaries become part of their workflow), it\u2019s a visible cliff. The GA chart shows high retained revenue, occasional large expansion events, very low churn, and super-linear LTV curves."),

            para("This is Tribe Capital\u2019s canonical example of a healthy B2B SaaS profile: growth rate of ~10% composed of 9% new + 4% expansion - 4% contraction - 0% churn, with negative net churn meaning the existing base grows without any new logos."),

            heading("Benchmarks", HeadingLevel.HEADING_3),

            benchmarkTable([
                ["Gross Retention", "90\u201395%", "SaaS Capital: median B2B SaaS GRR 91%"],
                ["Net Dollar Retention", "105\u2013120%", "SaaS Capital: enterprise ACV >$100k median 110\u2013118%"],
                ["Quick Ratio", "4.0\u20138.0x", "Mamoon Hamid/Social Capital benchmark for B2B"],
                ["Annual Logo Churn", "5\u201310%", "SaaS Capital: enterprise contracts are sticky"],
                ["LTV Curve Shape", "Super-linear", "Tribe Capital: cohort revenue increases with age"],
            ]),

            sectionBreak(),

            heading("What to Watch", HeadingLevel.HEADING_2),

            bullet("Client acquisition cadence \u2014 are step-functions getting bigger or smaller over time?"),
            bullet("Seat expansion within accounts \u2014 are existing clients deploying to more teams without active sales effort?"),
            bullet("Model mix trending toward Opus = handling more complex, longer meetings. Revenue expansion without volume change."),
            bullet("Any churn cliff = lost enterprise client. Investigate immediately \u2014 rare events carry outsized signal."),
            bullet("NDR above 110% confirms the land-and-expand motion is working."),

            heading("Red Flags", HeadingLevel.HEADING_3),
            bullet("GRR falling below 85% \u2014 below SaaS Capital median, signals product issues"),
            bullet("NDR below 100% \u2014 existing base shrinking, enterprise products should be expanding"),
            bullet("Revenue concentration: top 5% of clients generating >50% of revenue creates dangerous dependency"),
            bullet("Quick Ratio below 2.0 (Tribe Capital flags this as concerning for B2B)"),

            new Paragraph({ children: [new PageBreak()] }),

            // ============ CROSS-COMPARISON ============
            heading("Cross-Use-Case Comparison", HeadingLevel.HEADING_1),

            para("The table below summarises how the same metrics carry different interpretations across the three use cases:"),

            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2000, 2342, 2342, 2342],
                rows: [
                    new TableRow({
                        children: ["Metric", "Consumer (WriteFlow)", "Dev Tooling (FinLedger)", "B2B Enterprise (BrieflyAI)"].map((h, i) =>
                            new TableCell({
                                borders,
                                width: { size: i === 0 ? 2000 : 2342, type: WidthType.DXA },
                                shading: { fill: "2B3544", type: ShadingType.CLEAR },
                                margins: { top: 50, bottom: 50, left: 80, right: 80 },
                                children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 18, font: "Arial", color: "FFFFFF" })] })]
                            })
                        )
                    }),
                    ...([
                        ["Gross Retention", "23\u201370%", "~100% (binary)", "90\u201395%"],
                        ["NDR", "32\u201385%", "N/A (usage proxy)", "105\u2013120%"],
                        ["Quick Ratio", "1.5\u20132.5x", "N/A", "4.0x+ target"],
                        ["LTV Curve", "Sub-linear", "Linear to mild super-linear", "Super-linear"],
                        ["Growth Driver", "New user acquisition", "Deepening usage/dev", "Seat expansion"],
                        ["Primary Risk", "Churn > acquisition", "Binary tool-switch", "Account concentration"],
                    ]).map(r =>
                        new TableRow({
                            children: r.map((cell, i) =>
                                new TableCell({
                                    borders,
                                    width: { size: i === 0 ? 2000 : 2342, type: WidthType.DXA },
                                    margins: { top: 40, bottom: 40, left: 80, right: 80 },
                                    children: [new Paragraph({ children: [new TextRun({ text: cell, size: 18, font: "Arial" })] })]
                                })
                            )
                        })
                    )
                ]
            }),

            sectionBreak(),

            // ============ SOURCES ============
            heading("Sources", HeadingLevel.HEADING_1),

            bullet("Tribe Capital \u2014 \u201CA Quantitative Approach to Product-Market Fit\u201D (tribecap.co)"),
            bullet("Jonathan Hsu / Social Capital \u2014 Growth Accounting & LTV SQL (GitHub Gist)"),
            bullet("a16z \u2014 \u201CRetention Is All You Need\u201D and Growth Metrics Guide (a16z.com)"),
            bullet("ChartMogul \u2014 \u201CThe SaaS Retention Report: The AI Churn Wave\u201D (2025)"),
            bullet("Arcade.dev \u2014 \u201CAI Platform Retention & Monetization Analysis\u201D (2025)"),
            bullet("SaaS Capital \u2014 \u201C2023 B2B SaaS Retention Benchmarks\u201D"),
            bullet("Tomasz Tunguz \u2014 \u201CWhat is Quick Ratio Hiding?\u201D"),
            bullet("OpenView Partners \u2014 2023 SaaS Benchmarks Report"),
            bullet("Twilio public filings / SaaStr analysis"),

            sectionBreak(),

            para("This document accompanies the interactive dashboard. All data is synthetic. The analytical framework and benchmarks are real.", { run: { italics: true, color: "64748B" } }),
        ]
    }]
});

const outPath = "/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project/CASE-STUDIES-ANALYSIS.docx";
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync(outPath, buffer);
    console.log("DOCX saved to: " + outPath);
    console.log("Size: " + (buffer.length / 1024).toFixed(0) + " KB");
});
