# Executive Data Product Dashboard: Build Plan (v2)

> **Archived plan (Oct 5, 2026).** Kept for the reasoning behind decisions; it is not maintained. Where it differs from the code, the code is current: see `README.md`, `docs/metric-definitions.md` and `docs/adr/`.

Oct 5, 2026 · @K · v2 replaces v1 of the same date

## Summary

Build a clean, one-page executive dashboard that shows C-level leaders each week how every domain is progressing on data products. This follows the direction from the joint executive session and the 1-on-1: the executive dashboard takes priority over extending technical validation scripts, because it gives leadership immediate visibility.

The dashboard does not compute a readiness score. It reports the headline metrics leadership agreed (certifications per quarter, G1 to G4 cycle time and adoption) and adds a few leading indicators that warn early when a domain is likely to miss them. Each data product shows one accountable name: its Data Product Owner (DPO).

v2 aligns the plan with the argenx Data Product Governance Framework (gates G1 to G6), replaces the free-form weekly Excel with a product register keyed on each product's NextData identifier, and moves hosting off SharePoint document libraries. It also makes the dashboard the place where the G4 requirement "lifecycle tracking reported" is met, and the domain view replaces the domain status slide in the EDP Success Team Weekly Update rather than adding a third weekly report.

The repo validation tool stays in the picture. Its results are G3 evidence, and it feeds the dashboard from the first release.

The first release runs on local files. The program team drops a structured workbook and source exports into one folder, and one command produces a one-file dashboard and a one-page PDF. The second release adds connectors that write the same files, plus hosting, so nothing in the core changes. The app is built by a small team of AI agents with human checkpoints.

## What changed from v1

| # | v1 said | v2 says | Evidence |
| --- | --- | --- | --- |
| 1 | Four gates, "Gate 1 (Inception) to Gate 4 (Production)"; Gate 2 and 3 undefined | Six gates: G1 Intake, G2 Contract, G3 Build, G4 Certify (GA), G5 Revise, G6 Retire | Data Product Governance Framework (Confluence) |
| 2 | "Certified" undefined | Certified = passed G4 Certify (GA) for the first time | Same, G4 definition of done |
| 3 | Four statuses incl. "Stopped" | Statuses follow the six lifecycle stages; "Retired" via G6; cancellation before GA is an open question | Same, lifecycle stages |
| 4 | Cycle time only for products that reached Gate 4 | First-time G1 to G4 cycle time, plus age of products still in flight; G5 re-traversals measured separately | Framework G5 loop; avoids survivorship bias |
| 5 | One weekly Excel workbook is the only input | Product register keyed on NextData URN; each field from its system of record; people only enter plans, gate dates and comments. Release 1 reads these as local files with a fixed format; Release 2 connectors write the same files | URN reserved at G1, NextData listing required at G4; ODPS-aligned fields in DP Tasks–Ownership deck |
| 6 | Users per product reported by DPOs | Self-reported in release 1 and labelled as such; replaced by Snowflake access history in Phase 2 | Snowflake ACCESS_HISTORY |
| 7 | Domains "such as TechOps and Commercial" | Commercial, G&A, R&D, TechOps & Quality; Commercial grouped by pod | EDP Success Team Weekly Update |
| 8 | Static HTML hosted "on an internal static site or shared location" | Release 1: one-file dashboard opened locally, plus a PDF one-pager posted in Teams. Release 2: hosted behind Entra ID sign-in (e.g. Azure Static Web Apps), linked from SharePoint; never an .html file in a document library | SharePoint downloads .html files and blocks custom script |
| 9 | Browser reads the Excel file | A publish pipeline builds a signed-off JSON snapshot; no spreadsheet parsing in the browser | npm `xlsx` package stuck on a version with a known vulnerability |
| 10 | Seven leading indicators shown alongside headline metrics | Leading indicators appear as reasons on flags, not as extra tiles | Carbon guidance for presentation dashboards |
| 11 | Certifications per quarter as the lead metric | Certifications always shown next to consumption, plus "certified but unused" | DAX objective 01 measure: "Certified products / active consumption" |
| 12 | Planned dates owned by DPOs, editable | Planned dates keep a baseline; every later change is counted as a slip (by comparing weekly snapshots in Release 1, from version history in Release 2) | Prevents silent re-planning |
| 13 | No ownership gap handling | "No DPO assigned" is a flag | Open DPO roles reported in domain working groups |
| 14 | KPIs limited to the leadership set | The leadership set stays on the executive page; other valuable KPIs are listed below and reserved in the metric registry, so any of them can be switched on later | Section "KPIs considered but not selected" |

