# Board

Product-owner decisions, open items, contract changes and the status log. Newest entries go at the bottom of each table and at the top of the status log.

## Decisions (product owner)

| Date | Decision |
| --- | --- |
| 2026-10-05 | Build the vertical slice (I0+I1) first; PO reviews look and numbers at H2 before I2 starts. |
| 2026-10-05 | Stack: React + motion + TanStack Table + custom SVG charts; template budget 600 KB (ADR-001). |
| 2026-10-05 | Look: restrained executive. react-bits CountUp, SpotlightCard, AnimatedList, Stepper, GooeyNav, GlareHover. No backgrounds. |
| 2026-10-05 | Git: one commit per completed task. |
| 2026-10-05 | Slice computes all five headline metrics plus the supporting metrics and flags the executive page needs, so H2 shows real numbers in every tile. |
| 2026-10-06 | H2 feedback: dark background, no draft watermark, no all-caps, few fonts per view, domain cluster map with a red/orange/yellow/green signal per product, GlareHover on view navigation. |
| 2026-10-06 | Brand: argenx PowerPoint template 3.0 and Portals guidelines; fonts Instrument Sans + Inria Serif italic (downloaded, SIL OFL). |
| 2026-10-06 | Redesign direction: the category-standard executive dashboard at the craft of Linear, Vercel and Apple Health's summary (impeccable roll declined for canon). ADR-002. |
| 2026-10-07 | Inventory plan approved: platform files (NextData, validation tool) feed product identity and readiness; business domain stays with the register; EDP team layer becomes the pod; never-reviewed rows show "Not yet reported" instead of "Not updated". Governance tooling and glossaries are not counted by default (crosswalk can override). |
| 2026-10-07 | Domain table with expandable rows on the executive Table view (collapsed) and the products page (expanded). Template budget raised from 600 KB to 640 KB instead of trimming code (ADR-001). |
| 2026-10-07 | PO feedback round: title-case "Data Product Delivery"; no sign-off chip in the header; domain rows with disclosure triangles (executive Table view and Products page); "Data product owner" column; calm neutral flags, emphasised numbers; fuzzy order-independent product search; map labels hugging their clusters; products table with pinned header, frozen columns, drag-to-pan and a draggable scrollbar. TanStack Table removed. |
| 2026-10-07 | One domain table: the cloud session's `DomainGroupTable` (PR #1) and the local feedback build overlapped. Kept the local build (DPO column, calm flags, search, scrolling table, no TanStack) and carried over PR #1's signal counts per domain, "n of N shown", print behaviour, and its axe and signal-count checks. Budget stays at PR #1's 640 KB. |
| 2026-10-07 | Domains corrected (everything is commercial): Patient, HCP, Market access, Channel partner, Revenue / vials, Medical affairs, Logistics, plus Unknown; the word Commercial is not shown. Mapping by product name in `registry/product-domains.yaml` (committed, real names allowed in the private repo), then name rules, then team. EDP team sub-groups dropped; the team is shown on the product page. |
| 2026-10-07 | Second demo with real product and domain names and made-up values (`demo/index-named.html`). Front page: Technical readiness (renamed from Readiness) above Speed and adoption; Reporting coverage moved to the end; both stay conditional. Removed from the code: in-flight age, spec complete, owner coverage, the 12 reserved stubs, and the domain view's leading-indicators table. NextData link on each product page. |
| 2026-10-07 | Clean version (branch `clean-version`): dead code removed; pods removed everywhere (no data had one), including the register's `pod` column; the `dp export` placeholder removed until the PDF export is built; `registry/fields.yaml` removed (nothing read it); design-tool working files removed; plans moved to `docs/archive/`; this board trimmed to decisions, open items and the log; one-command setup (`scripts/setup.sh`). |

## Open items

