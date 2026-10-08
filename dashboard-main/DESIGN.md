---
name: Data Product Delivery
description: argenx weekly executive dashboard for data product delivery, dark Vast Blue world with a shape-coded health signal
colors:
  bg: "#001a22"
  panel: "#002834"
  panel-2: "#06323f"
  panel-3: "#0b3c4a"
  line: "#134451"
  line-strong: "#22596a"
  ink: "#f2fafc"
  ink-2: "#c5dbe2"
  ink-3: "#93b2bc"
  on-light: "#001a22"
  clear: "#d2f1fa"
  link: "#74cbe5"
  confidence: "#18687f"
  data-1: "#74cbe5"
  data-2: "#2397b8"
  track: "#0b3c4a"
  sig-red: "#e55e5e"
  sig-orange: "#ff7b24"
  sig-yellow: "#ffe224"
  sig-green: "#76cb5f"
  sig-grey: "#9fa5ad"
typography:
  display:
    fontFamily: "Instrument Sans, Arial, Helvetica, sans-serif"
    fontSize: "48px"
    fontWeight: 700
    lineHeight: 1
  figure:
    fontFamily: "Instrument Sans, Arial, Helvetica, sans-serif"
    fontSize: "32px"
    fontWeight: 600
    lineHeight: 1.05
  title:
    fontFamily: "Instrument Sans, Arial, Helvetica, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  heading:
    fontFamily: "Instrument Sans, Arial, Helvetica, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  lead:
    fontFamily: "Instrument Sans, Arial, Helvetica, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "Instrument Sans, Arial, Helvetica, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "\"kern\", \"liga\", \"calt\""
  small:
    fontFamily: "Instrument Sans, Arial, Helvetica, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
  accent:
    fontFamily: "Inria Serif, Georgia, serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  swatch: "3px"
  tag: "6px"
  control: "10px"
  panel: "16px"
  pill: "999px"
spacing:
  hairline: "1px"
  tight: "8px"
  row: "12px"
  panel: "24px"
  section: "24px"
  gutter: "24px"
  gutter-wide: "40px"
components:
  panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.panel}"
    padding: "24px"
  nav-tab:
    textColor: "{colors.ink-3}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
    padding: "6px 16px"
  nav-tab-active:
    backgroundColor: "{colors.panel-3}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "6px 16px"
  segmented-option:
    textColor: "{colors.ink-3}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    padding: "4px 14px"
  segmented-option-active:
    backgroundColor: "{colors.panel-3}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "4px 14px"
  filter-chip:
    textColor: "{colors.ink-3}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    height: "32px"
    padding: "0 12px"
  filter-chip-active:
    backgroundColor: "{colors.panel-3}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    height: "32px"
    padding: "0 12px"
  flag-badge:
    textColor: "{colors.ink-2}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    height: "24px"
    padding: "0 8px"
  source-label:
    textColor: "{colors.ink-3}"
    typography: "{typography.small}"
    rounded: "{rounded.tag}"
    height: "20px"
    padding: "0 6px"
  list-row-active:
    backgroundColor: "{colors.panel-3}"
    rounded: "{rounded.control}"
    padding: "12px"
  preview-card:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "20px"
    width: "300px"
  detail-box:
    backgroundColor: "{colors.panel-2}"
    rounded: "{rounded.control}"
    padding: "14px 16px"
---

# Design System: Data Product Delivery

## Overview

**Creative North Star: "The Quiet Control Room"**

A dark, still room in Vast Blue where the only things that light up are the things that need a leader's attention. The dashboard is read projected, by several executives at once, so the system is built for distance: one strict seven-step type scale, large rings and figures, generous 24px panel padding, and colour that is either brand blue (progress, place, data) or a reserved health signal (red, orange, yellow, green, grey). Everything else is tonal neutral. The craft bar is the category-standard dashboard executed at the level of Linear, the Vercel dashboard and Apple Health's summary; no novelty worlds.

