# Product

## Platform

web

## Users

- **Primary: argenx C-level and senior executives**, reviewing data product delivery once a week. The dashboard is most often projected or screen-shared in the weekly executive meeting, several leaders reading at once while one person drives the clicks. (Confirmed 2026-10-06.)
- **Program lead** signs off the weekly snapshot and owns quarterly certification targets.
- **Program team (DAX Success)** runs the weekly build, checks data quality and chases gaps.
- **Data Product Owners (DPOs)** keep their products' plans, gate dates and comments current; each product shows one accountable DPO.

## Product Purpose

A weekly executive view of how every business domain (Patient, HCP, Market access, Channel partner, Revenue / vials, Medical affairs, Logistics; all commercial) is progressing on data products, built on the argenx Data Product Governance Framework gates G1 Intake to G6 Retire. It answers, in under a minute: are we delivering, how fast, is anyone using what we deliver, and which domain is falling behind.

Success in the first ten seconds of the meeting: leaders see **which domain is falling behind** and **whether the quarter is on track** against its certification target. (Confirmed 2026-10-06.) Everything else is one click or one hover away.

## Positioning

The view is built from facts recorded in the product register and source systems, never from self-assessed red/amber/green. Every number links to the products behind it, every flag carries its reason, and every week is signed off by the program lead before it is shown. It replaces the domain slide in the EDP Success Team Weekly Update rather than adding another report.

## Operating Context

- Weekly cycle: DPOs update the register Mon to Wed; the program team runs `dp check` and `dp build` on Thursday; the program lead reviews and runs `dp approve` on Friday; the signed-off `index.html`, with its "what changed" lines, goes to the executive Teams channel. A one-page PDF export is planned but not built.
- Release 1 is a single HTML file opened locally (no server); Release 2 hosts the same file behind Entra ID sign-in.
- Drill-down questions in the meeting are answered from the same file: domain view, product list, product detail.

## Capabilities and Constraints

- One-file dashboard (React + TypeScript, Vite single-file build), snapshot JSON embedded by the Python `dp` pipeline. Opens from `file://`, hash routing, under 2 seconds; template budget 640 KB (ADR-001).
- Views: executive overview, domain view, product list, product detail, definitions.
- Headline metrics (leadership-agreed): certified this quarter vs target, median G1→G4 cycle time, median time to first consumer, median active users per live product, share of live products consumed by other products. Medians show n; self-reported values are labelled; nulls show "—" with a reason.
- Flags: Behind (domain), Overdue, Slipping, No DPO, Not updated, Unused, Pending URN. Each product carries a health signal derived from its flags: red (off track), orange (at risk), yellow (attention), green (on track), grey (retired or cancelled).
- Print stylesheet fits the executive overview on one A4 landscape page.
- Made-up values only in the repository; real inbox files are opened only by people.
- Out of scope: gate checklists, rule-level validation detail, editing data in the app.

## Brand Commitments

- **argenx brand (2026 refresh).** Palette from the Portals brand guidelines and the argenx PowerPoint template 3.0: Vast Blue `#002834`, Confidence Blue `#18687F`, Clear Blue `#D2F1FA`, White, Ever Green `#034940`, Growing Green `#028980`, Spring Green `#DBFFF0`, Amplified Green `#76CB5F`, Easy Green `#D0FFC4`, Eureka Teal `#45EFBC`, Activated Orange `#FF7B24`, Calming Coral `#FFEBDD`. Data-visualisation palettes (charts and colour-coded visuals only): tonal `#2397B8 #74CBE5 #DDF2F9 #76CD5F #ADE0A0 #E5F5E0 #FF7B24 #FFB17D #FFE6D6`; semantic `#76CB5F` positive, `#FFE224` median, `#E55E5E` negative; de-emphasis greys `#848D9B #9FA5AD #BBBFC3`. Primary colours are not for data; data-visualisation colours are not for non-data content.
- **Type.** Brand web fonts: Instrument Sans, with Inria Serif italic as the single accent face (Office equivalent: Arial with Georgia italic). Product-owner rules: no all-caps text; few fonts per view.
- **Logo.** argenx wordmark files `argenx_r_rev_wht_rgb_260527.png` (reversed white, for dark grounds), `argenx_r_pos_clr_rgb_260527.png`, `argenx_r_pos_blk_rgb_260527.png`. Never recoloured or restyled.
- **Voice.** "The immunology innovation company": courage and urgency for patients waiting for a breakthrough; Entrepreneurial Science; co-creation. Plain, factual, never hype.
- **Standing preference (2026-10-06):** the category-standard executive dashboard composition, executed at the craft level of Linear, the Vercel dashboard and Apple Health's summary screen; no novelty worlds.
- **Product-owner decisions (2026-10-06):** dark background; no draft watermark (the footer states draft or signed off, decision of 2026-10-07); domain section as a cluster map (domains as clusters, products as circles with a health-signal ring, hover lifts and previews key metrics); navigation between Executive, Products and Definitions uses the react-bits GlareHover effect; UI components drawn from react-bits where they serve the task.

## Evidence on Hand

- Rules: `docs/metric-definitions.md`. The original plans are archived in `docs/archive/` (the code is current where they differ).
- Synthetic golden week `tests/fixtures/golden/2026-W41.json` (25 products, 8 domains). Real register values never enter the repository. Real product and domain names appear only in the named demo, `registry/product-domains.yaml` and `tests/fixtures/inbox-named-demo/` (the repository is private). Never invent customers, patient numbers or outcomes.
- Brand sources: Portals brand guidelines (palette, fonts, logo, icon set, "Strings" and "Infinity Loop" line graphics, photography); argenx PowerPoint template 3.0. The icon set, line graphics and photography are not in the project; do not imitate them.

## Product Principles

1. **Hard news first.** Behind domains and overdue products are never softened or pushed below the fold.
2. **Picture first, numbers on request.** The first screen tells the story visually; figures sit one hover or one click away, and every figure links to the products behind it.
3. **Facts, not opinions.** Every colour and flag traces to a registry rule and a dated record; no blended scores.
4. **Readable across a meeting room.** The first screen works projected for a group; detail rewards a closer look.
5. **Serious and calm.** argenx serves patients with serious diseases: motion and colour explain, never entertain.

## Accessibility & Inclusion

WCAG 2.1 AA, verified with axe-core on every view. Colour is never the only signal: flags carry an icon and label, health signals carry a ring shape as well as a colour. Motion respects `prefers-reduced-motion`. Every chart has a table equivalent.
