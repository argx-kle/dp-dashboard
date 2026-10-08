/* First row of the executive overview. Left: the quarter in one sentence, led by its health. Right: the status
   board, every domain as a tiny certified/target pill in the column of its health, most urgent first.
   Health is the pipeline's forecast (HealthItem): certified against the pace expected by today for the current
   quarter, the result against the target for a closed one. */

import ProgressRing from '@/components/ProgressRing';
import QuarterBar from '@/components/QuarterBar';
import { HealthMark } from '@/components/HealthBadge';
import CountUp from '@/components/reactbits/CountUp';
import { useSnapshot } from '@/lib/context';
import { fmtValue, plural, quarterEnd, quarterLabel } from '@/lib/format';
import { healthOf, useQuarter } from '@/lib/quarter';
import { href } from '@/lib/router';
import { domainName, domainsNotOnTrack, inPlay } from '@/lib/select';
import { HEALTH, HEALTH_COLUMNS, type Health } from '@/lib/theme';
import type { HealthItem, Snapshot } from '@/types/snapshot';

const dp = (n: number) => plural(n, 'data product');
const num = (n: number | null | undefined) => fmtValue(n ?? 0, 'count');
const isResult = (h: HealthItem) => h.status.endsWith('target') && h.status !== 'no-target';

/** "1/3"; "1" without a target. */
export function ofTarget(h: Pick<HealthItem, 'certified' | 'target'> | undefined): string {
  if (!h) return '–';
  return h.target === null ? String(h.certified) : `${h.certified}/${h.target}`;
}

/** The quarter, one fact per line: what is live, what was expected by today, the target. */
export function headline(h: HealthItem, quarter: string): { lead: string; expected: string | null; target: string } {
  if (h.target === null) return { lead: `${dp(h.certified)} live this quarter.`, expected: null, target: 'No quarter target.' };
  if (isResult(h)) return { lead: `${h.certified} of ${dp(h.target)} went live in ${quarterLabel(quarter)}.`, expected: null, target: `Quarter target: ${h.target}.` };
  return { lead: `${dp(h.certified)} live.`, expected: `${num(h.expected)} expected by today.`, target: `Quarter target: ${h.target} by ${quarterEnd(quarter)}.` };
}

/** One line for tooltips and the domain page: "At risk: 2 live, 2.8 expected by now, target 5." */
export function verdict(h: HealthItem, _closed?: boolean, quarter?: string): string {
  const label = HEALTH[h.status as Health].label;
  if (h.target === null) return `${h.certified} live. No target.`;
  if (isResult(h)) return `${label}: ${h.certified} of ${h.target} live${quarter ? ` in ${quarterLabel(quarter)}` : ''}.`;
  return `${label}: ${h.certified} live, ${num(h.expected)} expected by today, target ${h.target}.`;
}

export function DomainRing({ id, size = 96, delay = 0 }: { id: string; size?: number; delay?: number }) {
  const s = useSnapshot();
  const h = healthOf(s, id);
  const c = h?.certified ?? 0;
  const f = h?.forecast ?? 0;
  const t = h?.target ?? null;
  return (
    <ProgressRing size={size} stroke={Math.round(size / 10)} certified={c} forecast={f} target={t} expected={h && !isResult(h) ? h.expected : null} delay={delay} label={h ? verdict(h) : domainName(s, id)}>
      <span className="text-heading font-semibold leading-none text-ink">{c}</span>
      <span className="mt-1 text-small text-ink-3">of {t ?? '—'}</span>
    </ProgressRing>
  );
}

function names(s: Snapshot, ids: string[]) {
  return ids.map((id, i) => (
    <span key={id}>
      {i > 0 && (i === ids.length - 1 ? ' and ' : ', ')}
      <a href={href.domain(id)} className="whitespace-nowrap">
        {domainName(s, id)}
      </a>
    </span>
  ));
}

