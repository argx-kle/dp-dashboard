/* #/delivery  Every data product repository in the GitHub extract and how it deploys, whether or not it is in
   the register (snapshot.delivery): the headline numbers, the promotion path dev → validation → production,
   twelve weeks of deployments, teams, and every repository. #/delivery?env=iac-apply-p lists the repositories
   that reached that environment; ?all=1 adds the tooling, template and test repositories that are not counted. */

import { useMemo, useState } from 'react';
import { ArrowUpRightIcon } from '@/components/Icons';
import SourceLabel from '@/components/SourceLabel';
import ScrollTable from '@/components/ScrollTable';
import { useSnapshot } from '@/lib/context';
import { fmtDateTimeZone, fmtShort, fmtValue, plural } from '@/lib/format';
import { href } from '@/lib/router';
import { C, SIGNALS } from '@/lib/theme';
import { useWidth } from '@/lib/useWidth';
import type { Delivery, DeliveryRepo, DeliveryWeek } from '@/types/snapshot';

/* Succeeded and failed fill the bars (validated pair on the panel surface); production successes are a
   labelled marker above the bar, never a third fill. */
const OK = C.data2;
const FAILED = SIGNALS.red.color;
const PROD = SIGNALS.green.color;
const DAY = 86_400_000;

const pct = (n: number, of: number) => (of ? fmtValue(n / of, 'share') : '–');
const daysBetween = (from: string, to: string) => Math.round((Date.parse(to) - Date.parse(from)) / DAY);
const prodEnv = (d: Delivery) => d.envs.find((e) => e.prod)?.id;

function Tile({ title, value, caption, link, testId }: { title: string; value: string; caption: string; link?: string; testId: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-2 bg-panel p-6" data-testid={testId}>
      <h3 className="text-small font-medium text-ink-2">{title}</h3>
      {link ? (
        <a href={link} className="text-figure font-semibold text-ink no-underline hover:text-clear tnum">{value}</a>
      ) : (
        <span className="text-figure font-semibold text-ink tnum">{value}</span>
      )}
      <span className="text-small text-ink-3 tnum">{caption}</span>
    </div>
  );
}

function Headline({ d }: { d: Delivery }) {
  const t = d.totals;
  const prod = prodEnv(d);
  return (
    <div className="grid gap-px border-t border-line bg-line sm:grid-cols-2 xl:grid-cols-5">
      <Tile testId="del-reached-prod" title="Reached production" value={String(t.reachedProd)} caption={`of ${t.repos} repositories, ever`} link={prod ? href.delivery({ env: prod }) : undefined} />
      <Tile
        testId="del-last-prod"
        title="Last production deploy"
        value={t.lastProdDeploy ? fmtShort(t.lastProdDeploy) : 'Never'}
        caption={t.lastProdDeploy ? `${daysBetween(t.lastProdDeploy, d.fetchedAt.slice(0, 10))} days before the extract of ${fmtShort(d.fetchedAt)} · ${t.lastProdRepo}` : 'No repository has deployed to production'}
      />
      <Tile testId="del-deploys" title={`Deployments, ${d.windowDays} days`} value={fmtValue(t.deploys30d, 'count')} caption={`${t.active30d} of ${t.repos} repositories deployed`} />
      <Tile testId="del-failure-rate" title={`Failure rate, ${d.windowDays} days`} value={pct(t.failed30d, t.deploys30d)} caption={`${fmtValue(t.failed30d, 'count')} of ${fmtValue(t.deploys30d, 'count')} failed`} />
      <Tile testId="del-prod-attempts" title={`Production attempts, ${d.windowDays} days`} value={String(t.prodAttempts30d)} caption={`${t.prodFailed30d} failed, ${t.prodAttempts30d - t.prodFailed30d} succeeded`} />
    </div>
  );
}

