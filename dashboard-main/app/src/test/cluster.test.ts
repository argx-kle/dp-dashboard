import { describe, expect, it } from 'vitest';
import { layoutGroups, packCircles } from '@/lib/cluster';

describe('packCircles', () => {
  it('never overlaps and is deterministic', () => {
    const input = Array.from({ length: 30 }, (_, i) => ({ key: `k${i}`, r: 16 }));
    const a = packCircles(input, 6);
    const b = packCircles(input, 6);
    expect(a).toEqual(b);
    for (let i = 0; i < a.circles.length; i++)
      for (let j = i + 1; j < a.circles.length; j++) {
        const d = Math.hypot(a.circles[i].x - a.circles[j].x, a.circles[i].y - a.circles[j].y);
        expect(d).toBeGreaterThan(32 + 6 - 0.6);
      }
    for (const c of a.circles) expect(Math.hypot(c.x, c.y) + c.r).toBeLessThanOrEqual(a.R + 1e-6);
  });
});

describe('layoutGroups', () => {
  it('lays groups left to right without overlap', () => {
    const items = (n: number) => Array.from({ length: n }, (_, i) => ({ key: `${n}-${i}` }));
    const l = layoutGroups(
      [
        { id: 'a', items: items(12) },
        { id: 'b', items: items(4) },
      ],
      { bubbleR: 16, gap: 6, groupPad: 12, groupGap: 30, labelTop: 50, labelBottom: 10 },
    );
    const [a, b] = l.groups;
    const reachA = 16 + 12; // bubble radius + halo
    const rightA = Math.max(...a.bubbles.map((p) => p.x)) + reachA;
    const leftB = Math.min(...b.bubbles.map((p) => p.x)) - reachA;
    expect(rightA + 30).toBeLessThanOrEqual(leftB + 1e-6);
    expect(a.bubbles).toHaveLength(12);
    // Outlines in a row share their top edge.
    const topOf = (g: typeof a) => Math.min(...g.bubbles.map((p) => p.y)) - 16 - 12;
    expect(Math.abs(topOf(a) - a.hullTop)).toBeLessThan(1e-6);
    expect(Math.abs(topOf(b) - b.hullTop)).toBeLessThan(1e-6);
    expect(l.width).toBeGreaterThan(0);
  });

  it('gives every empty group its own place, so empty domains never stack their labels', () => {
    const l = layoutGroups(
      [
        { id: 'full', items: Array.from({ length: 30 }, (_, i) => ({ key: `k${i}` })) },
        { id: 'e1', items: [] },
        { id: 'e2', items: [] },
        { id: 'e3', items: [] },
      ],
      { bubbleR: 16, gap: 6, groupPad: 12, groupGap: 30, labelTop: 50, labelBottom: 10 },
    );
    for (const g of l.groups) expect(Number.isFinite(g.cx) && Number.isFinite(g.cy)).toBe(true);
    const xs = l.groups.map((g) => g.cx);
    expect(new Set(xs).size).toBe(4);
    expect(Number.isFinite(l.width) && Number.isFinite(l.height)).toBe(true);
  });
});
