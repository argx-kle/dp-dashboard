/* Certified (solid), forecast (same blue, faint) and the shortfall to target (red, thin) around a
   track that represents the target. A ring that is not full in solid blue is not done; a red
   segment is the gap nobody has planned for yet. The tick is what should be live by today.
   Hovering a part names it ("9 live", "13 expected by today"); the aria label says it all at once. */

import { useState, type ReactNode } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { C, SIGNALS } from '@/lib/theme';

interface Props {
  size: number;
  stroke: number;
  certified: number;
  forecast: number;
  target: number | null | undefined;
  /** What should be certified by today; drawn as a tick across the ring. */
  expected?: number | null;
  /** Late products, named with the not-planned part on hover. */
  late?: number;
  children?: ReactNode;
  label: string;
  delay?: number;
}

type Part = 'live' | 'plan' | 'gap' | 'expected';

export default function ProgressRing({ size, stroke, certified, forecast, target, expected = null, late = 0, children, label, delay = 0 }: Props) {
  const reduced = useReducedMotion();
  const [tip, setTip] = useState<{ part: Part; x: number; y: number } | null>(null);
  const r = (size - stroke) / 2 - 1;
  const total = target && target > 0 ? target : Math.max(1, certified + forecast);
  const gap = (stroke * 1.1) / (2 * Math.PI * r); // fraction of the circle left between segments
  const fc = Math.min(1, certified / total);
  const ff = Math.min(1 - fc, forecast / total);
  const fs = target && target > 0 ? Math.max(0, 1 - fc - ff) : 0;
  const seg = (f: number) => Math.max(0, f - (f > 0 ? gap : 0));
  const startAt = (f: number) => -90 + f * 360 + (f > 0 ? (gap * 360) / 2 : 0);
  const notPlanned = target && target > 0 ? Math.max(0, target - certified - forecast) : 0;
  const showTick = expected !== null && !!target && target > 0 && expected > 0 && expected < target;
  const PARTS: Record<Part, { swatch: ReactNode; text: ReactNode }> = {
    live: { swatch: <span className="h-2.5 w-2.5 rounded-full" style={{ background: C.data1 }} />, text: <><strong className="font-semibold text-ink">{certified}</strong> live</> },
    plan: { swatch: <span className="h-2.5 w-2.5 rounded-full" style={{ background: C.data2 }} />, text: <><strong className="font-semibold text-ink">{forecast}</strong> on plan by the quarter end</> },
    gap: { swatch: <span className="h-2.5 w-2.5 rounded-full" style={{ background: SIGNALS.red.color }} />, text: <><strong className="font-semibold text-ink">{notPlanned}</strong> not planned{late > 0 ? <>, <strong className="font-semibold text-ink">{late}</strong> of them late</> : null}</> },
    expected: { swatch: <span className="h-3 w-[3px] rounded-full" style={{ background: C.ink }} />, text: <><strong className="font-semibold text-ink">{expected}</strong> expected by today</> },
  };
  const fullLabel = [label, `${certified} live`, forecast ? `${forecast} on plan` : '', notPlanned ? `${notPlanned} not planned` : '', showTick ? `${expected} expected by today` : ''].filter(Boolean).join('. ');

  // Which part sits under the pointer, from its angle around the centre (12 o'clock = 0, clockwise).
  const onMove = (e: React.MouseEvent<SVGCircleElement>) => {
    const box = e.currentTarget.ownerSVGElement!.getBoundingClientRect();
    const x = e.clientX - box.left - size / 2;
    const y = e.clientY - box.top - size / 2;
    const a = ((Math.atan2(y, x) * 180) / Math.PI + 90 + 360) % 360 / 360;
    let part: Part | null = null;
    if (showTick && Math.abs(a - expected! / target!) < 0.025) part = 'expected';
    else if (a < fc) part = 'live';
    else if (a < fc + ff) part = 'plan';
    else if (a < fc + ff + fs) part = 'gap';
    setTip(part ? { part, x: x + size / 2, y: y + size / 2 } : null);
  };

  const anim = (to: number, d: number) =>
    reduced
      ? { initial: false as const, animate: { pathLength: to } }
      : { initial: { pathLength: 0 }, animate: { pathLength: to }, transition: { duration: 0.9, delay: delay + d, ease: [0.16, 1, 0.3, 1] as const } };

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`${-size / 2} ${-size / 2} ${size} ${size}`} role="img" aria-label={fullLabel}>
        <circle r={r} fill="none" stroke={C.lineStrong} strokeOpacity={0.55} strokeWidth={stroke} />
        {fc > 0 && <motion.circle r={r} fill="none" stroke={C.data1} strokeWidth={stroke} strokeLinecap="round" transform="rotate(-90)" {...anim(seg(fc), 0)} />}
        {ff > 0 && (
          <motion.circle r={r} fill="none" stroke={C.data2} strokeOpacity={0.45} strokeWidth={stroke} strokeLinecap="round" transform={`rotate(${startAt(fc)})`} {...anim(seg(ff), 0.35)} />
        )}
        {fs > 0.001 && (
          <motion.circle
            r={r}
            fill="none"
            stroke={SIGNALS.red.color}
            strokeOpacity={0.85}
            strokeWidth={Math.max(3, stroke * 0.5)}
            strokeLinecap="round"
            transform={`rotate(${startAt(fc + ff)})`}
            {...anim(seg(fs), 0.6)}
          />
        )}
        {showTick && (
          <g transform={`rotate(${(expected! / target!) * 360 - 90})`} aria-hidden="true">
            <line x1={r - stroke / 2 - 4} x2={r + stroke / 2 + 4} y1={0} y2={0} stroke={C.ink} strokeWidth={2.5} strokeLinecap="round" />
          </g>
        )}
        {/* One invisible band over the whole ring catches the pointer; its angle picks the part. */}
        <circle r={r} fill="none" stroke="transparent" strokeWidth={stroke + 12} pointerEvents="stroke" onMouseMove={onMove} onMouseLeave={() => setTip(null)} style={{ cursor: 'default' }} data-testid="ring-hit" />
      </svg>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center [&_a]:pointer-events-auto">{children}</div>
      {tip && (
        <div
          role="tooltip"
          data-testid="ring-tip"
          data-part={tip.part}
          className="pointer-events-none absolute z-30 flex items-center gap-2 whitespace-nowrap rounded-control border border-line-strong bg-panel-2 px-3 py-2 text-small text-ink-2 shadow-[0_12px_24px_-10px_rgba(0,8,12,0.7)]"
          style={{ left: tip.x + 14, top: tip.y + 14 }}
        >
          <span className="inline-flex w-2.5 shrink-0 justify-center" aria-hidden="true">
            {PARTS[tip.part].swatch}
          </span>
          <span>{PARTS[tip.part].text}</span>
        </div>
      )}
    </div>
  );
}
