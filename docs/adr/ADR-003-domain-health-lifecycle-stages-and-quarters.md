# ADR-003: Domain health, lifecycle stages and the quarter selector

Date: 2026-10-08 · Status: accepted · Decided by: product owner (@K)

## Context

Executive feedback on the 2026-10-07 dashboard: product counts on the summary must be explicit ("0 of 3 data products"); a health colour per product reads as subjective, while the question in the room is whether a whole domain will hit its quarter; gate codes (G1 to G4) mean nothing to most executives; "live products used by others" is too hard to track; the room wants to look back at earlier quarters and see delivery week by week; scope must reach beyond Commercial to TechOps, R&D and G&A.

## Decision

1. **Health per domain, not per product.** The pipeline computes `snapshot.health` per quarter and scope: on track (certified + on-plan forecast reach the target), at risk (reached only if the late products also go live), off track (not even then), no target. Late = not yet live, go-live due by the quarter end, not on plan. Rule chosen by the product owner over a shortfall count or a share of target. Products no longer show a health colour; `ProductRow.signal` remains in the contract and only ranks the attention list. This supersedes points 3 and 4 of ADR-002 for display.
2. **Six business stages** (`ProductRow.lifecycle`): Ideation, In design, In development, In testing, Live, Failed / retired, derived from the gates. Each bubble on the map carries the product's name, and its ring is coloured by stage on one brand-blue ramp and drawn a fifth per stage, so health colours (red, orange, yellow, green) are reserved for domains.
3. **Quarter selector.** The pipeline rebuilds the closed trend quarters as of their last day from gate history (`snapshot.quarters`); the app overlays the chosen quarter on the snapshot. Plans, flags and usage are not historical, so a closed quarter shows none of them rather than today's values.
4. **Weekly trend.** `snapshot.weekly` holds cumulative certifications per ISO week; the trend switches between quarters and weeks, the quarter's bar unfolding into its weeks on one shared y scale.
5. **Areas.** `area` on each domain (Commercial, TechOps, R&D, G&A, Unassigned); empty areas and domains are hidden on the map and the summary.
6. **Metrics.** `inter_product_share` removed. The strip shows time to production, time to first consumer, users per live product and certified this quarter.
7. **Deferred.** Technical readiness as respected vs failing policies waits for the product owner's pass/fail counts per product; the strip is unchanged.

## Consequences

- Schema 1.0 gains `DomainInfo.area`, `ProductRow.lifecycle`, and optional `health`, `weekly`, `quarters` (in place, before first release). The snapshot grows from about 84 KB to 150 KB for 25 products; the template stays within its 640 KB budget (591 KB).
- The register template gains the new domains in its validation list; its columns are unchanged.

## Revision, same day (product-owner review round 2)

- **Health is a pace forecast.** Expected by today = target × share of the quarter elapsed; pace = certified ÷ expected. Ahead ≥ 110%, On track 90–109%, At risk 70–89%, Off track < 70%; a closed quarter reads Above, Met or Below target. Replaces the "recoverable" rule of point 1; forecast and late remain as context.
- **Status board** in place of the domain bars: columns by health, each domain a `certified/target` pill. The summary leads with one sentence instead of a heading and a list.
- **Stage rings in colour and shape** (grey dotted, yellow dashed, orange broken, blue half, green solid, red double) in place of the blue ramp and arc length of point 2; a yellow dot marks products that need attention. Domain health uses the same ring shapes, always with its word.
- **Next gate** ("G4 Certify · 20 Oct") on the hover card, the tables and the product page; the Definitions page shows the gates between the stages and explains each.
- **Areas**: TechOps, R&D and G&A are separate domains; no merged heading.
- **Last updated** moved from the header to the footer.
- **Showcase week** (`scripts/make_showcase.py`, week 2026-W47, 58 made-up products in all four areas; 60 since 2026-11-02) is the demo and the dev preview; the golden fixture stays the test reference.

## Revision, round 3

- Health marks are coloured icons (trend up, check, warning, stop sign, trend down), not rings.
- Board pills fill by certified ÷ target and show **certified**/target, with one `live / target` label.
- Stage marks fill one quarter of the circle per stage, slate to amber (indigo, violet, magenta in between). Ideation stays dotted, Failed / retired red double. This replaces the vivid ring shapes of round 2.
- "Products by domain" shows no health: it shows products at one date; health belongs to the quarter panel, which now holds the quarter title and selector.
- Flag icons take their registry signal colour. Domain figures hide while a domain is expanded.
- The "Updated" time is back in the header, as quiet text.
- User-facing definitions follow Simplified Technical English.

## Revision, round 4

- Expected by today is a whole number (target × part of the quarter passed, halves up), and health is judged on it.
- "At risk" is shown as "Behind"; the status key stays `at-risk`.
- The narrative has one fact per line; the key names every part of the ring.
- Flag reasons are rewritten in plain words ("G4 Certify is 31 days late. Due 20 Oct.").
- Stage words take their stage colour. The attention list fills the height of the panel beside it and names the rest in a footer; it no longer uses the react-bits AnimatedList.

## Revision, round 5

- Stage colours become one green ramp, brighter as the product advances (the round 3 slate-to-amber ramp read as too colourful).
- Hovering a product dims every map on the page, not only its own area.
- The quarter key line is replaced by hover labels on the ring.