## What executives see

The dashboard answers four questions in under a minute: are we delivering, how fast, is anyone using what we deliver, and which domain is falling behind. Everything on the page serves one of those questions.

- **Audience and cadence.** C-level and senior executives, reviewing weekly progress across four domains: Commercial, G&A, R&D, and TechOps & Quality.
- **Gates.** The six gates of the Data Product Governance Framework. The delivery clock runs from G1 Intake to G4 Certify (GA).
- **Lifecycle status.** Each product shows one status derived from the last gate it passed (table below).
- **Delivery capacity.** Developers onboarded and EDP Bootcamp qualified, per domain.
- **Ownership.** One name per product: the DPO, who holds ultimate delivery responsibility. Products without a DPO are flagged.
- **Left out on purpose.** Gate checklists, rule-level validation results and technical telemetry. These stay with the DPOs, NextData and the repo validation tool.

| Last gate passed | Lifecycle stage (framework) | Status shown to executives |
| --- | --- | --- |
| None (registered, URN reserved) | Inception | In design |
| G1 Intake | Discovery | In design |
| G2 Contract | Design / Develop | In build |
| G3 Build | Test / Launch | In certification |
| G4 Certify (GA) | Operate / Support | Live |
| G5 Revise, after a first G4 | Discovery or Design / Develop | Live · in revision |
| G6 Retire | Retire | Retired |

| Role | What they do with the dashboard |
| --- | --- |
| Executives | Review domain health weekly and spot lagging areas |
| Data Product Owners | Keep their products' plans, gate dates and comments current in the register; accountable for each product's status and dates |
| Program team (DAX Success) | Runs the weekly publish, checks data quality, chases gaps |
| Program lead | Signs off the weekly snapshot and owns quarterly targets |

## KPIs: headline metrics and leading indicators

Show the five headline metrics leadership agreed, each defined against the framework's gates, and pair them with leading indicators that move weeks earlier. Headline metrics confirm results after the fact; leading indicators are the earlier signals a DPO can still act on.

**Headline metrics (agreed in the executive session)**

| Metric | Definition | Shown as | Source, release 1 → Phase 2 |
| --- | --- | --- | --- |
| Data products certified per quarter | Products passing G4 Certify (GA) for the first time in the quarter | Count against quarterly target, by domain | Register gate dates → NextData listing |
| Cycle time, G1 to G4 | Days from G1 Intake to first G4, for products certified in the last six months | Median days by domain, with n; values listed when n < 3 | Register gate dates |
| Time to first consumer | Days from G1 Intake to the first access by someone outside the product team | Median days by domain | Register (self-reported) → Snowflake access history |
| Active users per product | Distinct people querying a live product in the last 30 days | Median per live product; domain table shows live products with at least one user | Register (self-reported) → Snowflake access history |
| Inter-product consumption | Live products declared as an input by at least one other data product | Count and share of live products | Product specs (declared inputs) → Snowflake access history |

Every certification count sits next to two consumption facts: active users and **certified but unused** (live 60 days or more with no consumer). This keeps the metric aligned with the DAX objective "trusted data products at scale", which is measured as certified products and active consumption.

The page also shows two status views agreed in the session: product counts by status, and developers onboarded versus bootcamp qualified.

**Leading indicators**

