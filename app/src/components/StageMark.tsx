/* The lifecycle stage mark: a quarter of the circle per stage, clockwise from 12 o'clock, on a green ramp
   (theme STAGES). Ideation is a dotted ring, Failed / retired a red double ring. */

import Ring, { QuarterPie, QuarterRing } from '@/components/Ring';
import { STAGES, stageText, type Stage } from '@/lib/theme';
import type { PlatformStage } from '@/lib/platform';

/** The ring around a map bubble. */
export function StageRing({ stage, r, width = 1 }: { stage: Stage; r: number; width?: number }) {
  const st = STAGES[stage];
  if (st.ring) return <Ring kind={st.ring} r={r} color={st.color} width={width} />;
  return <QuarterRing filled={st.quarters} r={r} color={st.color} stroke={2.4 * width} />;
}

/** Inline mark sized for text rows (default 16px). */
export default function StageMark({ stage, size = 16, title }: { stage: Stage; size?: number; title?: string }) {
  const st = STAGES[stage];
  const r = size / 2 - (st.ring === 'double' ? 3.3 : 1.2) * (size / 16);
  const svg = (
    <svg width={size} height={size} viewBox={`${-size / 2} ${-size / 2} ${size} ${size}`} role={title ? 'img' : undefined} aria-label={title} aria-hidden={title ? undefined : true} className="shrink-0" data-stage={stage}>
      {st.ring ? <Ring kind={st.ring} r={r} color={st.color} width={(size / 16) * 0.8} /> : <QuarterPie filled={st.quarters} r={r} color={st.color} />}
    </svg>
  );
  return title ? (
    <span title={title} className="inline-flex shrink-0 cursor-help align-middle">
      {svg}
    </span>
  ) : (
    svg
  );
}

export function StageLabel({ stage, className = '' }: { stage: Stage; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap text-small ${className}`}>
      <StageMark stage={stage} />
      <span style={{ color: stageText(stage) }}>{stage}</span>
    </span>
  );
}

/* The platform stage (lib/platform.ts) in the same drawing: one segment per environment of the promotion path,
   filled up to the furthest one reached. Repository only is a dotted ring, not on GitHub a thin grey one. */

export function PlatformRing({ stage, r, width = 1 }: { stage: PlatformStage; r: number; width?: number }) {
  if (stage.ring) return <Ring kind={stage.ring} r={r} color={stage.color} width={width} />;
  return <QuarterRing filled={stage.step} segments={stage.steps} r={r} color={stage.color} stroke={2.4 * width} />;
}

export function PlatformMark({ stage, size = 16, title }: { stage: PlatformStage; size?: number; title?: string }) {
  const r = size / 2 - 1.2 * (size / 16);
  return (
    <svg width={size} height={size} viewBox={`${-size / 2} ${-size / 2} ${size} ${size}`} role={title ? 'img' : undefined} aria-label={title} aria-hidden={title ? undefined : true} className="shrink-0" data-pstage={stage.key}>
      {stage.ring ? <Ring kind={stage.ring} r={r} color={stage.color} width={(size / 16) * 0.8} /> : <QuarterPie filled={stage.step} segments={stage.steps} r={r} color={stage.color} />}
    </svg>
  );
}

export function PlatformLabel({ stage, className = '' }: { stage: PlatformStage; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap text-small ${className}`}>
      <PlatformMark stage={stage} />
      <span style={{ color: stage.step < 0 ? undefined : stage.color }}>{stage.label}</span>
    </span>
  );
}
