/* #/products/:urn  Product detail: stage and flags, stage history (the governance gates) with G5 iterations, delivery,
   the facts. While the register has no gate dates, delivery leads: how far the repository has got on the promotion
   path, what is failing now, twelve weeks and the latest deployments; then NextData and validation. */

import GateTimeline from '@/components/GateTimeline';
import Stepper, { type StepSpec, type StepState } from '@/components/reactbits/Stepper';
import { PlatformLabel } from '@/components/StageMark';
import StatusPips from '@/components/StatusPips';
import FlagBadge from '@/components/FlagBadge';
import SourceLabel from '@/components/SourceLabel';
import { ArrowLeftIcon, ArrowUpRightIcon } from '@/components/Icons';
import { useSnapshot } from '@/lib/context';
import { fmtDate, fmtShort, humanize } from '@/lib/format';
import { envLabel, failingReasons, hasGates, platformStage, promotionPath } from '@/lib/platform';
import { href } from '@/lib/router';
import { domainName, productByUrn } from '@/lib/select';
import { C, SIGNALS, STAGE_AFTER_GATE, gateLabel } from '@/lib/theme';
import type { GithubDeploy, ProductRow } from '@/types/snapshot';

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-panel px-6 py-4">
      <dt className="text-small text-ink-3">{label}</dt>
      <dd className="mt-1 text-body text-ink">{children}</dd>
    </div>
  );
}

const pct = (v: number) => `${Math.round(v * 100)}%`;

