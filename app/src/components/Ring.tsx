/* The ring drawings shared by stage marks: dotted (not started), red double (ended), and the quarter ring for
   progress, where each stage fills one more segment clockwise from 12 o'clock (quarters for the lifecycle, one
   segment per environment for the platform stage). */

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

const point = (r: number, at: number, segments = 4) => {
  const a = (at * 2 * Math.PI) / segments - Math.PI / 2;
  return `${r * Math.cos(a)} ${r * Math.sin(a)}`;
};

/** `segments` arc segments (four by default) with small gaps; the first `filled` in colour, the rest faint. */
export function QuarterRing({ filled, r, color, stroke, segments = 4 }: { filled: number; r: number; color: string; stroke: number; segments?: number }) {
  const gap = Math.min(0.12, ((stroke * 1.4) / (2 * Math.PI * r)) * segments); // in segments
  return (
    <>
      {Array.from({ length: segments }, (_, q) => (
        <path
          key={q}
          d={`M ${point(r, q + gap / 2, segments)} A ${r} ${r} 0 0 1 ${point(r, q + 1 - gap / 2, segments)}`}
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

/** A pie that fills `filled` of `segments` (four by default) of a circle, clockwise from 12 o'clock, inside a faint outline. */
export function QuarterPie({ filled, r, color, segments = 4 }: { filled: number; r: number; color: string; segments?: number }) {
  return (
    <>
      <circle r={r} fill="none" stroke={color} strokeOpacity={0.55} strokeWidth={1.2} />
      {filled >= segments ? (
        <circle r={r - 1.6} fill={color} data-quarters={filled} />
      ) : filled > 0 ? (
        <path d={`M 0 0 L ${point(r - 1.6, 0, segments)} A ${r - 1.6} ${r - 1.6} 0 ${filled / segments > 0.5 ? 1 : 0} 1 ${point(r - 1.6, filled, segments)} Z`} fill={color} data-quarters={filled} />
      ) : null}
    </>
  );
}
