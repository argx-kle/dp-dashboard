# Metric definitions (checkpoint H1)

Oct 5, 2026 · Draft for approval by the product owner, program lead and EDP Governance Lead.

Everything below is what the pipeline computes. The acceptance tests in `tests/acceptance/` are written from this document, not from the code. Changing a definition here is a contract change.

## Conventions

| Term | Definition |
| --- | --- |
| Week | ISO week, e.g. `2026-W41`. |
| As-of date | The Friday of the reported ISO week, unless `dp build --as-of` overrides it. Gate events after the as-of date are a blocker. |
| Quarter | Calendar quarter containing the as-of date (Q4 = Oct 1 to Dec 31). |
| Trailing 182 days | The half-open window `(asOf − 182 days, asOf]`. |
| Active product | A product that is neither Retired nor Cancelled. |
| Live product | Status Live or Live · in revision. |
| Median | Standard median. With n below `min_n` (3) the raw values are listed instead of hiding the number. |
| Self-reported | A value typed by a DPO into the register. Always labelled as such until the Snowflake connector replaces it. |
| Area | The level above the domain (`area` in `registry/domains.yaml`): Commercial (Patient, HCP, Market access, Channel partner, Revenue / vials, Medical affairs, Logistics), TechOps, R&D, G&A, and Unassigned for Unknown. Added 2026-10-08. The executive views hide an area or a domain with no products. |

## Status mapping

Gate events are ordered by date. Iteration 1 starts at G1; each G5 starts a new iteration. The status comes from the most recent event.

| Most recent event | Stage | Status |
| --- | --- | --- |
| None (URN reserved) | Inception | In design |
| G1 Intake | Discovery | In design |
| G2 Contract | Design/Develop | In build |
| G3 Build | Test/Launch | In certification |
| G4 Certify (GA) | Operate/Support | Live |
| G5 Revise, after a first G4 | Discovery (scope change) or Design/Develop (bug fix) | Live · in revision |
| G6 Retire | Retire | Retired |
| `cancelled_on` set | unchanged | Cancelled |

`firstG4Date` is the earliest G4 event. `daysInStage` is days from the most recent event to the as-of date, or from `reviewed_on` (else 0) when there is no event.

A G2, G3 or G4 after a G5 continues the new iteration. The status after a G5 followed by G2 is still Live · in revision until the next G4.

## Lifecycle stages (added 2026-10-08)

The executive views name six business stages instead of gate codes (`ProductRow.lifecycle`). Gates stay the governance record: the product page lists them, as the stage each one opens, in its stage history.

| Stage | Starts when | Status |
| --- | --- | --- |
| Ideation | Registered, no gate passed | In design (no event) |
| In design | G1 Intake passed, or a G5 scope change before any G4 | In design |
| In development | G2 Contract passed | In build |
| In testing | G3 Build passed | In certification |
| Live | G4 Certify passed; stays Live during a G5 revision | Live, Live · in revision |
| Failed / retired | G6 Retire passed, or `cancelled_on` set | Retired, Cancelled |

Each stage fills one more quarter of the circle, clockwise from 12 o'clock, on one green ramp that gets brighter as the product advances (product-owner choice, round 5): Ideation grey-green dotted ring, In design 1/4, In development 2/4, In testing 3/4, Live 4/4 in the brightest green, Failed / retired red double ring. A yellow dot marks a product with a flag ("Needs attention" in the legend). The hover card shows the stage and the next gate with its date ("G4 Certify · 20 Oct").

### Gates

Drafted from the gate names of the Data Product Governance Framework; to be confirmed by the EDP Governance Lead.

| Gate | What passing it means | Opens |
| --- | --- | --- |
| G1 Intake | The portfolio accepts the idea. The business owner and the use case are named. The URN is reserved. The delivery clock starts. | In design |
| G2 Contract | The team and the consumers agree the data contract: schema, meaning, quality rules, service levels and access. | In development |
| G3 Build | The team builds the product on the platform to its contract. Pipelines, tests and documentation are complete. | In testing |
| G4 Certify (GA) | The product passes certification. It is published and available to all users. The first G4 counts as certified. | Live |
| G5 Revise | A live product opens again for a scope change or a fix. A new iteration starts. The product stays Live. | New iteration |
| G6 Retire | The team removes the product from service. A product cancelled before go-live counts as failed. | Failed / retired |