These do not get their own tiles. They appear as reasons on domain and product flags, and in full on the domain view.

| Leading indicator | Definition | Early warning on | Source |
| --- | --- | --- | --- |
| G4 forecast for the quarter | Products not yet certified whose planned G4 date falls in the current quarter and is not overdue | Certifications per quarter | Register |
| Overdue against plan | Next gate not passed 14 days after its planned date | Cycle time | Register |
| Plan slips | Times the planned date of the next gate was moved later | Cycle time | Weekly snapshot comparison (Release 1); register version history (Release 2) |
| Age in current stage | Days since the last gate passed, including products still in flight | Cycle time | Register |
| Committed consumers before GA | Products in design, build or certification with at least one named consumer | Time to first consumer, users | Product specs / register |
| Qualified developer capacity | Bootcamp-qualified developers per domain, and share of onboarded developers qualified | Certifications and cycle time | Bootcamp roster |
| First-time validation pass | Share of products passing the repo validation tool with no blocking (P1) findings on first run for the gate | Cycle time | Repo validation tool |

**How lagging domains are flagged.** Flags rest on facts, not a blended score.

- A domain is **Behind** when certifications so far this quarter plus its on-plan G4 forecast are below its quarterly target.
- A product is flagged **Overdue** (next gate 14+ days past plan), **Slipping** (planned GA date moved later two or more times), **No DPO**, **Not updated** (not reviewed by its DPO in 14 days) or **Unused** (live 60+ days with no consumer).
- Colors appear only where an agreed target or a planned date exists; otherwise the number is shown plain. Every flag carries an icon and a text label, never color alone.

For each product, the drill-down shows the same facts at product level: status, last gate passed and date, days in stage, planned next gate and date (with baseline and slips), consumers, users, consuming products, latest validation result, DPO and DPO comment.

## Layout: the executive overview

One page, read top to bottom: five headline numbers, a domain health table that shows where things lag, then the quarterly certification trend and the short list of products that need attention, each with its DPO.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Data Product Delivery · Week 41 · Signed off                      [Vast Blue] │
├──────────────────────────────────────────────────────┬───────────────────────┤
│ [Certified QTD / target] [Median G1→G4] [Median G1→  │ NEEDS ATTENTION       │
│  first consumer] [Active users] [Consumed by other   │ (Clear Blue rail)     │
│  products %]                                         │ Product · reason · DPO│
│                                                      │ Product · reason · DPO│
│ DOMAIN HEALTH                                        │ ...                   │
│ Domain | Live | In pipeline | Certified QTD/target | │                       │
│        | Median cycle | Unused | Flags              │                       │
│ Commercial · G&A · R&D · TechOps & Quality           │                       │
│                                                      │                       │
│ CERTIFIED PER QUARTER (bars) vs TARGET (line)        │                       │
├──────────────────────────────────────────────────────┴───────────────────────┤
│ Sources as of … · Signed off by program lead on … · Definitions              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Clicking a domain row opens the domain view, grouped by pod for Commercial. Clicking a number opens the product list filtered to the products behind it. Nothing else sits on the executive page.

**Visual style.** Use the 2026 argenx brand palette, which the Llama Town intranet already uses:

- Vast Blue `#002834` for the title bar.
- White canvas with a Clear Blue `#D2F1FA` right-hand rail.
- Confidence Blue `#18687F` for table headers, links and buttons.
- Statuses use the brand data-visualisation palette:
  - In design `#74CBE5`
  - In build and In certification `#2397B8`
  - Live `#76CD5F`
  - Retired grey `#9FA5AD`
- Flags use the brand semantic red `#E55E5E` and yellow `#FFE224` as fills with an icon and label, never as text color.
- Arial throughout; Georgia Italic only as a single accent in the page title.

## Data sources and weekly update

**Where the data comes from.** No single file. A product register keyed on the NextData URN holds what no system records today; everything else is read from the system that already owns it.