The picture comes first: progress rings for the quarter and each domain, a cluster map where every product is a bubble carrying its signal ring, then figures one hover or one click away. Depth is tonal, not cast: the ground, panels and raised states are four steps of the same blue, separated by one-step-lighter hairlines. Only things that float above the page (the bubble preview, the chart tooltip) carry a shadow.

Motion explains and then stops. Rings draw and figures count once on load, bubbles lift on hover or focus, the tab glare sweeps once on view change, and all of it is off under reduced motion. Print swaps the whole palette to light through the same variables.

**Key Characteristics:**
- Vast Blue tonal neutrals; Clear Blue marks place and focus; brand tonal blues carry data.
- A reserved five-step health signal, always paired with a ring shape or an icon.
- Instrument Sans for everything; Inria Serif italic for exactly one word, in the product title.
- Sentence case throughout; no all-caps.
- Panels with 16px corners and hairline borders; related figures share one panel split by 1px rules.
- Signature interaction: the cluster map bubble lifts and previews, linked to the Needs attention list.

## Colors

A cold, low-chroma Vast Blue ground with one pale accent for place, two data blues, and a saturated health scale that is the only warm colour on screen.

### Primary
- **Clear Blue** (`clear`): where you are. Focus outline (2px, offset 2px), the bubble focus ring, caret and form accent colour, the current sort arrow, the serif title word, and the hover colour for figure and name links. Never a panel fill.
- **Confidence Blue** (`confidence`): text selection background; becomes the link colour in print.

### Secondary
- **Data Blue** (`data-1`): certified progress. Solid ring arcs, certified bars, the matching legend swatch, completed gate steps.
- **Deep Data Blue** (`data-2`): forecast. Always used faint (45 to 50% opacity) on top of certified, so planned never reads as done.
- **Link Blue** (`link`): inline text links, underlined at 45% of the text colour with a 3px offset, full colour on hover. It shares its hex with Data Blue (see Do's and Don'ts).

### Tertiary
- **Off Track Red** (`sig-red`): off track and overdue; also the shortfall to target on rings (thin arc) and bars (dashed outline), and "days late" notes.
- **Activated Orange** (`sig-orange`): at risk (slipping, unused).
- **Signal Yellow** (`sig-yellow`): attention (no DPO, not updated, pending URN).
- **On Track Green** (`sig-green`): on track and an on-track verdict.
- **Retired Grey** (`sig-grey`): retired or cancelled products.

### Neutral
- **Abyss Ground** (`bg`): page ground, sticky header, the segmented control trough, retired bubble fill.
- **Vast Blue** (`panel`): every panel surface.
- **Raised Blue** (`panel-2`): row hover, floating preview and tooltip, cluster regions, detail boxes.
- **Selected Blue** (`panel-3`): current tab, active segment or filter, lit list row. `track` holds the same value for empty progress tracks.
- **Hairline** (`line`): panel borders, table rules, the 1px gaps of ruled strips.
- **Strong Hairline** (`line-strong`): borders on chips, tags, floating cards and the current tab; the ring track at 55%; the scrollbar thumb.
- **Ink** (`ink`, 15:1 on panel): names, figures, headings.
- **Ink Secondary** (`ink-2`, 10:1): body copy, reasons, status words.
- **Ink Muted** (`ink-3`, 6.6:1): labels, metadata, counts, inactive tabs, axes.
- **On Light** (`on-light`): figures printed inside light data bars.

### Named Rules
**The Signal Reserve Rule.** Red, orange, yellow, green and grey mean product health or a flag and nothing else, and they never appear alone: every use carries its ring shape (double, broken, dashed, solid, dotted) or a flag icon and label.

**The Pale Pointer Rule.** Clear Blue shows where you are (focus, current view, hovered figure). It is a line or a text colour, never a surface.

**The Token Mirror Rule.** Colours come from the CSS tokens or their JS mirror for SVG and motion; print overrides the same variables to a light palette, so a hard-coded hex silently breaks print.

## Typography