| Item | Owner | Note |
| --- | --- | --- |
| Metric definitions sign-off (checkpoint H1) | PO, program lead, EDP Governance Lead | `docs/metric-definitions.md` is still a draft. |
| PDF one-pager export | – | Not built. Until then, print the executive overview from the browser (it fits one A4 landscape page). |
| Freshness warning for inbox files | – | The definitions promised a warning for files older than 7 days (`SOURCE_STALE`); it was never built and was taken out of the definitions on 2026-10-07. Validation results already have `VAL_STALE`. |
| Link colour | PO | Link Blue shares its hex with Data Blue (#74CBE5); see DESIGN.md. |
| Past-quarter bars link to their products | A3 | Contract change request below (`TrendPoint.urns[]`). |
| Release 2: connectors and hosting | – | See the archived plans in `docs/archive/`. |

## Contract change requests

| Date | Requested by | Change | Decision |
| --- | --- | --- | --- |
| 2026-10-05 | A1 | Snapshot adds `quarter`, `domains[]`, `registry{metrics,flags}`, `MetricValue.urns[]`, `MetricValue.reason`, `ProductRow.iteration`, `ProductRow.lastGate`, `DataQualityItem.file/row`. Definitions page and "every number links to its products" need them. | Accepted (A1), schema 1.0 |
| 2026-10-05 | A3 | `TrendPoint.urns[]` so past-quarter bars can link to their products (today only the current quarter links, through `certified_qtd`). | Open |
| 2026-10-07 | A1 | Snapshot adds optional `reporting[]` (data coverage), `ProductRow.nextdata`, `ProductRow.platformDomain`, `MetricDefinition.coverage`, `ComponentScore`; `ValidationSummary` gains `score`, `components`, `ownerStatus`, `keyids` and its `p1Findings`/`firstRunPass` become optional; signal adds `unreported`. All additive for readers. | Accepted (PO approved the inventory plan), schema 1.0 |
| 2026-10-07 | A1 | `NextDataSummary` gains `url` and `team`, `NextDataDeployment` gains `url`. Additive. | Accepted (PO asked for the NextData link) |
| 2026-10-07 | PO | Clean version: remove `DomainInfo.pods`, `ProductRow.pod`, `ValidationSummary.firstRunPass` and the source status `stale`. None was ever filled or shown; the app is the only reader and changes with it. | Accepted, schema 1.0 |

## Status log

- 2026-10-07 · Clean version: 159 acceptance, 32 end-to-end, 36 component tests green; template 570 KB of 640 KB. Both demos rebuilt; their numbers are unchanged. The `ND_NOT_IN_REGISTER` warning now names the EDP team (it read the always-empty pod and said "no team"), and the data-quality report's Team column shows the team for the same reason. A real register that still has a `pod` column gets one `UNKNOWN_COLUMN` warning until the column is deleted.
- 2026-10-07 · Real domains round: 160 acceptance, 32 end-to-end, 36 component tests green; no page overflow from 390 to 1920 px; template 572 KB of 640 KB. Three packs built: made-up demo, named demo, real inbox (44 products: HCP 13, Market access 11, Patient 9, Unknown 8, Channel partner 2, Revenue / vials 1). New domain registry and name rules (AT-PLAT-09b, 09c), named demo generator (AT-DEMO-01..03), Technical readiness strip (AT-E2E-22), NextData link and EDP team on the product page (AT-E2E-19).
- 2026-10-07 · Platform sources merged: NextData and validation readers, product identity rules, crosswalk and register seeding (AT-PLAT-01..15); `ND_*` and `VAL_*` checks, readiness, data coverage and "Not yet reported" (AT-PLAT-20..27); app coverage strip, readiness row, platform facts and column (AT-E2E-17..21).
- 2026-10-07 · PO tweaks: Products domain rows total only, no custom scrollbar, hover names on signal marks. 97 acceptance, 22 end-to-end, 26 component tests green; template 548 KB of 640 KB.
- 2026-10-07 · Merged PR #1 (cloud session) with the local feedback round into one domain table (header title case, disclosure triangles, DPO column, calm flags, fuzzy search, map labels, scrolling table): 97 acceptance, 22 end-to-end, 26 component tests green; no page overflow from 390 to 1920 px; template 551 KB of 640 KB.
- 2026-10-06 · H2 redesign built and reviewed (health signal per product, dark argenx theme, overview with rings and cluster map, GlareHover tabs, all views redesigned, DESIGN.md): 97 acceptance, 16 end-to-end, 15 component tests green; template 597 KB of 600 KB; no overflow from 390 to 1920 px.
- 2026-10-05 · I1 vertical slice complete on synthetic data (readers, lifecycle, metrics, flags, data-quality checks, `dp check/build/approve`, app template): 95 acceptance tests, 11 component tests, 13 end-to-end checks green. Template 487 KB, opens from `file://` in well under 2 s. `dp approve` and slip counting came forward from I2/I3 because the snapshot needed `baselineDate`/`slips`.
- 2026-10-05 · I0 contracts written (inbox contract and register template, snapshot schema and TypeScript types, registries, fixtures and golden snapshot); toolchains installed (Python 3.13 venv, Node 22).
