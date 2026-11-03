# Vendored react-bits components

Source: https://github.com/DavidHDev/react-bits (main branch, Oct 2026).
License: MIT + Commons Clause. Use inside this application is permitted; redistributing the
components themselves is not. See ADR-001 and ADR-002.

Each file keeps the original structure and animation logic, restyled with the argenx tokens and
adapted where its header comment says so (controlled props, reduced-motion support, keyboard
behaviour). Updates are manual copies.

| Component | Variant | Used for | Dependency |
| --- | --- | --- | --- |
| GlareHover | JS + CSS, verbatim, plus a `sweep` state | view navigation tabs; the glare crosses the new tab on view change | – |
| CountUp | TS + Tailwind | quarter ring figure and the speed and adoption figures | motion |
| Stepper | TS + Tailwind | G1 to G6 gate timeline on the product view | motion |

Removed on 2026-11-03: AnimatedList (the Needs attention list stopped using it on 2026-10-08).
Removed on 2026-10-06: GooeyNav (replaced by GlareHover at the product owner's request) and
SpotlightCard (the tiles it decorated were replaced by the quarter rings and the stat strip).
The cluster map's pointer-proximity magnification follows react-bits Dock's idea but is our own code.
