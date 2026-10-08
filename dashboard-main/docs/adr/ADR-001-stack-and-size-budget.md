# ADR-001: App stack, animation library and size budget

Date: 2026-10-05 · Status: accepted · Decided by: product owner (@K) with A1

## Context

The engineering plan (section 11) names React, TypeScript, Vite with a single-file plugin, TanStack Table and "Recharts or Tremor", with a template budget of 400 KB and a 2-second open time. The product owner asked for UI built from react-bits components (MIT + Commons Clause), chosen for a restrained executive look.

Measured with esbuild (minified, uncompressed, which is what a `file://` open pays):

| Layer | KB |
| --- | --- |
| React + ReactDOM 19 | 217 |
| motion (tree-shaken subset used by react-bits) | 144 |
| Recharts, one composed chart | 411 |
| TanStack Table | 60 |
| gsap | 69 |

React alone is more than half of the 400 KB figure, which was set before anything was measured.

## Decision

1. Stack: React 19, TypeScript, Vite 6 + `vite-plugin-singlefile`, Tailwind 4 (build-time only), `motion` as the single animation runtime. No gsap, no react-router (a 40-line hash router instead). TanStack Table was dropped on 2026-10-07 for a small in-house table (`app/src/lib/table.ts`), saving about 60 KB.
2. Charts are hand-written SVG components animated with `motion`. Recharts is not used.
3. react-bits components are vendored into `app/src/components/reactbits/` with attribution, restyled with brand tokens. Used: CountUp, AnimatedList, Stepper, GlareHover (SpotlightCard and GooeyNav were removed on 2026-10-06, see ADR-002). No background effects.
4. Budget: template HTML ≤ 640 KB before snapshot injection (raised from 600 KB on 2026-10-07 by the product owner, for the grouped domain table, rather than trimming code). The hard rule stays the 2-second open from `file://` on a standard laptop, measured by the end-to-end suite.
5. All motion respects `prefers-reduced-motion` and is disabled in print.

## Consequences

- One runtime animation dependency (motion), approved here as required by the plan's guardrails.
- The quarterly chart is ~3 KB of our own code instead of 411 KB; it needs its own tests.
- react-bits updates are manual copies; the vendored file header records the source version.
- The Commons Clause forbids reselling the components themselves, not using them in this app.