Reasons name the gate: "G4 Certify was due 20 Oct, 31 days overdue".

## Headline metrics (executive tiles)

| Id | Rule | Edge cases |
| --- | --- | --- |
| `certified_qtd` | Count of products whose `firstG4Date` falls in the current quarter. Shown against the Targets sheet for the quarter. | Re-certifications after G5 are not counted; the first G4 decides the quarter. |
| `cycle_time_g1_g4` | Median of `firstG4Date − G1 date`, over products whose `firstG4Date` is in the trailing 182 days. | Product without G1 excluded with a warning (and it is a blocker if it has G2 to G4). |
| `time_to_first_consumer` | Median of `firstConsumerDate − G1 date`, over products whose `firstConsumerDate` is in the trailing 182 days. | Source label (self-reported or snowflake) carried through. |
| `active_users_median` | Median of `activeUsers30d` over Live products that have a figure. | Live product without a figure is excluded and gets a warning. |

The executive strip shows, in this order: median time to production (`cycle_time_g1_g4`), median time to first consumer, median users per live product, and certified this quarter against its target. `inter_product_share` (live products used by other products) was removed on 2026-10-08 (product owner): too complex to show and track accurately for now. `input_products` stays in the register and on the product page.

## Supporting metrics

| Id | Rule |
| --- | --- |
| `live_count` | Live products. |
| `pipeline_count` | Products In design, In build or In certification. |
| `certified_unused` | Live products with `firstG4Date` 60 or more days before the as-of date, `activeUsers30d` equal to 0 and no consuming product. A missing usage figure is a warning, not an unused product. |
| `g4_forecast` | Active products without G4 whose `planned_ga_date` is in the current quarter and on or after the as-of date, and whose next gate is not OVERDUE. |

These feed the domain table, the map's rings and the BEHIND flag; they are not shown as separate indicator tiles. Removed 2026-10-07 (product owner): `in_flight_age`, `spec_complete`, `owner_coverage` and the reserved stubs for later releases. Counts already shown elsewhere are not repeated as indicators.

## Flags

| Flag | Level | Rule | Signal |
| --- | --- | --- | --- |
| BEHIND | Domain | Health at risk or off track (below target once the quarter is closed). No target, no flag. | Red |
| OVERDUE | Product (active) | `asOf > planned_next_gate_date + 14 days` and the planned gate is not yet passed. | Red |
| SLIPPING | Product (active) | `planned_ga_date` moved later two or more times since its baseline (weekly snapshot comparison). | Orange |
| UNUSED | Product (active) | Same rule as `certified_unused`. | Orange |
| NO_DPO | Product (active) | G1 passed and no DPO. | Yellow |
| NOT_UPDATED | Product (active) | `reviewed_on` older than 14 days. A product never reviewed is shown as "Not yet reported" instead (changed 2026-10-07: during onboarding every row would otherwise be flagged). | Yellow |
| PENDING_URN | Product | URN starts with `pending:`. | Yellow |

## Domain health (added 2026-10-08, pace rule from 2026-10-08 round 2)

Health is a forecast per domain, and for the organisation, per quarter (`snapshot.health`), never a colour per product. It compares delivery with what was expected **by today**, not with the final target (product-owner decision):

- `elapsed` = days from the quarter start to the as-of date, inclusive, divided by the days in the quarter
- `expected` = target × `elapsed`, rounded to the nearest whole product (halves up), so the numbers on screen are the ones judged
- `pace` = `certified_qtd` ÷ `expected`

| Health | Current quarter |
| --- | --- |
| Ahead | pace ≥ 110% |
| On track | 90% to 109% |
| Behind (status key `at-risk`) | 70% to 89% |
| Off track | below 70% |
| No target | no row in the Targets sheet for the quarter |