**Display Font:** Instrument Sans (with Arial, Helvetica)
**Body Font:** Instrument Sans (with Arial, Helvetica)
**Accent Font:** Inria Serif italic (with Georgia), one word only

**Character:** A clean grotesque doing all the work at a few clearly separated sizes, with a single serif italic word as the brand's signature. Both faces are subset to Latin and inlined.

### Hierarchy
- **Display** (700, 48px, 1): the certified-this-quarter figure inside the quarter ring. One per screen.
- **Figure** (600, 32px, 1.05): headline metric values in the speed and adoption strip; proportional digits.
- **Title** (600, 28px, 1.15, -0.01em): page titles and the quarter heading.
- **Heading** (600, 20px, 1.3, -0.01em): panel headings; also the figure inside domain rings.
- **Lead** (600, 17px, 1.5): the product title in the header, preview card names, the quarter verdict, tooltip figures.
- **Body** (400 to 600, 15px, 1.55): copy, table cells, tab labels, cluster labels. Prose blocks cap at 68ch.
- **Small** (400 to 500, 13px, 1.45): labels, metadata, chips, legends, counts, footer, chart axes.

### Named Rules
**The Seven Steps Rule.** Text is 13, 15, 17, 20, 28, 32 or 48px. Nothing in between, including SVG chart labels.

**The One Serif Word Rule.** Inria Serif italic appears once, on "delivery" in the header title, in Clear Blue. Nowhere else.

**The Sentence Case Rule.** All text is sentence case. No all-caps labels, no letter-spaced small caps. One exception: the product's proper name, "Data Product Delivery", is title case (product-owner decision, 2026-10-07).

**The Aligned Numbers Rule.** Tables, axes and counts use tabular numerals; large figures keep proportional digits.

## Layout

A centred column capped at 1440px, with 24px side gutters that widen to 40px from 1024px. Sections stack with 24px gaps under a sticky 64px header (wordmark, divider, title, week and as-of date, tabs pushed right). Panels pad 24px; table cells pad 12px with 24px at the outer edges. The executive overview reads in rows: quarter ring beside a ring per domain (four to a row) in one split panel; the cluster map beside a 380px Needs attention column from 1280px; then Technical readiness when platform files are in the inbox; then the four-up Speed and adoption strip (two-up from 640px, one-up below); then the quarter chart; and last, Reporting coverage while inputs are incomplete. The domain page follows the same order: its map and attention list, Technical readiness, Speed and adoption, its product table, and Reporting coverage last. Below 1280px the attention list stacks under the map. The executive overview prints on one A4 landscape page, with the domain table in place of the map.

**The Ruled Strip Rule.** Related figures share one panel and are divided by 1px hairlines (a hairline ground showing through 1px gaps), not split into separate floating cards.

## Elevation & Depth

Tonal layering. Depth is four steps of Vast Blue (ground, panel, raised, selected) plus hairline borders; panels themselves cast nothing. Shadows are reserved for the two things that float over content, both soft and dark-tinted. The active map bubble gets a blurred glow in its own signal colour (25% opacity, 6px blur), which is a highlight rather than elevation.

### Shadow Vocabulary
- **Preview lift** (`box-shadow: 0 24px 48px -16px rgba(0,8,12,0.75)`): the cluster map product preview card.
- **Tooltip lift** (`box-shadow: 0 16px 32px -12px rgba(0,8,12,0.7)`): the quarter chart hover tooltip.

### Named Rules
**The Flat Panel Rule.** Panels sit flat on the ground with a hairline. Shadow means "this floats over the page and will go away".

## Shapes

Soft, consistent geometry. Panels are 16px; controls, list rows and detail boxes 10px; tabs, chips, toggles and badges are full pills; small source tags are 6px; legend swatches 3px. Borders are always 1px hairlines. The circle is the system's recurring form: the quarter and domain progress rings, the product bubbles, the signal marks and the gate steps are all rings, and domain regions on the map are the union of halos around their bubbles, so a cluster hugs its members.

