/* Hover/focus preview on the cluster map: the picture's caption, not a report. Name, where it
   lives, its lifecycle stage, the one reason, and at most three figures. Empty figures hide. While the register
   has no gate dates: its platform stage, what is failing now, and the delivery figures. */

import { useLayoutEffect, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { useSnapshot } from '@/lib/context';
import { fmtShort, humanize } from '@/lib/format';
import { domainName, flagDef } from '@/lib/select';
import { gateLabel } from '@/lib/theme';
import { PlatformLabel, StageLabel } from '@/components/StageMark';
import { failingReasons, hasGates, platformStage } from '@/lib/platform';
import type { ProductRow } from '@/types/snapshot';

interface Props {
  product: ProductRow;
  left: string;
  top: string;
  width: number;
}

function Fact({ label, value, note }: { label: string; value: React.ReactNode; note?: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1">
      <dt className="shrink-0 text-small text-ink-3">{label}</dt>
      <dd className="m-0 min-w-0 text-right text-body font-semibold text-ink">
        {value}
        {note && <span className="block text-small font-semibold text-sig-red">{note}</span>}
      </dd>
    </div>
  );
}

export default function ProductPreview({ product: p, left, top, width }: Props) {
  const s = useSnapshot();
  const reduced = useReducedMotion();
  const year = Number(s.asOfDate.slice(0, 4));
  const next = p.nextGate;
  const first = p.flags[0];
  const ref = useRef<HTMLDivElement>(null);
  const [shift, setShift] = useState(0);

  // Centre on the bubble, then nudge so the whole card stays inside the visible viewport
  // (below the sticky header, above the bottom edge).
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const head = document.querySelector('header')?.getBoundingClientRect().bottom ?? 0;
    const minTop = head + 12;
    const maxBottom = window.innerHeight - 12;
    let d = 0;
    if (r.bottom > maxBottom) d = maxBottom - r.bottom;
    if (r.top + d < minTop) d = minTop - r.top;
    setShift(d);
  }, [p.urn, top, left]);

  return (
    <motion.div
      ref={ref}
      role="tooltip"
      data-testid="product-preview"
      initial={reduced ? false : { opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reduced ? undefined : { opacity: 0, transition: { duration: 0.1 } }}
      transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
      className="pointer-events-none absolute z-30 rounded-panel border border-line-strong bg-panel-2 p-5 shadow-[0_24px_48px_-16px_rgba(0,8,12,0.75)]"
      style={{ left, top, width, translate: `0 calc(-50% + ${shift}px)` }}
    >
      <div className="text-lead font-semibold leading-snug text-ink">{p.name}</div>
      <div className="mt-0.5 text-small text-ink-3">
        {domainName(s, p.domain)}
      </div>
      {!hasGates(s) ? (
        <PlatformFacts product={p} year={year} />
      ) : (
        <>
      {first && (
        <p className="mt-2.5 text-small text-pretty text-ink-2">
          <span className="font-semibold text-ink">{flagDef(s, first.code)?.label}</span>
          {': '}
          {humanize(first.reason, year)}
          {p.flags.length > 1 && <span className="text-ink-3"> (+{p.flags.length - 1} more)</span>}
        </p>
      )}
      <dl className="mt-3 border-t border-line pt-2">
        <Fact label="Stage" value={<StageLabel stage={p.lifecycle} className="text-body font-semibold text-ink" />} />
        {next && <Fact label="Next gate" value={`${gateLabel(next.gate)} · ${fmtShort(next.plannedDate, year)}`} note={next.overdueDays > 0 ? `${next.overdueDays} days late` : undefined} />}
        <Fact label="Days in stage" value={p.daysInStage} />
        <Fact label="Owner" value={p.dpo ?? 'No DPO'} />
      </dl>
        </>
      )}
    </motion.div>
  );
}

function PlatformFacts({ product: p, year }: { product: ProductRow; year: number }) {
  const s = useSnapshot();
  const failing = failingReasons(s, p);
  const g = p.github;
  return (
    <>
      {failing.length > 0 && (
        <p className="mt-2.5 text-small text-pretty text-ink-2">
          <span className="font-semibold text-ink">Failing now:</span> {failing.join(', ')}
        </p>
      )}
      <dl className="mt-3 border-t border-line pt-2">
        <Fact label="Platform stage" value={<PlatformLabel stage={platformStage(s, p)} className="text-body font-semibold text-ink" />} />
        {g && <Fact label="Last production deploy" value={g.lastProdDeploy ? fmtShort(g.lastProdDeploy, year) : 'Never'} />}
        {g && <Fact label="Deploys, 30 days" value={g.deploys30d ? `${g.deploys30d}, ${Math.round((g.failed30d / g.deploys30d) * 100)}% failed` : 'None'} />}
        {p.nextdata && <Fact label="NextData" value={`${p.nextdata.runtime}${p.nextdata.env && p.nextdata.runtime === 'Started' ? ` · ${p.nextdata.env}` : ''}`} />}
        {p.validation?.score != null && <Fact label="Spec score" value={`${Math.round(p.validation.score * 100)}%`} />}
      </dl>
    </>
  );
}
