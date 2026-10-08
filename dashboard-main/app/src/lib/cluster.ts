/* Deterministic circle packing for the cluster map. No dependency, no randomness:
   the same snapshot always draws the same picture.

   packCircles: gravity toward the origin + pairwise collision resolution, seeded on a
   sunflower spiral so the result is compact and organic. */

export interface Circle {
  key: string;
  r: number;
  x: number;
  y: number;
}

const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

export function packCircles(input: { key: string; r: number }[], gap: number, iterations = 320): { circles: Circle[]; R: number } {
  if (input.length === 0) return { circles: [], R: 0 };
  if (input.length === 1) return { circles: [{ ...input[0], x: 0, y: 0 }], R: input[0].r };
  const mean = input.reduce((a, c) => a + c.r, 0) / input.length;
  const circles: Circle[] = input.map((c, i) => {
    const d = (mean + gap) * 1.1 * Math.sqrt(i + 0.5);
    const a = i * GOLDEN_ANGLE;
    return { ...c, x: d * Math.cos(a), y: d * Math.sin(a) };
  });
  for (let it = 0; it < iterations; it++) {
    const pull = 0.06 * (1 - it / iterations);
    for (const c of circles) {
      c.x -= c.x * pull;
      c.y -= c.y * pull;
    }
    for (let pass = 0; pass < 2; pass++) {
      for (let i = 0; i < circles.length; i++) {
        for (let j = i + 1; j < circles.length; j++) {
          const a = circles[i];
          const b = circles[j];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          let dist = Math.hypot(dx, dy);
          const min = a.r + b.r + gap;
          if (dist >= min) continue;
          if (dist < 1e-6) {
            dx = Math.cos(i + j);
            dy = Math.sin(i + j);
            dist = 1;
          }
          const push = (min - dist) / 2;
          const ux = dx / dist;
          const uy = dy / dist;
          // Larger circles move less.
          const wa = b.r / (a.r + b.r);
          const wb = a.r / (a.r + b.r);
          a.x -= ux * push * 2 * wa;
          a.y -= uy * push * 2 * wa;
          b.x += ux * push * 2 * wb;
          b.y += uy * push * 2 * wb;
        }
      }
    }
  }
  return recentre(circles);
}

/** Centre on the bounding box and return the enclosing radius. */
function recentre(circles: Circle[]): { circles: Circle[]; R: number } {
  const minX = Math.min(...circles.map((c) => c.x - c.r));
  const maxX = Math.max(...circles.map((c) => c.x + c.r));
  const minY = Math.min(...circles.map((c) => c.y - c.r));
  const maxY = Math.max(...circles.map((c) => c.y + c.r));
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  for (const c of circles) {
    c.x -= cx;
    c.y -= cy;
  }
  const R = Math.max(...circles.map((c) => Math.hypot(c.x, c.y) + c.r));
  return { circles, R };
}

export interface GroupInput {
  id: string;
  items: { key: string }[];
  /** Width the group's label needs, so long names never collide with a neighbour. */
  minWidth?: number;
}

export interface PlacedGroup {
  id: string;
  cx: number;
  cy: number;
  R: number;
  /** Top edge of this group's drawn outline. Outlines in a row share it, so labels placed just above
      it sit at the same distance from every cluster and on one baseline. */
  hullTop: number;
  bubbles: { key: string; x: number; y: number }[]; // absolute coordinates
}

export interface Layout {
  groups: PlacedGroup[];
  width: number;
  height: number;
  bubbleR: number;
  rowTops: number[];
}

/** Pack every group, then flow the groups left to right, wrapping into rows wider than rowWidth.
    Spacing and alignment use each cluster's drawn outline (bubbles plus halo), not its enclosing
    circle: outlines in a row are top-aligned, so every label hugs its own cluster. */