**Release 1 reads local files.** One inbox folder (OneDrive-synced, owned by the program team) holds a register workbook with four sheets (Products, GateEvents, Targets, Capacity) plus the latest NextData export and validation tool results. Release 2 replaces each manual file with a connector that writes the same file, so the pipeline and the app don't change.

| Data | System of record | Release 1 (local file) | Release 2 and later (connector writes the same file) |
| --- | --- | --- | --- |
| Product ID (URN), name, domain, DPO | NextData catalog | `nextdata_catalog` export; register Products sheet fills gaps (seeded once from the Confluence inventory) | NextData API |
| Gate dates passed (with evidence link), planned next gate and GA dates, comment | Product register (new) | GateEvents and Products sheets, edited by DPOs | SharePoint lists with version history; later G3 and G4 from CI and NextData |
| Declared inputs and consumers | Product repo spec (`spec.py`, `contracts.yml`), ODPS-aligned | NextData export input ports; Products sheet as fallback | Repos and NextData |
| Validation results | Repo validation tool | Its JSON output (or current Excel report) copied into the inbox | Tool writes to the inbox directly |
| Users, first consumer, actual consumption | Snowflake access history | Self-reported in Products sheet, labelled | `usage.csv` from Snowflake |
| GxP validation status for G4 | Veeva | Not in Release 1 | Status only |
| Developers onboarded and qualified | EDP Bootcamp roster | Capacity sheet | SharePoint list |
| Quarterly certification targets | Program lead | Targets sheet | SharePoint list |

**Weekly cycle.** Corrections are made in the register, not in the dashboard, so the register stays the single record. Each signed-off week is stored as an immutable snapshot, which is what produces the trend lines, and the dashboard footer shows who approved the current week.

| Step | When | Who | What happens |
| --- | --- | --- | --- |
| 1. Update | Mon–Wed | DPOs | Record gates passed (with evidence link), update planned dates and comments in the register workbook |
| 2. Draft | Thu | Program team (Release 2: scheduled) | Adds the latest NextData export and validation results to the inbox; runs `dp build` for a draft dashboard and data-quality report |
| 3. Sign off | Fri | Program lead | Reviews the draft; corrections go into the workbook and the draft is rebuilt; `dp approve` |
| 4. Publish | Fri | Program team (Release 2: automatic) | Posts the one-page PDF and a three-line "what changed" note in the executive Teams channel (Release 2: link to the hosted app) |

The domain section of the dashboard replaces the domain RAG slide in the EDP Success Team Weekly Update, so DPOs and the Success team report once.

## Build approach

Build a small custom web app now, because leadership preferred it to Power BI for visual and functional flexibility, and confirm that choice on purpose at the first checkpoint rather than by default.

- **Three views only.** Executive overview (one page), domain view (the same metrics for one domain, grouped by pod where relevant, with its products), and a product list with product detail for drill-down.
- **Architecture.** Two contracts: a fixed inbox file format going in, and one JSON snapshot per week coming out. A Python command-line tool (`dp`) reads the inbox, checks data quality, computes metrics from a metric registry, and embeds the snapshot in a one-file dashboard. There's no server and no spreadsheet parsing in the browser.
- **Technology.** React and TypeScript with free, open-source chart components (Tremor or Recharts), built once into an HTML template. Python for the pipeline; the weekly run needs Python only.
- **Hosting.** Release 1 needs none: the program team opens the file locally and posts the PDF. Release 2 hosts the same file behind Entra ID sign-in, restricted to a security group (Azure Static Web Apps proposed, to confirm with IT), linked from SharePoint and Llama Town. It is never hosted as an .html file in a SharePoint library, because SharePoint downloads those instead of showing them and blocks custom script.
- **Builders.** Four AI agents, each owning distinct files (contracts and integration, data pipeline, app, verification), with human checkpoints on definitions, look, real-data runs and dry runs.
- **Design rules.** Clean and uncluttered, domain health first, no gate checklists, one color meaning per status, every number clickable to the products behind it, and WCAG 2.1 AA contrast.