While `expected` is 0 (less than half a product due: early in a quarter, or a small target) a domain with nothing certified is On track and one with something certified is Ahead; a target of 0 works the same way. A closed quarter has nothing left to be at risk of: it reads Above target (`certified > target`), Met target (=) or Below target (<). BEHIND on `certified_qtd` means at risk or off track (below target once closed). `forecast` (on plan by the quarter end) and `late` (go-live due by the quarter end, not on plan) stay in the snapshot as context for the summary; they no longer decide the health.

The executive summary gives one fact per line ("Behind. 11 data products live." / "13 expected by today." / "Quarter target: 23 by 31 December.") with a key that names every part of the ring (live, on plan, not planned, late, the expected-by-today tick), and a status board: one column per health, each domain a `certified/target` pill in its column. Health marks are icons in colour: trend up, green (ahead, above target); check, green (on track, met target); warning triangle, orange (at risk); stop sign, red (off track); trend down, red (below target). Each pill fills by certified ÷ target, and shows the numbers as **certified**/target. Health is not shown in "Products by domain": that section shows the products at one date.

## Quarter selector (added 2026-10-08)

The executive overview opens on the current quarter; the selector offers the four trend quarters (`#/?q=2026-Q3`). Each closed quarter is rebuilt as it stood on its last day (`snapshot.quarters`): gate events up to that day, products that had passed a gate by then, cancellations up to then, the quarter's targets. Stages, certified, time to production, time to first consumer and health are therefore exact. Plans, flags and usage are only known for the current week, so a closed quarter forecasts nothing, raises no flag and shows usage (`active_users_median`, `certified_unused`) as null with the reason; the attention list is replaced by the products that went live in the quarter.

## Product signal (ranking only since 2026-10-08)

Each product still carries one signal (ADR-002). Since 2026-10-08 it is not drawn: it orders the "Needs attention" list. The rules:

| Signal | Rule | Ring |
| --- | --- | --- |
| Grey, "Retired or cancelled" | Status Retired or Cancelled | Dotted |
| Red, "Off track" | Most severe flag signal is red | Double |
| Orange, "At risk" | Most severe flag signal is orange | Broken (one quarter missing) |
| Yellow, "Attention" | Most severe flag signal is yellow | Dashed |
| Hollow, "Not yet reported" | Active, no flags, and its DPO has never reviewed the row (`reviewed_on` empty) | Thin, no fill |
| Green, "On track" | Active, no flags, reviewed | Solid |

Which flag raises which signal is set in `registry/flags.yaml`. The "Needs attention" list orders flagged products by signal, then by days overdue.

## Technical readiness (added 2026-10-07)

From the platform sources. They move weekly, long before a certification. The "Technical readiness" strip is shown only when NextData, validation or GitHub files are in the inbox (above Speed and adoption, on the executive overview and each domain page), with the tiles of the sources present; a metric whose source is missing is null with the reason.