/* Promotion path: repositories with at least one successful deployment in each environment. */
function Funnel({ d }: { d: Delivery }) {
  const path = d.envs.filter((e) => e.path);
  return (
    <div className="border-t border-line px-6 py-5" data-testid="del-funnel">
      <h3 className="text-small font-medium text-ink-2">Promotion path: repositories with a successful deployment</h3>
      <ol className="m-0 mt-3 list-none space-y-2 p-0">
        {path.map((e) => (
          <li key={e.id}>
            <a href={href.delivery({ env: e.id })} className="group grid grid-cols-[96px_minmax(0,1fr)_88px] items-center gap-3 text-body no-underline" data-testid={`del-funnel-${e.id}`} data-count={e.repos}>
              <span className="text-ink-2 group-hover:text-ink">{e.label}</span>
              <span className="h-3 rounded-[4px] bg-track">
                <span className="block h-3 rounded-[4px]" style={{ width: `${d.totals.repos ? (e.repos / d.totals.repos) * 100 : 0}%`, minWidth: e.repos ? 4 : 0, background: e.prod ? PROD : OK }} />
              </span>
              <span className="text-right text-ink tnum">
                <span className="font-semibold">{e.repos}</span> <span className="text-small text-ink-3">of {d.totals.repos}</span>
              </span>
            </a>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** The headline numbers and the promotion path; the executive overview shows it too. */
export function DeliverySummary({ link = false }: { link?: boolean }) {
  const s = useSnapshot();
  const d = s.delivery;
  if (!d) return null;
  return (
    <section aria-labelledby="delivery-h" className="overflow-hidden rounded-panel border border-line bg-panel print-break-avoid" data-testid="delivery-summary">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 px-6 pt-6 pb-4">
        <h2 id="delivery-h" className="flex items-center gap-2 text-heading font-semibold text-ink">
          Delivery <SourceLabel source="github" />
        </h2>
        <p className="text-small text-ink-3">
          {d.totals.repos} data product repositories in {d.org ?? 'GitHub'}, {d.totals.notInRegister} not in the register · fetched {fmtDateTimeZone(d.fetchedAt)}
          {link && (
            <>
              {' · '}
              <a href={href.delivery()} data-testid="delivery-open">Every repository</a>
            </>
          )}
        </p>
      </div>
      <Headline d={d} />
      <Funnel d={d} />
    </section>
  );
}

/* Deployments per week, stacked succeeded / failed, production successes marked above the bar. */
function WeeklyChart({ weeks }: { weeks: DeliveryWeek[] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const H = 220;
  const PAD = { top: 28, right: 8, bottom: 32, left: 40 };
  const max = Math.max(1, ...weeks.map((w) => w.deploys));
  const step = Math.pow(10, Math.floor(Math.log10(max)));
  const top = Math.ceil(max / step) * step;
  const ticks = [0, top / 2, top];
  const plotW = width - PAD.left - PAD.right;
  const slot = plotW / weeks.length;
  const bar = Math.min(40, slot * 0.6);
  const y = (v: number) => PAD.top + (H - PAD.top - PAD.bottom) * (1 - v / top);
  const w = hover === null ? null : weeks[hover];
  return (
    <div ref={ref} className="relative">
      <svg width={width} height={H} viewBox={`0 0 ${width} ${H}`} className="block" role="group" aria-label="Deployments per week, succeeded and failed">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={width - PAD.right} y1={y(t)} y2={y(t)} stroke={C.line} />
            <text x={PAD.left - 8} y={y(t) + 4} textAnchor="end" fontSize="12" fill={C.ink3}>{t}</text>
          </g>
        ))}
        {weeks.map((wk, i) => {
          const x = PAD.left + slot * i + (slot - bar) / 2;
          const ok = wk.deploys - wk.failed;
          const gap = ok && wk.failed ? 2 : 0;
          return (
            <g
              key={wk.week}
              tabIndex={0}
              role="img"
              aria-label={`${wk.week}: ${wk.deploys} deployments, ${wk.failed} failed, ${wk.prodSuccess} successful in production`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(i)}
              onBlur={() => setHover(null)}
              className="outline-none"
              data-testid="del-week"
            >
              <rect x={PAD.left + slot * i} y={PAD.top} width={slot} height={H - PAD.top - PAD.bottom} fill={hover === i ? C.panel2 : 'transparent'} />
              {ok > 0 && <rect x={x} y={y(ok)} width={bar} height={y(0) - y(ok)} rx={4} fill={OK} />}
              {wk.failed > 0 && <rect x={x} y={y(wk.deploys)} width={bar} height={y(ok) - y(wk.deploys) - gap} rx={4} fill={FAILED} />}
              {wk.prodSuccess > 0 && (
                <>
                  <circle cx={x + bar / 2} cy={y(wk.deploys) - 12} r={4} fill={PROD} stroke={C.panel} strokeWidth={2} />
                  <text x={x + bar / 2 + 8} y={y(wk.deploys) - 8} fontSize="12" fill={C.ink2}>{wk.prodSuccess}</text>
                </>
              )}
              <text x={PAD.left + slot * i + slot / 2} y={H - 10} textAnchor="middle" fontSize="12" fill={C.ink3}>{(i % 2 === weeks.length % 2 || slot > 56) && `W${wk.week.slice(-2)}`}</text>
            </g>
          );
        })}
      </svg>
      {w && hover !== null && (
        <div role="tooltip" className="pointer-events-none absolute z-20 w-56 rounded-control border border-line-strong bg-panel-2 p-4 shadow-[0_16px_32px_-12px_rgba(0,8,12,0.7)]" style={{ left: Math.min(Math.max(0, PAD.left + slot * hover + slot / 2 - 112), width - 224), top: 0 }}>
          <p className="text-small font-semibold text-ink">{w.week} · from {fmtShort(w.start)}</p>
          <p className="mt-1 text-small text-ink-2 tnum">{w.deploys} deployments · {w.failed} failed ({pct(w.failed, w.deploys)})</p>
          <p className="text-small text-ink-2 tnum">{w.prodSuccess} successful in production</p>
        </div>
      )}
    </div>
  );
}

function Weekly({ d }: { d: Delivery }) {
  return (
    <section aria-labelledby="del-weekly-h" className="rounded-panel border border-line bg-panel p-6" data-testid="del-weekly">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <h2 id="del-weekly-h" className="text-heading font-semibold text-ink">Deployments per week</h2>
        <ul className="m-0 flex list-none flex-wrap gap-4 p-0 text-small text-ink-2">
          <li className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-[3px]" style={{ background: OK }} />Succeeded or running</li>
          <li className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-[3px]" style={{ background: FAILED }} />Failed</li>
          <li className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: PROD }} />Successful in production (number)</li>
        </ul>
      </div>
      <div className="mt-4">
        <WeeklyChart weeks={d.weekly} />
      </div>
      <div className="sr-only">
        <table>
          <caption>Deployments per week</caption>
          <thead><tr><th>Week</th><th>Deployments</th><th>Failed</th><th>Successful in production</th></tr></thead>
          <tbody>{d.weekly.map((w) => <tr key={w.week}><td>{w.week}</td><td>{w.deploys}</td><td>{w.failed}</td><td>{w.prodSuccess}</td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}

const TH = 'border-b border-line bg-panel-2 px-3 py-3 text-left text-small font-medium whitespace-nowrap text-ink-2 first:pl-5 last:pr-5';
const TD = 'border-b border-line px-3 py-3 align-middle first:pl-5 last:pr-5';

function Teams({ d }: { d: Delivery }) {
  return (
    <section aria-labelledby="del-teams-h" className="overflow-hidden rounded-panel border border-line bg-panel" data-testid="del-teams">
      <h2 id="del-teams-h" className="px-6 pt-6 pb-4 text-heading font-semibold text-ink">By team</h2>
      <div className="overflow-x-auto">
        <table className="w-full border-separate border-spacing-0 text-body">
          <thead>
            <tr>
              <th scope="col" className={TH}>Team</th>
              <th scope="col" className={`${TH} text-right`}>Repositories</th>
              <th scope="col" className={`${TH} text-right`}>Reached production</th>
              <th scope="col" className={`${TH} text-right`}>Deployments, {d.windowDays} days</th>
              <th scope="col" className={`${TH} text-right`}>Failed</th>
            </tr>
          </thead>
          <tbody>
            {d.teams.map((t) => (
              <tr key={t.team} className="hover:bg-panel-2">
                <td className={TD}>
                  <a href={href.delivery({ team: t.team })} className="font-semibold text-ink no-underline hover:text-clear hover:underline">{t.label}</a>
                  {t.label !== t.team && <span className="ml-2 text-small text-ink-3">{t.team}</span>}
                </td>
                <td className={`${TD} text-right tnum`}>{t.repos}</td>
                <td className={`${TD} text-right tnum`}>{t.reachedProd}</td>
                <td className={`${TD} text-right tnum`}>{t.deploys30d}</td>
                <td className={`${TD} text-right tnum`}>
                  {t.failed30d} <span className="text-small text-ink-3">{pct(t.failed30d, t.deploys30d)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/** Twelve weeks of deployments as a sparkline of bars. */
export function Spark({ values, label }: { values: number[]; label: string }) {
  const max = Math.max(1, ...values);
  return (
    <svg width={values.length * 6} height={20} viewBox={`0 0 ${values.length * 6} 20`} role="img" aria-label={label} className="block">
      {values.map((v, i) => (
        <rect key={i} x={i * 6} y={v ? 20 - Math.max(2, (v / max) * 20) : 19} width={4} height={v ? Math.max(2, (v / max) * 20) : 1} rx={1} fill={v ? C.data1 : C.line} />
      ))}
    </svg>
  );
}

/** One dot per step of the promotion path: filled when it succeeded there, ringed in red when it only failed. */
export function EnvLadder({ repo, d }: { repo: DeliveryRepo; d: Delivery }) {
  const by = new Map(repo.envs.map((e) => [e.env, e]));
  // relative: the sr-only labels are absolute and would otherwise escape the table's scroll viewport.
  return (
    <span className="relative inline-flex items-center gap-1.5">
      {d.envs
        .filter((e) => e.path)
        .map((e) => {
          const r = by.get(e.id);
          const state = r?.lastSuccess ? `last success ${fmtShort(r.lastSuccess)}` : r ? 'deployed, never succeeded' : 'never deployed';
          const fill = r?.lastSuccess ? (e.prod ? PROD : OK) : 'transparent';
          const stroke = r?.lastSuccess ? fill : r ? FAILED : C.lineStrong;
          return (
            <span key={e.id} title={`${e.label}: ${state}`} className="inline-flex items-center gap-1">
              <svg width="12" height="12" aria-hidden="true">
                <circle cx="6" cy="6" r="4.5" fill={fill} stroke={stroke} strokeWidth="1.5" />
              </svg>
              <span className="sr-only">{`${e.label}: ${state}.`}</span>
            </span>
          );
        })}
    </span>
  );
}

type SortKey = 'name' | 'team' | 'prod' | 'lastProd' | 'deploys' | 'failed' | 'last';
const SORTS: Record<SortKey, (r: DeliveryRepo) => string | number> = {
  name: (r) => r.name,
  team: (r) => r.team ?? '',
  prod: (r) => r.prodDeploys,
  lastProd: (r) => r.lastProdDeploy ?? '',
  deploys: (r) => r.deploys30d,
  failed: (r) => (r.deploys30d ? r.failed30d / r.deploys30d : -1),
  last: (r) => r.lastDeploy ?? '',
};

function Repos({ d, params }: { d: Delivery; params: URLSearchParams }) {
  const env = params.get('env');
  const team = params.get('team');
  const all = params.get('all') === '1';
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: 'deploys', desc: true });
  const rows = useMemo(() => {
    const out = d.repos.filter((r) => (all || !r.excluded) && (!team || r.team === team) && (!env || r.envs.some((e) => e.env === env && e.lastSuccess)));
    const f = SORTS[sort.key];
    return out.sort((a, b) => {
      const c = f(a) < f(b) ? -1 : f(a) > f(b) ? 1 : 0;
      return (sort.desc ? -c : c) || a.name.localeCompare(b.name);
    });
  }, [d.repos, all, team, env, sort]);
  const excluded = d.repos.filter((r) => r.excluded).length;
  const filters = { env: env ?? undefined, team: team ?? undefined };
  const envLabel = d.envs.find((e) => e.id === env)?.label;
  const teamLabel = d.teams.find((t) => t.team === team)?.label ?? team;
  const head = (key: SortKey, label: string, right = false) => (
    <th scope="col" className={`${TH} ${right ? 'text-right' : ''}`} aria-sort={sort.key === key ? (sort.desc ? 'descending' : 'ascending') : 'none'}>
      <button type="button" className="cursor-pointer whitespace-nowrap text-ink-2 hover:text-ink" onClick={() => setSort((s) => ({ key, desc: s.key === key ? !s.desc : key !== 'name' && key !== 'team' }))}>
        {label}
        {sort.key === key ? (sort.desc ? ' ↓' : ' ↑') : ''}
      </button>
    </th>
  );
  return (
    <section aria-labelledby="del-repos-h" className="overflow-hidden rounded-panel border border-line bg-panel" data-testid="del-repos">
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 pt-6 pb-4">
        <h2 id="del-repos-h" className="text-heading font-semibold text-ink">
          {plural(rows.length, 'repository', 'repositories')}
          {envLabel && <span className="text-ink-3"> · succeeded in {envLabel}</span>}
          {team && <span className="text-ink-3"> · {teamLabel}</span>}
        </h2>
        <div className="flex flex-wrap items-center gap-4 text-small">
          {(env || team) && <a href={href.delivery({ all: all ? '1' : undefined })} data-testid="del-clear">Clear filter</a>}
          {excluded > 0 && (
            <a href={href.delivery({ ...filters, all: all ? undefined : '1' })} data-testid="del-toggle-all">
              {all ? 'Hide' : 'Show'} {excluded} not counted (tooling, template, test)
            </a>
          )}
        </div>
      </div>
      <ScrollTable label="Repositories" maxHeight="70dvh" testId="del-repo-scroll">
        <table className="w-full border-separate border-spacing-0 text-body" data-testid="del-repo-table" data-count={rows.length}>
          <thead className="sticky top-0 z-20">
            <tr>
              {head('name', 'Repository')}
              {head('team', 'Team')}
              <th scope="col" className={TH}>{d.envs.filter((e) => e.path).map((e) => e.label).join(' · ')}</th>
              {head('lastProd', 'Last production deploy')}
              {head('prod', 'Production deploys', true)}
              {head('deploys', `Deployments, ${d.windowDays} days`, true)}
              {head('failed', 'Failed', true)}
              <th scope="col" className={TH}>12 weeks</th>
              {head('last', 'Last deploy')}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name} className="hover:bg-panel-2" data-repo={r.name}>
                <td className={TD}>
                  {r.url ? (
                    <a href={r.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-semibold whitespace-nowrap text-ink no-underline hover:text-clear hover:underline">
                      {r.name} <ArrowUpRightIcon width={12} height={12} />
                    </a>
                  ) : (
                    <span className="font-semibold whitespace-nowrap text-ink">{r.name}</span>
                  )}
                  <span className="block text-small whitespace-nowrap">
                    {r.excluded ? (
                      <span className="text-ink-3">Not counted: {r.excluded}</span>
                    ) : r.urn ? (
                      <a href={href.product(r.urn)}>Product page</a>
                    ) : (
                      <span className="text-ink-3" data-testid="del-not-in-register">Not in register</span>
                    )}
                  </span>
                </td>
                <td className={`${TD} whitespace-nowrap text-ink-2`}>{r.team ?? '–'}</td>
                <td className={TD}><EnvLadder repo={r} d={d} /></td>
                <td className={`${TD} whitespace-nowrap ${r.lastProdDeploy ? 'text-ink' : 'text-ink-3'}`}>{r.lastProdDeploy ? fmtShort(r.lastProdDeploy) : 'Never'}</td>
                <td className={`${TD} text-right tnum`}>{r.prodDeploys}</td>
                <td className={`${TD} text-right tnum`}>{r.deploys30d}</td>
                <td className={`${TD} text-right whitespace-nowrap tnum`}>
                  {r.failed30d} <span className="text-small text-ink-3">{pct(r.failed30d, r.deploys30d)}</span>
                </td>
                <td className={TD}><Spark values={r.weekly} label={`Deployments per week, last 12 weeks: ${r.weekly.join(', ')}`} /></td>
                <td className={`${TD} whitespace-nowrap text-ink-2`}>{r.lastDeploy ? fmtShort(r.lastDeploy) : '–'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ScrollTable>
    </section>
  );
}

export default function DeliveryView({ params }: { params: URLSearchParams }) {
  const s = useSnapshot();
  const d = s.delivery;
  if (!d) {
    return (
      <p className="rounded-panel border border-line bg-panel p-6 text-body text-ink-2" data-testid="delivery-view">
        No GitHub extract in this week's inbox. Run <code>dp fetch-github</code>, then <code>dp build</code>.
      </p>
    );
  }
  return (
    <div className="space-y-6" data-testid="delivery-view">
      <DeliverySummary />
      <Weekly d={d} />
      <Teams d={d} />
      <Repos d={d} params={params} />
    </div>
  );
}