## Components

### Navigation
- **Style:** three pill tabs (Executive, Products, Definitions) on the right of the sticky header, built on the vendored react-bits GlareHover.
- **States:** inactive is Ink Muted text on no fill, Ink on hover; current is Selected Blue fill, Strong Hairline border, Ink text.
- **Signature:** a Clear Blue glare (32% opacity, -30 degrees) crosses the tab once on hover and once on the newly current tab after a view change (800ms); none under reduced motion.
- **Mobile:** the header wraps; tabs drop to their own line.

### Chips and badges
- **Flag badge:** pill, 24px (32px medium size), Strong Hairline border, no fill, 14px SVG icon in Ink Muted, Ink Secondary label. One calm style for every flag (product-owner decision, 2026-10-07): colour lives on the signal mark and ring arcs, so flags never out-shout the numbers. Reason in the title tooltip.
- **Sign-off state:** not in the header (product-owner decision, 2026-10-07). The footer states "Draft, not yet signed off" or "Signed off by … on …".
- **Filter chip and segmented toggle:** pills; active is Selected Blue with Ink text, inactive Ink Muted with a hairline that strengthens on hover. The Map / Table toggle sits in an Abyss Ground trough.
- **Source label:** 20px, 6px corners, Strong Hairline border, Ink Muted: marks self-reported and external values.

### Cards / Containers
- **Corner Style:** 16px.
- **Background:** Vast Blue on the Abyss Ground.
- **Shadow Strategy:** none (see Elevation & Depth).
- **Border:** 1px Hairline.
- **Internal Padding:** 24px; headings sit 24px from the top with content following at 8 to 20px.

### Health signal mark
One drawing at every size (map bubble, legend, tables, list, preview): a circle tinted 18% in the signal colour inside its ring shape. Red is a double ring, orange a ring with a quarter missing, yellow dashed, green solid, grey dotted with no tint. Paired in text with its label (Off track, At risk, Attention, On track, Retired or cancelled).

Not yet reported: active, no flag, and the owner has never reviewed the row. A thin (1.1px) Ink Muted outline with no fill, the quietest mark on the map (bubble drawn at 94%). It replaces a wall of yellow during onboarding and turns green at the first review.

### Progress ring
Track in Strong Hairline at 55%; certified in Data Blue, forecast in Deep Data Blue at 45%, and any shortfall to target as a thinner red arc, separated by small gaps with round caps. Figure and "of N target" sit centred inside. Arcs draw once on load (900ms, staggered 350ms).

### Cluster map and preview (signature)
Domains are regions on Raised Blue outlined by a Hairline (Strong Hairline when lit); the EDP team is shown on the product page, not on the map. Each product is a bubble filled with its signal tint (off track loudest at 38% and drawn 15% larger, on track quietest at 6%) with its signal ring and the last gate passed in the centre. The pointer magnifies nearby bubbles up to 14%; hover or focus lifts one to 125% on a spring, dims the others to 35%, lights the matching Needs attention row and opens a 300px preview card (Raised Blue, 20px padding, Preview lift shadow): name, domain, signal and lifecycle pips, the first flag's reason, and at most three facts. The card stays within the viewport below the header.

