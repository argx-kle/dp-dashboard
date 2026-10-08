# ADR-002: Dark argenx theme, brand fonts and the product health signal

Date: 2026-10-06 · Status: accepted · Decided by: product owner (@K)

## Context

After the H2 preview the product owner asked for a dark background, no draft watermark, no all-caps text, few fonts per view, a domain cluster map in which every product carries a red, orange, yellow or green signal, and the react-bits GlareHover effect on view navigation. The argenx brand materials (PowerPoint template 3.0 and the Portals brand guidelines) were supplied. The redesign followed the impeccable workflow; the product owner chose the category-standard dashboard composition with Linear, the Vercel dashboard and Apple Health's summary as the craft bar.

## Decision

1. **Theme.** Dark on screen, built from the Vast Blue family (ground `#001A22`, panels `#002834`), Clear Blue for focus and the current view, brand tonal blues for data. Print and the PDF one-pager switch to a light palette through CSS variables.
2. **Type.** Instrument Sans for everything, Inria Serif italic once (the product title), as named in the Portals guidelines. Both are subset to Latin, converted to woff2 and inlined (55 KB). SIL Open Font License texts ship in `app/src/assets/fonts/`. Sentence case everywhere.
3. **Health signal.** Each product gets one signal, computed by the pipeline (`ProductRow.signal`) from the flag registry: grey when retired or cancelled, otherwise the most severe flag signal (red Overdue; orange Slipping, Unused; yellow No DPO, Not updated, Pending URN), green when active with no flags. Which flag raises which signal is one line in `registry/flags.yaml`. This replaces the earlier `coloured`/`colour` flag fields (snapshot contract change, schema 1.0 updated in place before first release).
4. **Signal colours.** Brand semantic red `#E55E5E`, yellow `#FFE224`, green `#76CB5F`, and Activated Orange `#FF7B24`. The validator shows orange and green collapse under deuteranopia (ΔE 3.4) and no orange clears both that and the red/orange normal-vision floor, so every signal also has its own ring shape: double (red), broken (orange), dashed (yellow), solid (green), dotted (grey). The same mark is used on the map, legend, tables, list and preview.
5. **Lifecycle status** is shown with four pips (gates passed to G4) plus the status words, with no colour meaning, so it never competes with the signal.
6. **No watermark.** Draft state shows in the footer only ("Draft, not yet signed off"); the header chip was removed on 2026-10-07 at the product owner's request.
7. **Navigation** uses the react-bits GlareHover (JS + CSS variant, vendored verbatim plus a `data-sweep` state) on the three view tabs; the glare crosses the new tab once on view change. GooeyNav and SpotlightCard were removed.
8. **Budget.** Template 594 KB against the 600 KB budget of ADR-001 (raised to 640 KB on 2026-10-07; see ADR-001). TanStack Table was later replaced by a hand-written table (about 60 KB saved).

## Consequences

- Every UI change is checked against the brand rules above and the tokens in `app/src/styles/tokens.css`.
- Signal semantics now live in the registry and are covered by acceptance tests (AT-FLAG-10, AT-FLAG-11).
- Print keeps the domain table instead of the map, because hover does not exist on paper.
