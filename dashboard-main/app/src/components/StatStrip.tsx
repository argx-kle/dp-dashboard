/* The four core metrics in one ruled strip (no card grid): time to production, time to first consumer, users
   per live product and certified this quarter; and the same strip for technical readiness, one tile per platform
   source in the inbox. Every value links to its products; an incomplete input says so under the number. */

import { useCallback } from 'react';
import CountUp from '@/components/reactbits/CountUp';
import SourceLabel from '@/components/SourceLabel';
import { CoverageNote } from '@/components/Coverage';
import { useSnapshot } from '@/lib/context';
import { fmtValue, quarterLabel } from '@/lib/format';
import { href } from '@/lib/router';
import { metricDef, metricValue, reportingItem } from '@/lib/select';
import type { MetricValue } from '@/types/snapshot';

const IDS = ['cycle_time_g1_g4', 'time_to_first_consumer', 'active_users_median', 'certified_qtd'];
/** Technical readiness tiles by the coverage kind they need; a source missing from the inbox drops its tiles. */
const READINESS_BY_SOURCE: [string, string[]][] = [
  ['validation', ['spec_score_median']],
  ['nextdata', ['runtime_failing']],
  ['github', ['no_prod_deploy', 'prod_deploy_frequency', 'deploy_failure_rate']],
];
export const READINESS = READINESS_BY_SOURCE.flatMap(([, ids]) => ids);
const SOURCE_NAME: Record<string, string> = { validation: 'the validation tool', nextdata: 'NextData', github: 'GitHub' };
const TITLE: Record<string, string> = {
  cycle_time_g1_g4: 'Median time to production',
  time_to_first_consumer: 'Median time to first consumer',
  active_users_median: 'Median users per live product',
  spec_score_median: 'Median finish-spec score',
  runtime_failing: 'Failing in NextData',
  no_prod_deploy: 'Never deployed to production',
  prod_deploy_frequency: 'Production deploys per shipping product, 30 days',
  deploy_failure_rate: 'Deployment failure rate, 30 days',
};
const CAPTION: Record<string, (mv: MetricValue) => string> = {
  runtime_failing: (mv) => `of ${mv.n ?? 0} deployed`,
  no_prod_deploy: (mv) => `of ${mv.n ?? 0} with a repository`,
  deploy_failure_rate: (mv) => `of ${mv.n ?? 0} deployments`,
  certified_qtd: (mv) => (mv.target == null ? 'no target set' : `of ${mv.target} targeted`),
};
const UNIT: Record<string, string> = { days: 'days', people: 'people', share: '', count: '' };

function Stat({ id, scope }: { id: string; scope: string }) {
  const s = useSnapshot();
  const def = metricDef(s, id)!;
  const mv = metricValue(s, id, scope);
  const value = mv?.value ?? null;
  const integer = value !== null && Number.isInteger(value);
  const format = useCallback((v: number) => fmtValue(def.unit === 'share' ? v : integer ? Math.round(v) : Math.round(v * 10) / 10, def.unit), [def.unit, integer]);
  const smallN = def.minN && mv?.n !== undefined && mv.n < def.minN && (mv.values?.length ?? 0) > 0;
  return (
    <div className="flex min-w-0 flex-col gap-2 bg-panel p-6">
      <h3 className="text-small font-medium text-ink-2" title={def.definition}>{id === 'certified_qtd' ? `Certified in ${quarterLabel(s.quarter)}` : TITLE[id] ?? def.label}</h3>
      <div className="flex items-baseline gap-1.5">
        {value === null ? (
          <span className="text-figure font-semibold text-ink-3">–</span>
        ) : (
          <a href={href.products({ metric: id, scope })} className="text-figure font-semibold text-ink no-underline hover:text-clear" data-testid={`tile-link-${id}-${scope}`} data-count={mv?.urns?.length ?? 0} aria-label={`${def.label}: ${fmtValue(value, def.unit)} ${UNIT[def.unit]}. Open the ${mv?.urns?.length ?? 0} products behind it`}>
            <CountUp key={s.quarter} to={value} format={format} />
            <span className="sr-only">{fmtValue(value, def.unit)}</span>
          </a>
        )}
        {UNIT[def.unit] && value !== null && <span className="text-body text-ink-3">{UNIT[def.unit]}</span>}
      </div>
      <div className="flex min-h-5 flex-wrap items-center gap-2 text-small text-ink-3">
        {value === null ? <span>{mv?.reason}</span> : <span className="tnum">{CAPTION[id] ? CAPTION[id](mv!) : `n = ${mv?.n}`}{smallN ? ` · ${mv!.values!.map((v) => fmtValue(v, def.unit)).join(', ')}` : ''}</span>}
        <SourceLabel source={mv?.source ?? 'register'} />
      </div>
      <CoverageNote id={id} scope={scope} />
    </div>
  );
}

const XL_COLS: Record<number, string> = { 3: 'xl:grid-cols-3', 4: 'xl:grid-cols-4', 5: 'xl:grid-cols-5' };

export default function StatStrip({ scope = 'org', title = 'Speed, adoption and delivery', ids = IDS, note }: { scope?: string; title?: string; ids?: string[]; note?: string }) {
  const hid = `stats-h-${scope}-${ids[0]}`;
  return (
    <section aria-labelledby={hid} className="overflow-hidden rounded-panel border border-line bg-panel print-break-avoid" data-testid={ids === IDS ? 'stat-strip' : 'readiness-strip'}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 px-6 pt-6">
        <h2 id={hid} className="text-heading font-semibold text-ink">
          {title}
        </h2>
        {note && <p className="text-small text-ink-3">{note}</p>}
      </div>
      <div className={`mt-2 grid gap-px border-t border-line bg-line sm:grid-cols-2 ${XL_COLS[ids.length] ?? ''}`}>
        {ids.map((id) => (
          <Stat key={id} id={id} scope={scope} />
        ))}
        {/* An odd tile count leaves one slot of the two-column grid empty: fill it so no hairline colour shows. */}
        {ids.length % 2 === 1 && ids.length > 1 && <div aria-hidden="true" className="hidden bg-panel sm:block xl:hidden" />}
      </div>
    </section>
  );
}

/** Technical readiness: shown only when platform files (validation results, NextData listing, GitHub extract) are in the inbox. */
export function TechnicalReadiness({ scope = 'org' }: { scope?: string }) {
  const s = useSnapshot();
  const present = READINESS_BY_SOURCE.filter(([kind]) => reportingItem(s, kind, scope));
  if (present.length === 0) return null;
  const names = present.map(([kind]) => SOURCE_NAME[kind]);
  const note = `From ${names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}` : names[0]}.`;
  return <StatStrip scope={scope} ids={present.flatMap(([, ids]) => ids)} title="Technical readiness" note={note} />;
}