export function layoutGroups(
  groups: GroupInput[],
  opts: { bubbleR: number; gap: number; groupPad: number; groupGap: number; labelTop: number; labelBottom: number; minR?: number; rowWidth?: number; rowGap?: number },
): Layout {
  const { bubbleR, gap, groupPad, groupGap, labelTop, labelBottom, minR = bubbleR * 2.2, rowWidth = Infinity, rowGap = 12 } = opts;
  const packed = groups.map((g) => {
    const res = packCircles(g.items.map((i) => ({ key: i.key, r: bubbleR })), gap);
    const bubbles = res.circles.map((c) => ({ key: c.key, x: c.x, y: c.y }));
    const R = Math.max(minR, res.R + groupPad);
    const reach = bubbleR + groupPad;
    // A group with no products still gets a slot the size of the smallest cluster, so its label has
    // a place of its own (Math.min of nothing is Infinity, which would put every empty label at NaN).
    const ext = bubbles.length
      ? {
          left: Math.min(...bubbles.map((b) => b.x)) - reach,
          right: Math.max(...bubbles.map((b) => b.x)) + reach,
          top: Math.min(...bubbles.map((b) => b.y)) - reach,
          bottom: Math.max(...bubbles.map((b) => b.y)) + reach,
        }
      : { left: -minR, right: minR, top: -minR, bottom: minR };
    const slot = Math.max(ext.right - ext.left, g.minWidth ?? 0);
    return { id: g.id, R, bubbles, ext, slot };
  });

  // Flow into rows.
  const rows: (typeof packed)[] = [];
  let row: typeof packed = [];
  let rowW = 0;
  for (const p of packed) {
    if (row.length && rowW + groupGap + p.slot > rowWidth) {
      rows.push(row);
      row = [];
      rowW = 0;
    }
    rowW += (row.length ? groupGap : 0) + p.slot;
    row.push(p);
  }
  if (row.length) rows.push(row);

  const rowWidths = rows.map((r) => r.reduce((a, p, i) => a + p.slot + (i ? groupGap : 0), 0));
  const width = Math.max(0, ...rowWidths);
  const placed: PlacedGroup[] = [];
  const rowTops: number[] = [];
  let top = 0;
  rows.forEach((r, ri) => {
    rowTops.push(top);
    const hullTop = top + labelTop;
    const tallest = Math.max(...r.map((p) => p.ext.bottom - p.ext.top));
    let x = (width - rowWidths[ri]) / 2;
    for (const p of r) {
      // Centre the outline in its slot horizontally; put its top edge on the row's hull line.
      const cx = x + p.slot / 2 - (p.ext.left + p.ext.right) / 2;
      const cy = hullTop - p.ext.top;
      x += p.slot + groupGap;
      placed.push({ id: p.id, cx, cy, R: p.R, hullTop, bubbles: p.bubbles.map((b) => ({ key: b.key, x: cx + b.x, y: cy + b.y })) });
    }
    top += labelTop + tallest + labelBottom + (ri < rows.length - 1 ? rowGap : 0);
  });
  return { groups: placed, width, height: top, bubbleR, rowTops };
}

/* Fitting a product name inside its bubble: the largest type size (12 px down to 8 px) at which the name wraps
   into at most three lines, each within the circle's chord at that line's height. Widths are estimated per
   character class for Instrument Sans semibold, so layout stays deterministic and needs no DOM measurement. */

const charWidth = (ch: string) => (ch === ' ' ? 0.27 : /[A-Z]/.test(ch) ? 0.66 : /[0-9]/.test(ch) ? 0.56 : /[il.,'|!]/.test(ch) ? 0.26 : /[mw]/.test(ch) ? 0.8 : 0.53);
export const textWidth = (s: string, size: number) => [...s].reduce((a, ch) => a + charWidth(ch), 0) * size;

function wrapInto(input: string[], widths: number[], size: number, hyphenate = false): string[] | null {
  const words = [...input];
  const lines: string[] = [];
  let i = 0;
  for (const w of widths) {
    if (i >= words.length) break;
    let line = words[i];
    if (textWidth(line, size) > w) {
      // A long word may break once, with a hyphen, leaving at least four letters on each side.
      if (!hyphenate || line.length < 9) return null;
      let cut = line.length - 4;
      while (cut >= 4 && textWidth(`${line.slice(0, cut)}-`, size) > w) cut--;
      if (cut < 4) return null;
      words.splice(i, 1, `${line.slice(0, cut)}-`, line.slice(cut));
      line = words[i];
    }
    i++;
    while (!line.endsWith('-') && i < words.length && textWidth(`${line} ${words[i]}`, size) <= w) line = `${line} ${words[i++]}`;
    lines.push(line);
  }
  return i >= words.length ? lines : null;
}

export function fitName(name: string, inner: number): { lines: string[]; size: number } {
  const words = name.trim().split(/\s+/);
  const chords = (n: number, size: number) =>
    Array.from({ length: n }, (_, i) => {
      const lh = size * 1.14;
      const y = Math.abs((i - (n - 1) / 2) * lh) + size * 0.42;
      return y >= inner ? 0 : 2 * Math.sqrt(inner * inner - y * y) - 2;
    });
  for (const hyphenate of [false, true]) {
    for (let size = 12; size >= (hyphenate ? 8 : 9); size -= 0.5) {
      for (let n = 1; n <= 3; n++) {
        const lines = wrapInto(words, chords(n, size), size, hyphenate);
        if (lines) return { lines, size };
      }
    }
  }
  // Too long even at 8 px: three lines, the last one cut with an ellipsis (the preview shows the full name).
  const size = 8;
  const widths = chords(3, size);
  const lines: string[] = [];
  let rest = name.trim();
  for (let i = 0; i < 3 && rest; i++) {
    let cut = rest.length;
    while (cut > 1 && textWidth(rest.slice(0, cut) + (i === 2 && cut < rest.length ? '…' : ''), size) > widths[i]) cut--;
    const space = rest.lastIndexOf(' ', cut);
    const at = i < 2 && cut < rest.length && space > 0 ? space : cut;
    lines.push(rest.slice(0, at).trim() + (i === 2 && at < rest.length ? '…' : ''));
    rest = rest.slice(at).trim();
  }
  return { lines, size };
}