/** The status board: one column per health, each domain a pill with certified/target. */
function StatusBoard({ closed }: { closed: boolean }) {
  const s = useSnapshot();
  const domains = s.domains.filter(inPlay(s));
  const columns = HEALTH_COLUMNS[closed ? 'closed' : 'open'];
  const noTarget = domains.filter((d) => healthOf(s, d.id)?.status === 'no-target' && s.products.some((p) => p.domain === d.id));
  return (
    <div data-testid="status-board">
      <div className={`grid grid-cols-1 gap-x-3 gap-y-5 sm:grid-cols-2 ${closed ? 'xl:grid-cols-3' : 'xl:grid-cols-4'}`}>
        {columns.map((status, ci) => {
          const h = HEALTH[status];
          const items = domains.filter((d) => healthOf(s, d.id)?.status === status);
          return (
            <section key={status} aria-label={`${h.label}: ${items.length}`} data-testid={`board-${status}`}>
              <h3 className="flex items-center gap-2 border-b pb-2 text-small font-semibold" style={{ color: `color-mix(in srgb, ${h.color} 55%, #f2fafc)`, borderColor: `color-mix(in srgb, ${h.color} 40%, transparent)` }}>
                <HealthMark status={status} size={16} />
                {h.label}
                <span className="ml-auto font-normal text-ink-3 tnum">{items.length}</span>
              </h3>
              <div className={`mt-1.5 flex h-4 justify-end pr-3 text-[11px] leading-4 text-ink-3 ${ci === 0 ? '' : 'invisible max-sm:hidden'}`} aria-hidden="true">
                live / target
              </div>
              <ul className="m-0 mt-1 flex list-none flex-col gap-1.5 p-0">
                {items.length === 0 && <li className="px-1 text-small text-ink-3">None</li>}
                {items.map((d) => {
                  const dh = healthOf(s, d.id)!;
                  const t = dh.target ?? 0;
                  const done = t > 0 ? Math.min(1, dh.certified / t) : dh.certified > 0 ? 1 : 0;
                  return (
                    <li key={d.id}>
                      <a
                        href={href.domain(d.id)}
                        title={`${d.name}: ${dh.certified} of ${t} live`}
                        aria-label={`${d.name}: ${dh.certified} of ${t} live. ${HEALTH[status].label}`}
                        className="relative flex h-8 items-center justify-between gap-2 overflow-hidden rounded-full border px-3 text-small no-underline transition-[filter] duration-150 hover:brightness-125"
                        style={{ borderColor: `color-mix(in srgb, ${h.color} 40%, transparent)`, background: `color-mix(in srgb, ${h.color} 6%, transparent)` }}
                        data-testid={`domain-health-${d.id}`}
                        data-health={status}
                        data-done={done.toFixed(2)}
                      >
                        <span className="absolute inset-y-0 left-0" style={{ width: `${done * 100}%`, background: `color-mix(in srgb, ${h.color} ${dh.certified > t ? 38 : 28}%, transparent)` }} aria-hidden="true" data-testid="pill-fill" />
                        <span className="relative truncate font-medium text-ink">{d.name}</span>
                        <span className="relative shrink-0 tnum">
                          <span className="font-semibold text-ink">{dh.certified}</span>
                          <span className="text-ink-2">/{t}</span>
                        </span>
                      </a>
                    </li>
                  );
                })}
              </ul>
            </section>
          );
        })}
      </div>
      {noTarget.length > 0 && (
        <p className="mt-4 text-small text-ink-3" data-testid="no-target">
          No target: {names(s, noTarget.map((d) => d.id))}
        </p>
      )}
    </div>
  );
}

export default function QuarterSummary() {
  const s = useSnapshot();
  const closed = useQuarter()?.closed ?? false;
  const org = healthOf(s, 'org');
  const certified = org?.certified ?? 0;
  const forecast = org?.forecast ?? 0;
  const late = org?.late ?? 0;
  const target = org?.target ?? null;
  const behind = domainsNotOnTrack(s).map((d) => d.id);
  const certUrns = s.metrics.find((m) => m.id === 'certified_qtd' && m.scope === 'org')?.urns?.length ?? 0;
  const lines = org ? headline(org, s.quarter) : null;
  const color = org ? HEALTH[org.status as Health].color : undefined;

  return (
    <section aria-label={`${quarterLabel(s.quarter)} summary`} className="overflow-hidden rounded-panel border border-line bg-panel print-break-avoid">
      <div className="border-b border-line px-6 py-5">
        <QuarterBar />
      </div>
      <div className="grid grid-cols-1 gap-px bg-line lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <div className="flex flex-col items-start gap-6 bg-panel p-6 sm:flex-row sm:items-center sm:gap-8">
        <ProgressRing size={168} stroke={15} certified={certified} forecast={forecast} target={target} expected={closed ? null : org?.expected ?? null} late={closed ? 0 : late} label={org ? verdict(org, closed, s.quarter) : quarterLabel(s.quarter)}>
          <a href={href.products({ metric: 'certified_qtd', scope: 'org' })} className="text-display font-bold leading-none text-ink no-underline hover:text-clear" data-testid="tile-link-certified_qtd-org" data-count={certUrns} aria-label={`${certified} data products live this quarter. Open them`}>
            <CountUp key={s.quarter} to={certified} />
            <span className="sr-only">{certified}</span>
          </a>
          <span className="mt-1.5 text-small text-ink-3">of {target ?? '—'} data products</span>
        </ProgressRing>
        <div className="min-w-0">
          {org && (
            <p className="text-heading leading-snug text-pretty text-ink" data-testid="quarter-verdict" data-health={org.status}>
              <strong className="font-semibold" style={{ color: `color-mix(in srgb, ${color} 75%, #f2fafc)` }}>
                {HEALTH[org.status as Health].label}.
              </strong>{' '}
              {lines?.lead}
            </p>
          )}
          {lines?.expected && (
            <p className="mt-1 text-lead text-ink" data-testid="quarter-expected">
              {lines.expected}
            </p>
          )}
          {lines && (
            <p className="mt-1 text-lead text-ink-2" data-testid="quarter-target">
              {lines.target}
            </p>
          )}
          {behind.length > 0 && (
            <p className="mt-2 text-body text-pretty text-ink-2">
              {names(s, behind)} {behind.length === 1 ? 'is' : 'are'} {closed ? 'below target' : 'behind'}.
            </p>
          )}
        </div>
      </div>
      <div className="bg-panel p-6">
        <h2 className="sr-only">By domain</h2>
        <StatusBoard closed={closed} />
      </div>
      </div>
    </section>
  );
}