**Design references worth browsing**

- [Carbon dashboard guidance](https://carbondesignsystem.com/data-visualization/dashboards/): IBM's rules for executive "presentation" dashboards (few metrics, hierarchy, consistent color). The executive page follows these; drill-down lives on the domain and product views.
- [Tremor](https://www.tremor.so/): open-source React components for KPI cards, charts and status trackers, free under MIT license since Vercel's [January 2025 acquisition](https://vercel.com/blog/vercel-acquires-tremor).
- [shadcn/ui blocks](https://ui.shadcn.com/blocks): free copy-paste dashboard layouts with sidebar, charts and data table.
- [SaaSFrame](https://www.saasframe.io/categories/dashboard) and [Mobbin](https://mobbin.com/explore/web/screens/admin-dashboard): libraries of real dashboard screens.

## Roadmap

Move in three phases and automate only once the weekly view is in regular use. Release 1 has dry runs on Oct 29–30 and Nov 5–6 and is planned to post its first signed-off executive pack on Fri Nov 13, 2026, ahead of the DAX 60-day milestone (end of November) for gates operating with evidence.

| Phase | Scope | Exit checkpoint |
| --- | --- | --- |
| 1. Release 1: local files (about 5 weeks) | Inbox workbook and exports, `dp` tool, three views in a one-file dashboard, PDF one-pager, weekly sign-off | **Checkpoint 1:** executives use it in four consecutive weekly reviews, and the Success weekly deck stops duplicating it. Confirm custom app vs Power BI before hosting. |
| 2. Release 2: connected and hosted (target Dec 11, subject to access approvals) | Connectors for SharePoint lists, NextData API, validation tool and Snowflake usage; scheduled runs; Entra-protected hosting; automatic Teams post | **Checkpoint 2:** self-reported usage fields retired |
| 3. Automated gates | G3 from CI and validation results, G4 from NextData listing, GxP status from Veeva; register shrinks to plans and comments | — |

Each new feed writes the same inbox files that people fill by hand in Release 1, so the dashboard itself does not change.

## KPIs considered but not selected

Leadership chose five headline metrics for the executive page. The KPIs below are also worth tracking. Each is reserved in the metric registry, so it can be switched on (on the domain view or the executive page) by adding one function and its test.

"Available" means:
- **Now:** computable from Release 1 files.
- **R2:** needs a Release 2 connector.
- **Later:** needs a new source.

**Delivery flow**

| KPI | Definition | Question it answers | Available |
| --- | --- | --- | --- |
| Stage duration by gate | Median days G1→G2, G2→G3, G3→G4, by domain | Where does work stall? | Now |
| Gate throughput | Products passing each gate per month | Is the pipeline filling or drying up? | Now |
| Work in progress vs capacity | Products in design, build or certification per qualified developer | Is a domain overloaded? | Now |
| Funnel conversion | Share of products past G1 that reach G4 within two quarters; cancellations | How much started work turns into products? | Now |

**Predictability**

| KPI | Definition | Question it answers | Available |
| --- | --- | --- | --- |
| Plan reliability | Share of gates passed on or before the baseline date | Can we trust the dates DPOs give? | Now |
| Forecast accuracy | Certifications achieved vs G4 forecast at the start of the quarter | Are quarterly commitments realistic? | Now (after one quarter of snapshots) |

**Quality and reliability in production**

| KPI | Definition | Question it answers | Available |
| --- | --- | --- | --- |
| Revision rate | G5 events per live product per quarter, split by scope change and bug fix | Are products stable after GA? | Now |
| SLO attainment | Share of live products meeting freshness, completeness and availability SLOs | Can consumers rely on live products? | Later (observability) |
| Production data-quality pass rate | Share of DQ rule runs passing in production | Is quality holding after launch? | R2 (NextData / Soda) |
| Incidents and time to restore | Incidents per live product and median time to restore | How disruptive are failures? | Later (incident tool) |

**Adoption and value**

| KPI | Definition | Question it answers | Available |
| --- | --- | --- | --- |
| Consumer retention | Share of users active in each of the last three months | Do people keep using what they tried? | R2 (Snowflake) |
| Consumer breadth | Distinct domains consuming each product | Is the product reused beyond its home domain? | R2 |
| Agent consumption | Share of queries from AI agents and MCP clients | Is the AI-ready investment used? | R2 |
| Use cases served | Use cases or decisions linked to each live product | What business need does each product serve? | Later (use case register) |
| Value realised | Value cases delivered and benefits realised (DAX objective 04) | Is the programme paying back? | Later |
| Consumer satisfaction | Short quarterly survey score per product | Are consumers happy with quality and support? | Later (survey) |

**Reuse and architecture**

| KPI | Definition | Question it answers | Available |
| --- | --- | --- | --- |
| Reuse ratio | Share of new products built on existing data products rather than raw sources | Is the mesh compounding? | Now (declared inputs) |
| Semantic coverage | Share of products with a semantic model linked to the domain glossary (G2) | Will products be understood consistently? | R2 (NextData) |
| Lineage coverage | Share of products emitting lineage | Can we trace issues and impact? | R2 (validation tool) |

**Compliance and AI readiness**

| KPI | Definition | Question it answers | Available |
| --- | --- | --- | --- |
| Evidence completeness | Share of gates passed with an evidence link; open blocking findings and their age (DAX objective 05) | Are we audit-ready? | Now |
| Classification completeness | Share of products with confidentiality/integrity/availability rating, AI-Act tier and GxP impact declared | Are controls applied to the right products? | R2 (NextData) |
| AI-ready share | Share of live products with Information Card, Agent/Model Card and passing eval pack | Can agents use our products safely? | R2 |

**Cost, capacity and ownership**

| KPI | Definition | Question it answers | Available |
| --- | --- | --- | --- |
| Cost to serve | Monthly platform cost per live product and per active user (G4 requires cost tracking) | Is each product worth what it costs? | Later (cost attribution) |
| Bootcamp throughput | Developers qualified per month; days from onboarding to qualification | Is delivery capacity growing? | Now |
| DPO load | Live and in-flight products per DPO; open DPO roles | Is accountability spread thinly? | Now |
| Reporting hygiene | Share of products reviewed by their DPO this week | Can we trust this week's numbers? | Now |

**Five to propose to leadership next.** These are cheap to add and answer questions executives will ask once the headline view is familiar:

1. **Stage duration by gate.** It turns "cycle time is long" into "G2 is the bottleneck".
2. **Plan reliability.** It shows whether forecasts can be trusted.
3. **Reuse ratio.** It is the clearest sign the data mesh is working.
4. **Evidence completeness.** It links delivery to audit readiness.
5. **Consumer retention.** It arrives with Snowflake usage in Release 2 and separates real adoption from trial use.

**Deliberately not recommended:**
- counts of tables, columns or datasets;
- raw query volume;
- number of DQ rules defined;
- lines of code;
- self-assessed red/amber/green.

These measure activity rather than outcomes and are easy to inflate.

## Open questions and next steps

Answered since v1: what "certified" means (first G4 Certify), what the gates are (G1 to G6), and which domains are in scope (Commercial, G&A, R&D, TechOps & Quality).

**Open questions**

- How is a product cancelled before GA recorded? The framework's G6 covers retirement after Operate / Support only.
- Is "time to first consumer" measured from G1 (total time to value) or from G4 (adoption after launch)? v2 keeps G1 as agreed.
- Who counts as a consumer: does access by the product's own team or by a BI or agent service account count?
- Can the pipeline read NextData through an API with a service identity, or only by export?
- Is the argenx Snowflake account on Enterprise Edition (needed for access history), and will the platform team expose a narrow view of it?
- Is Azure Static Web Apps with Entra ID sign-in approved hosting, and which security group gets access?
- Who sets the quarterly certification target for each domain, and are quarters calendar quarters?
- Does the dashboard formally replace the domain slide in the EDP Success Team Weekly Update?

**Next steps**

- [ ] Confirm the metric definitions and status mapping with leadership and the EDP Governance Lead (checkpoint H1, by Oct 13)
- [ ] Set up the inbox folder and register workbook template; seed it from the NextData export and the Confluence inventory
- [ ] Test the workbook with two DPOs
- [ ] Build Release 1 with the agent team; first real local run by Oct 23
- [ ] Run two dry-run weeks in parallel with the Success weekly deck, then switch over on Nov 13
- [ ] Agree quarterly certification targets per domain
- [ ] Raise Release 2 access requests now: Graph permissions, NextData service identity, Snowflake view, hosting and Entra groups
- [ ] Choose which of the five proposed extra KPIs to take to leadership

The engineering plan for the first release is in *Data Product Dashboard v1 Engineering Plan.md*.

## Sources

**Internal**

- [Data Product Governance Framework (Confluence, DT Data & AI)](https://argenx.atlassian.net/wiki/spaces/DDA/pages/882409506/Data+Product+Governance+Framework)
- [Commercial Data Product Inventory (Confluence)](https://argenx.atlassian.net/wiki/spaces/DDA/pages/1270808748/Commercial+Data+Product+Inventory)
- [DP - Tasks - Ownership.pptx](https://argenxbvba.sharepoint.com/sites/P-DataGovernance-EXTTEAM/Shared%20Documents/Data%20Catalog/02.%20Delivery/2026%20(2)%20-%20April%20to%20June/2.1%20Data%20Framework/DP%20-%20Tasks%20-%20Ownership.pptx)
- [Gov & Success Weekly Update & Syncs.pptx (DAX objectives, roadmap)](https://argenxbvba.sharepoint.com/sites/P-DataGovernance-EXTTEAM/Shared%20Documents/Data%20Catalog/01.%20Project%20management/2026%20(3)%20-%20July%20to%20December/03.%20Weekly%20Update%20&%20Syncs/Gov%20&%20Success%20Weekly%20Update%20&%20Syncs.pptx)
- [EDP-Success-Weekly-Status-18-September-2026.pptx](https://argenxbvba.sharepoint.com/sites/P-DataGovernance-EXTTEAM/Shared%20Documents/Data%20Catalog/02.%20Delivery/2026%20(2)%20-%20April%20to%20June/2.1%20Data%20Framework/EDP%20Weekly/EDP-Success-Weekly-Status-18-September-2026.pptx)
- [Nextdata DP Validation Report - Sep 10 2026.xlsx](https://argenxbvba.sharepoint.com/sites/P-USCommercialMAF-DataandAnalyticsTEAM/Shared%20Documents/5.%20Data%20Governance/Working%20Folder/Nextdata%20DP%20Validation%20Report%20-%20Sep%2010%202026.xlsx)

**External**

- [Snowflake: ACCESS_HISTORY view](https://docs.snowflake.com/en/sql-reference/account-usage/access_history)
- [Open Data Product Standard v1.0 (Bitol)](https://bitol-io.github.io/open-data-product-standard/v1.0.0/)
- [Nextdata OS](https://www.nextdata.com/product)
- [Host an HTML file on SharePoint: why it won't render](https://yapp.page/host-html-on-sharepoint)
- [Snyk: Prototype Pollution in xlsx](https://security.snyk.io/vuln/SNYK-JS-XLSX-5457926)
- [Carbon Design System: dashboards](https://carbondesignsystem.com/data-visualization/dashboards/)
- [Promethium: Measuring data product success](https://promethium.ai/guides/measuring-data-product-success-kpis-metrics-that-matter/)
- [Tremor](https://www.tremor.so/) · [Vercel acquires Tremor](https://vercel.com/blog/vercel-acquires-tremor) · [shadcn/ui blocks](https://ui.shadcn.com/blocks)