| Id | Rule |
| --- | --- |
| `spec_score_median` | Median finish-spec score (validation tool) over active products that have one. Static completeness of the specification, not a launch pass. |
| `runtime_failing` | Active products deployed in NextData whose deployments are all Failed or Unreachable; n is the number of active products deployed. |
| `no_prod_deploy` | Active products whose GitHub repository has never deployed to production successfully, up to the as-of date; n is the number of active products with a repository. Added 2026-10-30. |
| `prod_deploy_frequency` | Median number of successful production deployments in the trailing 30 days `(asOf − 30 days, asOf]`, over active products whose repository has deployed to production at least once (GitHub decides, not the register's Live stage); a product with none in the window counts as 0. Added 2026-10-30, pool changed 2026-11-02. |
| `deploy_failure_rate` | Deployments in the trailing 30 days, every environment, whose outcome is failure or error, divided by all deployments with an outcome in that window, over the repositories of active products; n is the number of deployments, the products listed had at least one failure. Pending deployments are not counted. Added 2026-10-30. |

GitHub rules: production is an environment listed in `github.prod_environments` in `registry/platform.yaml` (`iac-apply-p`; GitHub's own production flag is not set on these repositories). A deployment's outcome is its latest `success`, `failure` or `error` status; `inactive` (a success replaced by a newer deployment), `queued` and `in_progress` are ignored, and a deployment without any of the three is pending. Deployments dated after the as-of date are ignored.

## Delivery (added 2026-11-02)

The `#/delivery` view and the Delivery panel on the executive overview come from the GitHub extract alone, so they show real numbers while the register is still being filled. The panel sits at the top of the overview while no product has a gate, and next to Technical readiness once products do. It is shown for the current week only.

- **Counted repositories:** every `*-dp-*` repository except tooling teams, template, test and placeholder names (the `exclude_*` rules in `registry/platform.yaml`) and crosswalk rows marked not counted. Excluded repositories are listed behind a toggle and left out of every total. Counted repositories that match no register product are tagged "Not in register".
- **Promotion path:** `github.environments` in `registry/platform.yaml`, in order (Dev `iac-apply-d`, Validation `iac-apply-v`, Production `iac-apply-p`). A repository "reached" a step when at least one deployment there ended in success. Other environments count in the totals only.
- **Window:** `(asOf − 30 days, asOf]`. Deployments are counted when they have an outcome; the failure rate is failure or error over those.
- **Weekly:** the last 12 ISO weeks up to the as-of date, by the day each deployment started. "Succeeded or running" is every deployment that did not fail; production successes are marked above the bar.
- **Last production deploy:** the latest successful production deployment of any counted repository. The tile counts days back from the extract date.

## Data coverage (added 2026-10-07)

For every scope (org and each domain) and each kind of input, the snapshot's `reporting` list says how many products have it and which do not. Each metric names the input it needs (`coverage` in `registry/metrics.yaml`), and the app shows the coverage next to the number whenever it is incomplete, so a figure built on missing data never reads like a delivery result. The "Reporting coverage" strip sits at the end of the executive overview and of each domain page, and only while some input is below 80%.

| Kind | Base | Has the data when |
| --- | --- | --- |
| `gates` | Active products | At least one gate event |
| `plans` | Active products without a G4 | A planned GA date |
| `reviewed` | Active products | The DPO has reviewed the row at least once |
| `dpo` | Active products | A DPO is named |
| `usage` | Live products | An active-users figure |
| `consumers` | Live products | A first-consumer date |
| `validation` | Active products (only when validation results are in the inbox) | A finish-spec score |
| `nextdata` | Active products (only when a NextData listing is in the inbox) | At least one deployment |
| `github` | Active products (only when a GitHub extract is in the inbox) | A matched repository |

## Trend

For each of the last four quarters including the current one, and each domain: products whose `firstG4Date` falls in the quarter, and the target from the Targets sheet (null when none).

By week (added 2026-10-08, `snapshot.weekly`): for each of those quarters and every ISO week (Monday to Sunday) overlapping it, the products whose `firstG4Date` falls between the quarter start and the end of that week (or the quarter end, or the as-of date, when earlier), in total and per domain. The current quarter stops at the as-of week. The app draws them against a target pace that rises evenly from zero to the quarter's target at its last week; the quarter's bar unfolds into its weeks when the unit changes.

## What changed

Up to three lines comparing the current snapshot with the last approved one: new certifications, new flags raised, flags cleared. The first snapshot states that there is no previous week.

## Data-quality rules

| Severity | Rule | Code |
| --- | --- | --- |
| Blocker | Required sheet or column missing; file unreadable | `MISSING_TABLE`, `MISSING_COLUMN`, `UNREADABLE` |
| Blocker | Duplicate URN in Products | `DUPLICATE_URN` |
| Blocker | Gate events not in gate order within an iteration, or dated after the as-of date | `GATE_ORDER`, `FUTURE_DATE` |
| Blocker | G2, G3 or G4 without a G1 | `NO_G1` |
| Blocker | Gate event for an unknown URN | `UNKNOWN_URN` |
| Blocker | Unparseable date or number | `BAD_VALUE` |
| Blocker | DPO comment matches a screening pattern (email, phone, ID-like string) or term | `SCREENING` |
| Blocker | Snapshot fails schema validation | `SCHEMA` |
| Warning | Gate event without evidence link | `NO_EVIDENCE` |
| Warning | Active product without a plan for its next gate, or a plan for a gate already passed | `NO_PLAN`, `STALE_PLAN` |
| Warning | Live product without a usage figure | `NO_USAGE` |
| Warning | Product with G2 to G4 history but no G1 (excluded from cycle time) | `NO_G1_WARN` |
| Warning | Unknown column ignored | `UNKNOWN_COLUMN` |
| Warning | NextData listing present but empty | `SOURCE_MISSING` |
| Warning | NextData, validation, GitHub and crosswalk checks (see "Platform warnings" below) | `ND_*`, `VAL_*`, `GH_*`, `XWALK_*` |

## Platform sources (added 2026-10-07)

Optional inbox files, read every week when present. They never block a pack: every problem is a warning.

| File | What it is | Grain |
| --- | --- | --- |
| `nextdata/*.txt` | NextData `dp list` output: name, environment, version, state, RPC, URL | One row per deployment |
| `nextdata/*.csv` with a `parent` column | NextData domain tree; used only to check domain hygiene and that its counts reconcile with the listing | One row per domain |
| `nextdata/*.csv` otherwise | NextData catalog lookup: name, domain, version, state, owner (later URN and ports) | One row per name |
| `validation/*.xlsx` or `*.csv` | Repo validation tool results: finish-spec score, component scores, owner declared in the repository. Either the status inventory (a `keyid` column) or the audit workbook itself (a `Data product` column naming the audited folder, `name-version (copy)`, read as keyid and version; `Completeness score` is the score) | One row per keyid |
| `github/*.csv` | `dp fetch-github` output: `repositories.csv`, `deployments.csv`, `deployment_statuses.csv`, `fetch.csv` (when and from which org), `issues.csv` (requests GitHub did not answer) | One row per repository, deployment or status |
| `crosswalk.csv` | Program lead's decisions per name: product, counted or not, business domain (empty: use the product-to-domain map), display name, reviewed. Rows with `source` github link a repository to a product | One row per name |

### From names to products

NextData lists deployments, not products, and the validation tool has its own keyids. The rules below run in order; `crosswalk.csv` overrides any of them, name by name (`scripts/seed_crosswalk.py` writes a first version to review).

1. **Older names.** A bare name `X` and a team-prefixed name `dp-<team>-X` are one product, and the prefixed name is the product's key, unless `X`'s repository or NextData domain points to another team (then `dp-<team>-X` is a separate product built on `X`). `X-vN` is another version of `X`.
2. **Validation keyids** match a NextData name exactly, with a team prefix, with an `-nxd` suffix, with the same words in another order, as the prefix of exactly one name, or as a clone (identical results) of a matched keyid. A keyid that matches nothing is a product known only to the validation tool ("Not deployed").
3. **Not counted** (listed with the reason in the data-quality report): names matching a pattern in `registry/platform.yaml` (template, test, sandbox or synthetic, placeholder `dp-<team>-<word>-dp`); tooling teams (`gov`, `nxd`); every deployment unreachable and the catalog does not know the name; deployed only in a demo environment and never validated.
4. **Team layer.** The `<team>` in `dp-<team>-…` is the EDP team subdomain (ops, hcp, patient, claims): Source systems, HCP team, Patient team, Claims team. For a bare name: its repository name (`…-ops-dp-…`), else its NextData domain (`EDP/OPS`), else the team of other bare products with the same first word, else a team word in the name. The team is shown on the product page; it is not a sub-group inside the domain (changed 2026-10-07).
5. **Business domain** (Patient, HCP, Market access, Channel partner, Revenue / vials, Medical affairs, Logistics, or Unknown; `registry/domains.yaml`), first match wins:
   1. the crosswalk's `domain` column, for one name;
   2. `registry/product-domains.yaml`, the durable product-to-domain map, keyed by product key, NextData name or keyid;
   3. the name rules (`domain_rules` in `registry/platform.yaml`): a phrase in the name (`channel-partner`, `buy-n-bill`) or a whole word (`claims`, `payer`, `mmit` → Market access; `hcp`, `veeva`, `ama`, `territory` → HCP; `patient` → Patient; `msl`, `kol` → Medical affairs; `logistics`, `3pl` → Logistics; `revenue`, `vial`, `sales` → Revenue / vials);
   4. the team (`team_domains`: patient → Patient, hcp → HCP, claims → Market access);
   5. `default_domain` (Unknown).

   `scripts/seed_crosswalk.py` leaves `domain` empty and shows the result in `domain_by_rule` with the rule that decided, so a seeded crosswalk never freezes today's mapping.
6. **Display name**: the crosswalk, else the repository's business name when it is written as a proper name, else the technical name without its team prefix (acronyms in `registry/platform.yaml` stay upper case). Two counted products with the same display name get their team in brackets.
7. **Runtime** of a product: Started if any of its deployments is Started, else Failed, else Unreachable; Not deployed when NextData has none. Its environment is the best one among its running deployments (prod, nxd, demo, dev), and its NextData link is that deployment's URL from the listing (each deployment's own URL is listed too).

A register product is matched to its platform product by URN: `nxd:<name>`, a catalog URN, or a URN whose last segment is a NextData name or keyid.

### GitHub repositories (added 2026-10-30)

`dp fetch-github` reads every repository of the org whose name contains `-dp-` (read-only). A repository `edp-<team>-dp-<x_y>` belongs to a register product, first match wins:

1. a crosswalk row with `source` github and the repository as `name`: `product` is the register URN or a NextData name; `include` no leaves the repository out;
2. the repository's `data_product_urn` custom property equals the register URN (no repository has it yet; it is read as soon as the org defines it);
3. `dp-<team>-x-y`, `x-y` or `x-y-nxd` is the last segment of the register URN or a NextData name of the product.

Repositories of tooling teams (`gov`, `nxd`) and with template or test names (`registry/platform.yaml`) are not counted. When two repositories match one product, the first by these rules (then by name) is used.

### Platform warnings

| Code | Rule |
| --- | --- |
| `ND_NOT_FOUND` | A counted name is in the listing but the catalog lookup returned NOT FOUND. |
| `ND_NO_OWNER` | NextData records no owner (one line with the count). |
| `ND_DOMAIN` | Team-prefixed products registered under another NextData domain than their team domain `EDP/<TEAM>` (one line per team and domain). |
| `ND_RECONCILE` | The domain tree's top-level counts do not add up to the number of deployments in the listing. |
| `ND_DUPLICATE` | One product is deployed under two or more names (retire the older one). |
| `XWALK_MISSING`, `XWALK_NEW`, `XWALK_UNREVIEWED` | No crosswalk; names decided by rule because the crosswalk does not list them yet; crosswalk rows not marked reviewed. |
| `ND_NOT_IN_REGISTER` | A counted platform product has no row on the Products sheet. |
| `ND_NOT_IN_CATALOG` | A register product (other than `pending:`) is not in the NextData listing. |
| `ND_EXCLUDED` | A register product is one the platform rules leave out (the crosswalk can count it). |
| `ND_STATUS` | Live in the register, but NextData shows no running production deployment. |
| `VAL_STALE`, `VAL_NO_DATE` | Validation results older than 14 days at the as-of date; no run date in the file (the file date is used). |
| `GH_STATUS` | Live in the register, but the product's repository has no successful production deployment. |
| `GH_NOT_IN_REGISTER` | Counted repositories that match no product on the Products sheet (one line per EDP team). |
| `GH_DUPLICATE` | A second repository matches a product that already uses another; its deployments are not counted. |
| `GH_STALE` | The GitHub extract is more than 7 days older than the as-of date. |
| `GH_FETCH` | Requests GitHub did not answer when the extract ran (from `issues.csv`), or deployments that name no known repository. |

The validation tool's check IDs (A8, B3, D3, G1, G2, …) are not governance gates. The dashboard always writes them as "check G2".

## Decisions recorded here (from the engineering plan, section 17, in `docs/archive/`)

1. Status mapping: as above.
2. Inbox location: a OneDrive-synced SharePoint folder owned by the program team; the pipeline only sees a local path.
3. Cancellation before GA: `cancelled_on` on the Products sheet. The product keeps its stage and shows status Cancelled; it leaves every active-product metric.
4. Consumer definition: Release 1 is self-reported, so the DPO decides. Proposal for Release 2: product-team and service-account access do not count.
5. Quarters are calendar quarters. The program lead sets each domain's target in the Targets sheet.
