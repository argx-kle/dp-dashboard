/* The ring drawings shared by stage marks: dotted (not started), red double (ended), and the quarter ring for
   progress, where each stage fills one more quarter clockwise from 12 o'clock. */

import type { RingKind } from '@/lib/theme';

export default function Ring({ kind, r, color, width = 1 }: { kind: RingKind; r: number; color: string; width?: number }) {
  switch (kind) {
    case 'double':
      return (
        <>
          <circle r={r} fill="none" stroke={color} strokeWidth={2.4 * width} />
          <circle r={r + 3.4 * width} fill="none" stroke={color} strokeWidth={1.1 * width} opacity={0.85} />
        </>
      );
    case 'dotted':
      return <circle r={r} fill="none" stroke={color} strokeWidth={1.8 * width} strokeDasharray={`0.1 ${3.4 * width}`} strokeLinecap="round" />;
    case 'thin':
      return <circle r={r} fill="none" stroke={color} strokeWidth={1.1 * width} />;
    default:
      return <circle r={r} fill="none" stroke={color} strokeWidth={2.2 * width} />;
  }
}

const point = (r: number, quarter: number) => {
  const a = (quarter * Math.PI) / 2 - Math.PI / 2;
  return `${r * Math.cos(a)} ${r * Math.sin(a)}`;
};

/** Four arc segments with small gaps; the first `filled` in colour, the rest faint. */
export function QuarterRing({ filled, r, color, stroke }: { filled: number; r: number; color: string; stroke: number }) {
  const gap = Math.min(0.12, (stroke * 1.4) / (2 * Math.PI * r) * 4); // in quarters
  return (
    <>
      {[0, 1, 2, 3].map((q) => (
        <path
          key={q}
          d={`M ${point(r, q + gap / 2)} A ${r} ${r} 0 0 1 ${point(r, q + 1 - gap / 2)}`}
          fill="none"
          stroke={color}
          strokeOpacity={q < filled ? 1 : 0.22}
          strokeWidth={stroke}
          strokeLinecap="round"
          data-filled={q < filled ? 'true' : undefined}
        />
      ))}
    </>
  );
}

/** A pie that fills `filled` quarters of a circle, clockwise from 12 o'clock, inside a faint outline. */
export function QuarterPie({ filled, r, color }: { filled: number; r: number; color: string }) {
  return (
    <>
      <circle r={r} fill="none" stroke={color} strokeOpacity={0.55} strokeWidth={1.2} />
      {filled >= 4 ? (
        <circle r={r - 1.6} fill={color} data-quarters={4} />
      ) : filled > 0 ? (
        <path d={`M 0 0 L ${point(r - 1.6, 0)} A ${r - 1.6} ${r - 1.6} 0 ${filled > 2 ? 1 : 0} 1 ${point(r - 1.6, filled)} Z`} fill={color} data-quarters={filled} />
      ) : null}
    </>
  );
}