/* NextData deployments and validation results, and the GitHub repository. Validation check IDs are never written as bare gate names. */
function PlatformFacts({ product: p }: { product: ProductRow }) {
  const nd = p.nextdata;
  const v = p.validation;
  return (
    <section className="mt-6 overflow-hidden rounded-panel border border-line bg-panel" aria-labelledby="platform-h" data-testid="platform-section">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 px-6 pt-6 pb-4">
        <h2 id="platform-h" className="text-heading font-semibold text-ink">
          On the platform
        </h2>
        {nd?.url && (
          <a href={nd.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-body" data-testid="nextdata-link">
            Open in NextData <ArrowUpRightIcon width={14} height={14} />
          </a>
        )}
      </div>
      <div className="grid gap-px border-t border-line bg-line lg:grid-cols-2">
        {(nd || v) && (
          <>
            <div className="min-w-0 bg-panel p-6">
              <h3 className="flex items-center gap-2 text-small font-medium text-ink-2">
                Runtime <SourceLabel source="nextdata" />
              </h3>
              {nd ? (
                <>
                  <p className="mt-2 text-lead text-ink" data-testid="platform-runtime">
                    {nd.runtime}
                    {nd.env && <span className="text-ink-3"> · {nd.env}</span>}
                  </p>
                  <p className="mt-1 text-small text-ink-3">
                    {nd.team ? `${nd.team} · ` : ''}
                    {p.platformDomain ? `registered under ${p.platformDomain}` : 'no NextData domain on record'}
                    {nd.names.length > 1 && ` · also deployed as ${nd.names.slice(1).join(', ')}`}
                  </p>
                  {nd.deployments.length > 0 ? (
                    <div className="mt-4 overflow-x-auto">
                      <table className="w-full border-collapse text-small" aria-label="NextData deployments">
                        <thead>
                          <tr className="border-b border-line text-left text-ink-3">
                            <th scope="col" className="py-2 pr-4 font-medium">Name</th>
                            <th scope="col" className="py-2 pr-4 font-medium">Environment</th>
                            <th scope="col" className="py-2 pr-4 font-medium">Version</th>
                            <th scope="col" className="py-2 pr-4 font-medium">State</th>
                            <th scope="col" className="py-2 font-medium">
                              <span className="sr-only">Link</span>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="tnum">
                          {nd.deployments.map((d, i) => (
                            <tr key={`${d.name}-${d.env}-${d.version}-${i}`} className="border-b border-line last:border-b-0">
                              <td className="py-2 pr-4 text-ink-2">{d.name}</td>
                              <td className="py-2 pr-4 text-ink-2">{d.env}</td>
                              <td className="py-2 pr-4 text-ink-2">{d.version}</td>
                              <td className={`py-2 pr-4 ${d.state === 'Started' ? 'text-ink-2' : 'font-semibold text-ink'}`}>{d.state}</td>
                              <td className="py-2 text-right whitespace-nowrap">
                                {d.url && (
                                  <a href={d.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${d.name} (${d.env} ${d.version}) in NextData`}>
                                    Open
                                  </a>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="mt-4 text-body text-ink-3">No deployment in the NextData listing.</p>
                  )}
                </>
              ) : (
                <p className="mt-2 text-body text-ink-3">Not in the NextData listing.</p>
              )}
            </div>
            <div className="min-w-0 bg-panel p-6">
              <h3 className="flex items-center gap-2 text-small font-medium text-ink-2">
                Finish-spec validation <SourceLabel source="validation" />
              </h3>
              {v ? (
                <>
                  <p className="mt-2 text-lead text-ink" data-testid="platform-spec-score">
                    {v.score != null ? pct(v.score) : 'No score'}
                    <span className="text-small text-ink-3"> · run {fmtDate(v.lastRun)}</span>
                  </p>
                  <p className="mt-1 text-small text-ink-3">
                    Owner in the repository: {v.ownerStatus ?? 'not stated'}
                    {v.p1Findings != null && ` · ${v.p1Findings} blocking findings`}
                    {v.keyids && v.keyids.length > 0 && ` · keyid ${v.keyids.join(', ')}`}
                  </p>
                  {v.components && v.components.length > 0 && (
                    <ul className="mt-4 space-y-2.5" aria-label="Component scores">
                      {v.components.map((c) => (
                        <li key={c.label} className="grid grid-cols-[minmax(0,10rem)_1fr_3rem] items-center gap-3 text-small">
                          <span className="truncate text-ink-2">{c.label}</span>
                          <span className="h-1.5 overflow-hidden rounded-full bg-track" aria-hidden="true">
                            <span className="block h-full rounded-full bg-data-1" style={{ width: pct(c.score) }} />
                          </span>
                          <span className="text-right text-ink tnum">{pct(c.score)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              ) : (
                <p className="mt-2 text-body text-ink-3">No validation results for this product.</p>
              )}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

const OUTCOME: Record<GithubDeploy['outcome'], { label: string; color: string }> = {
  success: { label: 'Succeeded', color: C.data2 },
  failure: { label: 'Failed', color: SIGNALS.red.color },
  error: { label: 'Error', color: SIGNALS.red.color },
  pending: { label: 'No result yet', color: C.ink3 },
};

/** Deployments per week, the same twelve weeks as the Delivery view. */
function WeekBars({ values, weeks }: { values: number[]; weeks: string[] }) {
  const max = Math.max(1, ...values);
  return (
    <ol className="m-0 grid list-none grid-cols-12 items-end gap-1.5 p-0" aria-label={`Deployments per week, last 12 weeks: ${values.join(', ')}`} data-testid="delivery-weeks">
      {values.map((v, i) => (
        <li key={i} className="flex flex-col items-center gap-1">
          <span className="text-small text-ink-2 tnum">{v || ''}</span>
          <span className="block w-full max-w-7 rounded-[3px]" style={{ height: v ? Math.max(3, (v / max) * 56) : 1, background: v ? C.data1 : C.line }} />
          <span className="text-small text-ink-3">{weeks[i] ? `W${weeks[i].slice(-2)}` : ''}</span>
        </li>
      ))}
    </ol>
  );
}

/* Delivery from the GitHub extract: the promotion path as a stepper (succeeded, failing now, not yet), the
   numbers of the last 30 days, twelve weeks of deployments and the latest ones. */
function DeliverySection({ product: p }: { product: ProductRow }) {
  const s = useSnapshot();
  const g = p.github!;
  const d = s.delivery;
  const repo = d?.repos.find((r) => r.name === g.repo);
  const byEnv = new Map((repo?.envs ?? []).map((e) => [e.env, e]));
  const broken = new Map((d?.broken ?? []).filter((b) => b.repo === g.repo).map((b) => [b.env, b]));
  const stage = platformStage(s, p);
  const failing = failingReasons(s, p).filter((r) => !r.endsWith('in NextData'));
  const failingAt = promotionPath(s).findIndex((e) => broken.has(e.id));
  const steps: StepSpec[] = promotionPath(s).map((e, i) => {
    const r = byEnv.get(e.id);
    const b = broken.get(e.id);
    const state: StepState = r?.lastSuccess ? 'complete' : i === stage.step ? 'active' : 'inactive';
    return {
      id: e.id,
      label: e.label,
      sublabel: b ? `failing since ${fmtShort(b.since)}` : r?.lastSuccess ? `last success ${fmtShort(r.lastSuccess)}` : r ? 'never succeeded' : 'not deployed',
      state,
      content: (
        <div className="rounded-control border border-line bg-panel-2 px-4 py-3.5 text-body">
          <div className="font-semibold text-ink">
            {e.label} <span className="font-normal text-ink-3">· {e.id}</span>
          </div>
          <p className="mt-1.5 text-ink-2">
            {r?.lastSuccess ? (
              <>
                Last success <span className="text-ink">{fmtDate(r.lastSuccess)}</span>
              </>
            ) : r ? (
              'Deployed here, never successfully.'
            ) : (
              'Not deployed here yet.'
            )}
            {r && (
              <span className="text-ink-3">
                {' · '}last {d?.windowDays ?? 30} days: {r.deploys30d} {r.deploys30d === 1 ? 'deployment' : 'deployments'}, {r.failed30d} failed
              </span>
            )}
          </p>
          {b && (
            <p className="mt-1 font-semibold text-ink">
              Failing since {fmtDate(b.since)}
              <span className="font-normal text-ink-3"> · the latest deployment here failed</span>
            </p>
          )}
        </div>
      ),
    };
  });
  return (
    <section className="mt-8 overflow-hidden rounded-panel border border-line bg-panel" aria-labelledby="delivery-h" data-testid="platform-github">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 px-6 pt-6">
        <h2 id="delivery-h" className="flex items-center gap-2 text-heading font-semibold text-ink">
          Delivery <SourceLabel source="github" />
        </h2>
        {g.url && (
          <a href={g.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-body" data-testid="github-link">
            Open in GitHub <ArrowUpRightIcon width={14} height={14} />
          </a>
        )}
      </div>
      <p className="mt-2 px-6 text-lead text-ink" data-testid="github-last-prod">
        {g.lastProdDeploy ? `Last production deploy ${fmtDate(g.lastProdDeploy)}` : 'Never deployed to production'}
      </p>
      <p className="mt-1 flex flex-wrap items-center gap-x-2 px-6 text-small text-ink-3">
        <span>{g.repo} · furthest step</span> <PlatformLabel stage={stage} />
      </p>
      {failing.length > 0 && (
        <p className="mx-6 mt-4 rounded-control border border-line-strong border-l-4 bg-panel-2 px-4 py-3 text-body text-ink" style={{ borderLeftColor: SIGNALS.red.color }} data-testid="delivery-failing">
          <strong className="font-semibold">Failing now:</strong> {failing.join(', ')}. The latest deployment {failing.length === 1 ? 'there' : 'in each'} failed.
        </p>
      )}
      <div className="px-6 pt-6 pb-2">
        {/* Open on the step that is failing now, if any; otherwise the Stepper's default (the furthest reached). */}
        <Stepper steps={steps} initialStep={failingAt >= 0 ? failingAt + 1 : undefined} ariaLabel={`Promotion path for ${p.name}`} />
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-x-8 gap-y-2 border-t border-line px-6 py-4 text-small text-ink-3 tnum" data-testid="github-delivery">
        <span>
          Last {d?.windowDays ?? 30} days: <span className="text-ink">{g.deploys30d}</span> deployments, {g.failed30d} failed{g.deploys30d > 0 && ` (${pct(g.failed30d / g.deploys30d)})`},{' '}
          <span className="text-ink">{g.prodDeploys30d}</span> in production
        </span>
        {repo && <span>{repo.prodDeploys} production {repo.prodDeploys === 1 ? 'deploy' : 'deploys'} ever</span>}
        {repo?.lastFailure && <span>Last failure {fmtDate(repo.lastFailure)}</span>}
      </div>
      <div className="grid gap-px border-t border-line bg-line lg:grid-cols-2">
        <div className="bg-panel p-6">
          <h3 className="mb-3 text-small font-medium text-ink-2">Deployments per week</h3>
          <WeekBars values={g.weekly} weeks={d?.weekly.map((w) => w.week) ?? []} />
        </div>
        <div className="min-w-0 bg-panel p-6">
          <h3 className="mb-3 text-small font-medium text-ink-2">Latest deployments</h3>
          {g.recent.length === 0 ? (
            <p className="text-body text-ink-3">No deployments yet.</p>
          ) : (
            <table className="w-full border-separate border-spacing-0 text-body" data-testid="delivery-recent">
              <thead>
                <tr>
                  <th scope="col" className="border-b border-line pb-2 text-left text-small font-medium text-ink-3">Environment</th>
                  <th scope="col" className="border-b border-line pb-2 text-left text-small font-medium text-ink-3">Started</th>
                  <th scope="col" className="border-b border-line pb-2 text-left text-small font-medium text-ink-3">Result</th>
                </tr>
              </thead>
              <tbody>
                {g.recent.map((r, i) => (
                  <tr key={i}>
                    <td className="border-b border-line/60 py-2 pr-3 whitespace-nowrap text-ink-2">{envLabel(s, r.env)}</td>
                    <td className="border-b border-line/60 py-2 pr-3 whitespace-nowrap text-ink-2 tnum">
                      {fmtShort(r.at)} <span className="text-ink-3">{r.at.slice(11, 16)} UTC</span>
                    </td>
                    <td className="border-b border-line/60 py-2 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1.5 text-ink">
                        <span className="h-2 w-2 rounded-full" style={{ background: OUTCOME[r.outcome].color }} aria-hidden="true" />
                        {OUTCOME[r.outcome].label}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </section>
  );
}

/** One line for the facts list: runtime, spec score, last production deployment. */
function platformSummary(p: ProductRow): string {
  const parts: string[] = [];
  if (p.nextdata) parts.push(`${p.nextdata.runtime}${p.nextdata.env && p.nextdata.runtime === 'Started' ? ` · ${p.nextdata.env}` : ''}`);
  else if (p.validation) parts.push('Not in NextData');
  if (p.validation?.score != null) parts.push(`spec ${Math.round(p.validation.score * 100)}%`);
  if (p.github) parts.push(p.github.lastProdDeploy ? `prod deploy ${fmtDate(p.github.lastProdDeploy)}` : 'no prod deploy');
  return parts.join(', ');
}

export default function ProductView({ urn }: { urn: string }) {
  const s = useSnapshot();
  const p = productByUrn(s, urn);
  if (!p) {
    return (
      <div className="py-16">
        <h1 className="text-title font-semibold text-ink">Product not found</h1>
        <p className="mt-2 text-lead text-ink-2">
          No product has the URN <code className="text-ink-3">{urn}</code> this week. <a href={href.products()}>See all products</a>.
        </p>
      </div>
    );
  }
  const name = (u: string) => {
    const t = productByUrn(s, u);
    return t ? (
      <a key={u} href={href.product(u)}>
        {t.name}
      </a>
    ) : (
      <span key={u} className="text-ink-3" title="Not in the register">
        {u}
      </span>
    );
  };
  const list = (urns: string[]) => (urns.length ? urns.map((u, i) => <span key={u}>{i > 0 && ', '}{name(u)}</span>) : <span className="text-ink-3">None</span>);
  const gates = hasGates(s);
  const delivery = p.github ? (
    <DeliverySection product={p} />
  ) : s.delivery && !gates ? (
    <section className="mt-8 rounded-panel border border-line bg-panel p-6" aria-labelledby="delivery-h" data-testid="delivery-none">
      <h2 id="delivery-h" className="flex items-center gap-2 text-heading font-semibold text-ink">
        Delivery <SourceLabel source="github" />
      </h2>
      <p className="mt-2 text-body text-ink-2">No GitHub repository is matched to this product. A repository the naming rules miss can be linked in crosswalk.csv with source github.</p>
    </section>
  ) : null;

  return (
    <div data-testid="product-view">
      <a href={href.products({ domain: p.domain })} className="inline-flex items-center gap-1.5 text-small text-ink-3 no-underline hover:text-ink">
        <ArrowLeftIcon width={14} height={14} /> {domainName(s, p.domain)} products
      </a>
      <h1 className="mt-3 text-title font-semibold text-ink">{p.name}</h1>
      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2">
        {gates ? <StatusPips product={p} /> : <PlatformLabel stage={platformStage(s, p)} className="text-body" />}
        <span className="text-small text-ink-3">
          <a href={href.domain(p.domain)} className="text-ink-2">
            {domainName(s, p.domain)}
          </a>
        </span>
        {(gates || p.dpo) && (
          <span className="text-small text-ink-3">
            Owner <span className="text-ink-2">{p.dpo ?? 'not assigned'}</span>
          </span>
        )}
      </div>
      <p className="mt-1.5 text-small text-ink-3">{p.urn}</p>

      {!gates && delivery}

      {gates && p.flags.length > 0 && (
        <ul className="mt-5 space-y-2" aria-label="Why this product is flagged">
          {p.flags.map((f) => (
            <li key={f.code} className="flex flex-wrap items-center gap-3">
              <FlagBadge code={f.code} size="md" />
              <span className="text-body text-ink-2">{humanize(f.reason, Number(s.asOfDate.slice(0, 4)))}</span>
            </li>
          ))}
        </ul>
      )}

      {gates && (
        <section className="mt-8 rounded-panel border border-line bg-panel p-6" aria-labelledby="timeline-h">
          <h2 id="timeline-h" className="mb-5 text-heading font-semibold text-ink">
            Stage history{p.iteration > 1 ? `, iteration ${p.iteration}` : ''}
          </h2>
          <GateTimeline product={p} />
        </section>
      )}

      {gates && delivery}

      {gates && (
      <section className="mt-6 overflow-hidden rounded-panel border border-line bg-panel" aria-labelledby="facts-h">
        <h2 id="facts-h" className="px-6 pt-6 pb-4 text-heading font-semibold text-ink">
          Facts
        </h2>
        <dl className="grid gap-px border-t border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          <Fact label="Stage">{p.lifecycle}{p.status === "Live · in revision" ? ", in revision" : ""}</Fact>
          <Fact label="Days in stage">{p.daysInStage}</Fact>
          <Fact label="First certified">{fmtDate(p.firstG4Date)}</Fact>
          <Fact label="Next gate">
            {p.nextGate ? (
              <>
                {gateLabel(p.nextGate.gate)}, planned {fmtDate(p.nextGate.plannedDate)} <span className="font-normal text-ink-3">· opens {STAGE_AFTER_GATE[p.nextGate.gate]}</span>
                <span className="mt-0.5 block text-small text-ink-3">
                  first planned {fmtDate(p.nextGate.baselineDate)} · {p.nextGate.slips === 0 ? 'never moved' : `moved later ${p.nextGate.slips} ${p.nextGate.slips === 1 ? 'time' : 'times'}`}
                </span>
              </>
            ) : (
              <span className="text-ink-3">–</span>
            )}
          </Fact>
          <Fact label="Planned go-live">
            {p.plannedGA ? (
              <>
                {fmtDate(p.plannedGA.plannedDate)}
                <span className="mt-0.5 block text-small text-ink-3">
                  first planned {fmtDate(p.plannedGA.baselineDate)} · {p.plannedGA.slips === 0 ? 'never moved' : `moved later ${p.plannedGA.slips} ${p.plannedGA.slips === 1 ? 'time' : 'times'}`}
                </span>
              </>
            ) : (
              <span className="text-ink-3">Not planned</span>
            )}
          </Fact>
          <Fact label="Named consumers">{p.namedConsumers}</Fact>
          <Fact label="Active users, 30 days">
            {p.activeUsers30d ? (
              <span className="inline-flex items-center gap-2">
                {p.activeUsers30d.value} <SourceLabel source={p.activeUsers30d.source} />
              </span>
            ) : (
              <span className="text-ink-3">Not reported</span>
            )}
          </Fact>
          <Fact label="First consumer">
            {p.firstConsumerDate ? (
              <span className="inline-flex items-center gap-2">
                {fmtDate(p.firstConsumerDate.value)} <SourceLabel source={p.firstConsumerDate.source} />
              </span>
            ) : (
              <span className="text-ink-3">None yet</span>
            )}
          </Fact>
          <Fact label="Last reviewed by owner">{fmtDate(p.reviewedOn)}</Fact>
          <Fact label="Consumed by">{list(p.consumedByProducts)}</Fact>
          <Fact label="Built on">{list(p.inputProducts)}</Fact>
          <Fact label="On the platform">
            {p.nextdata || p.validation || p.github ? (
              <button
                type="button"
                onClick={() => document.getElementById('platform-h')?.scrollIntoView({ block: 'start' })}
                className="cursor-pointer text-left text-link underline decoration-1 underline-offset-[3px] hover:text-clear"
              >
                {platformSummary(p)}
              </button>
            ) : (
              <span className="text-ink-3">No platform data this week</span>
            )}
          </Fact>
          {p.cancelledOn && <Fact label="Cancelled">{fmtDate(p.cancelledOn)}</Fact>}
        </dl>
      </section>
      )}

      {(p.nextdata || p.validation) && <PlatformFacts product={p} />}

      {p.dpoComment && (
        <section className="mt-6" aria-labelledby="comment-h">
          <h2 id="comment-h" className="mb-2 text-heading font-semibold text-ink">
            Owner's note
          </h2>
          <p className="max-w-[68ch] text-lead text-pretty text-ink-2">{p.dpoComment}</p>
        </section>
      )}
    </div>
  );
}