### Lists and tables
- **Needs attention:** rows with an 18px signal mark, bold product name, the first flag's reason and the domain and owner in muted text; hovering or focusing lights the row in Selected Blue and the bubble on the map. Overflow becomes one "N more" link line, never an inner scroll.
- **Tables:** 15px cells with tabular numerals, Hairline row rules, Raised Blue row hover, small muted sortable headers with a Clear Blue arrow on the sorted column. Names and dates never wrap. Numbers are semibold Ink; their labels muted. The owner column is headed "Data product owner". A signal mark in a row shows its name on hover ("On track").
- **Domain rows with a disclosure triangle:** each domain row is led by a 12px filled triangle that rotates 90° when open (`aria-expanded`, `aria-controls`). *Executive Table view:* the domain name at 17px semibold with its Behind badge, a second line of signal counts (12px mark, 15px semibold count per signal present), then products, live, in pipeline, certified of target, median G1→G4 and unused as 17px semibold values; every figure links to its products. Rows start closed, open to a compact product table and print closed; it fits the panel from 1280px. *Products page:* the row carries only the domain name and its total in small muted text ("12 products", or "3 of 12 products" when filtered); rows start open and print open. "Expand all / Collapse all" sits above.
- **Scrolling table viewport (Products, domain view):** the table box fills the window below the header and scrolls on both axes; the column header row stays pinned, the signal and product columns stay frozen on the left with an edge shadow once scrolled, and pressing on empty table space and dragging pans sideways (grab cursor, 4px threshold). The browser's own scrollbar is the only scrollbar; no hint line.
- **Product search:** a 48px field above the filters (Strong Hairline border, Clear Blue on focus, search icon, "/" key hint). Matching is order-independent and forgiving (substring, letters in order with gaps, one typo); matched letters in names are highlighted in a 20% Clear Blue wash.
- **Reporting coverage strip:** one ruled strip at the end of the executive overview and of each domain page while any input (gate dates, planned GA dates, owner reviews, owners, usage, first consumers, validation score, NextData) is below 80% of its base. Each cell: small label, the count in Heading weight as a link to the products missing it, "of N base" muted, and a 4px Data Blue bar on Track. Under every number whose input is incomplete, one muted Small line says so ("Gate dates for 5 of 6 active products") and links to the same list. The strip disappears once inputs are complete; the notes stay.
- **Technical readiness strip:** the Speed and adoption strip's twin, directly above it, shown only when platform files are in the inbox: median finish-spec score and failing in NextData ("of N deployed"), two-up. Source labels say Validation tool or NextData.
- **On the platform (product page):** an "Open in NextData" link (Clear Blue, arrow icon) beside the heading goes to the best deployment's NextData page. Two cells. Runtime: state and best environment in Lead, the EDP team and NextData domain and other names muted, a small deployments table with an Open link per row where non-running states are bold Ink (never a signal colour). Finish-spec validation: score in Lead with the run date, the owner status in the repository, and one 6px Data Blue bar per component. A Facts cell summarises both and scrolls to the section.
- **Platform column:** on the products page when platform data exists: runtime (bold Ink when Failed or Unreachable) over "spec 73%" muted. It sits before the owner column and scrolls with the table.
- **Lifecycle pips:** four 7x3px pills (gates passed to G4) in Ink Secondary over Strong Hairline, plus the status words; no colour meaning, so they never compete with the signal.

## Do's and Don'ts

### Do:
- **Do** pair every signal colour with its ring shape or a flag icon and label, at every size.
- **Do** keep text on the seven steps: 13, 15, 17, 20, 28, 32, 48px.
- **Do** use Clear Blue only for focus, the current view and hovered figures, as a line or text colour.
- **Do** group related figures in one 16px panel divided by 1px hairlines.
- **Do** make every figure a link to the products behind it, with Clear Blue on hover.
- **Do** keep motion to one pass (rings 900ms, bars 600ms, state changes 150 to 250ms on `cubic-bezier(0.16, 1, 0.3, 1)`) and turn it off under reduced motion.
- **Do** take colours from the tokens so print can switch the palette to light.

### Don't:
- **Don't** use the health signal colours for decoration, branding or emphasis.
- **Don't** use all-caps or letter-spaced labels.
- **Don't** use Inria Serif anywhere except the one title word.
- **Don't** cast shadows from panels; only floating previews and tooltips lift.
- **Don't** give lifecycle status a colour; it is pips and words.
- **Don't** show draft state as a watermark or a header chip; it is stated in the footer.
- **Don't** recolour or restyle the argenx wordmark, or imitate the brand icon set, "Strings" or "Infinity Loop" line graphics, which are not in this project.
- **Don't** introduce new data colours for non-data content; the overlap of Link Blue with Data Blue is an open question, not a precedent.
