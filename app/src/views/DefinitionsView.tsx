/* #/definitions  Generated from the registry carried in the snapshot. */

import FlagBadge from '@/components/FlagBadge';
import HealthBadge from '@/components/HealthBadge';
import StageMark from '@/components/StageMark';
import { useSnapshot } from '@/lib/context';
import { fmtDate, quarterLabel } from '@/lib/format';
import { STAGES, STAGE_ORDER, type Health, type Stage } from '@/lib/theme';
import { READINESS } from '@/components/StatStrip';

const STAGE_RULE: Record<Stage, [string, string]> = {
  Ideation: ['The product is registered. It has passed no gate.', 'In design'],
  'In design': ['The product passed G1 Intake. (Or a G5 scope change before go-live.)', 'In design'],
  'In development': ['The product passed G2 Contract.', 'In build'],
  'In testing': ['The product passed G3 Build.', 'In certification'],
  Live: ['The product passed G4 Certify. It stays Live during a G5 revision.', 'Live, Live · in revision'],
  'Failed / retired': ['The product passed G6 Retire, or the team cancelled it.', 'Retired, Cancelled'],
};

/* What passing each gate means. Drafted from the gate names of the Data Product Governance Framework, to be
   confirmed by the EDP Governance Lead. */
const GATES: { gate: string; name: string; from: Stage | 'Live'; to: Stage; meaning: string }[] = [
  { gate: 'G1', name: 'Intake', from: 'Ideation', to: 'In design', meaning: 'The portfolio accepts the idea. The business owner and the use case are named. The URN is reserved. The delivery clock starts.' },
  { gate: 'G2', name: 'Contract', from: 'In design', to: 'In development', meaning: 'The team and the consumers agree the data contract: schema, meaning, quality rules, service levels and access.' },
  { gate: 'G3', name: 'Build', from: 'In development', to: 'In testing', meaning: 'The team builds the product on the platform to its contract. Pipelines, tests and documentation are complete. The product is ready for certification tests.' },
  { gate: 'G4', name: 'Certify (GA)', from: 'In testing', to: 'Live', meaning: 'The product passes certification. It is published and available to all users. The first G4 counts as certified for the quarter.' },
  { gate: 'G5', name: 'Revise', from: 'Live', to: 'In design', meaning: 'A live product opens again for a scope change or a fix. A new iteration starts. The product stays Live.' },
  { gate: 'G6', name: 'Retire', from: 'Live', to: 'Failed / retired', meaning: 'The team removes the product from service. A product cancelled before go-live counts as failed.' },
];

function StageChip({ stage }: { stage: Stage }) {
  return (
    <span className="inline-flex h-9 items-center gap-2 rounded-full border px-3.5 text-body font-semibold whitespace-nowrap text-ink" style={{ borderColor: `color-mix(in srgb, ${STAGES[stage].color} 45%, transparent)`, background: `color-mix(in srgb, ${STAGES[stage].color} 10%, transparent)` }}>
      <StageMark stage={stage} size={16} />
      {stage}
    </span>
  );
}

function GateFlow() {
  const main = GATES.slice(0, 4);
  return (
    <div className="px-6 py-6" data-testid="gate-flow">
      <ol className="m-0 flex list-none flex-col items-start gap-2 p-0 lg:flex-row lg:flex-wrap lg:items-center lg:gap-0">
        <li>
          <StageChip stage="Ideation" />
        </li>
        {main.map((g) => (
          <li key={g.gate} className="flex flex-col items-start gap-2 lg:flex-row lg:items-center">
            <span className="flex items-center gap-2 pl-4 text-small text-ink-3 lg:px-2" aria-label={`then gate ${g.gate} ${g.name}`}>
              <span className="hidden h-px w-5 bg-line-strong lg:block" aria-hidden="true" />
              <span className="rounded-control border border-line-strong bg-panel-2 px-2 py-0.5 font-semibold text-ink">{g.gate}</span>
              <span className="whitespace-nowrap">{g.name}</span>
              <span className="hidden h-px w-5 bg-line-strong lg:block" aria-hidden="true" />
              <span aria-hidden="true">→</span>
            </span>
            <StageChip stage={g.to} />
          </li>
        ))}
      </ol>
      <p className="mt-4 text-small text-ink-3">
        After Live: <span className="font-semibold text-ink-2">G5 Revise</span> starts a new iteration. The product stays Live. <span className="font-semibold text-ink-2">G6 Retire</span> ends the product. A cancelled product counts as failed.
      </p>
    </div>
  );
}

const HEALTH_RULE: [Health, string][] = [
  ['ahead', '110% or more of the expected number.'],
  ['on-track', '90% to 109%.'],
  ['at-risk', '70% to 89%.'],
  ['off-track', 'Below 70%.'],
  ['no-target', 'No target this quarter.'],
];

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={id} className="overflow-hidden rounded-panel border border-line bg-panel">
      <h2 id={id} className="border-b border-line px-6 pt-6 pb-4 text-heading font-semibold text-ink">
        {title}
      </h2>
      {children}
    </section>
  );
}

const th = 'px-6 py-3 text-left text-small font-medium text-ink-3';
const td = 'px-6 py-4 align-top';

export default function DefinitionsView() {
  const s = useSnapshot();
  const metrics = [...s.registry.metrics].sort((a, b) => a.order - b.order);
  return (
    <div className="space-y-10" data-testid="definitions-view">
      <div>
        <h1 className="text-title font-semibold text-ink">How each number is defined</h1>
        <p className="mt-3 max-w-[68ch] text-lead text-ink-2">
          Week {Number(s.weekId.slice(-2))}, as of {fmtDate(s.asOfDate)}, quarter {quarterLabel(s.quarter)}. All numbers come from the product register and its source files. No number comes from a self-assessed rating. When fewer than three products give a median, the dashboard shows each value. Self-reported values have a label.
        </p>
      </div>

      <Section id="health-h" title="Domain health">
        <ul className="divide-y divide-line">
          {HEALTH_RULE.map(([status, rule]) => (
            <li key={status} className="flex flex-col gap-2 px-6 py-4 sm:flex-row sm:items-center sm:gap-4">
              <span className="w-36 shrink-0">
                <HealthBadge status={status} size="md" />
              </span>
              <span className="max-w-[68ch] text-body text-ink-2">{rule}</span>
            </li>
          ))}
          <li className="max-w-[90ch] px-6 py-4 text-body text-ink-3">
            Expected = quarter target × part of the quarter passed, rounded to a whole product. A closed quarter shows Above, Met or Below target.
          </li>
        </ul>
      </Section>

      <Section id="metrics-h" title="Metrics">
        <table className="w-full border-collapse text-body">
          <thead>
            <tr className="border-b border-line">
              <th scope="col" className={th}>Metric</th>
              <th scope="col" className={th}>Definition</th>
              <th scope="col" className={th}>Shown on</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => (
              <tr key={m.id} className="border-b border-line last:border-b-0">
                <th scope="row" className={`${td} w-64 text-left font-semibold text-ink`}>
                  {m.label}
                </th>
                <td className={`${td} max-w-[68ch] text-ink-2`}>{m.definition}</td>
                <td className={`${td} whitespace-nowrap text-ink-3`}>{m.execTile ? 'Executive overview' : READINESS.includes(m.id) ? 'Technical readiness' : 'Domain table and rings'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section id="flags-h" title="Flags">
        <table className="w-full border-collapse text-body">
          <tbody>
            {s.registry.flags.map((f) => (
              <tr key={f.code} className="border-b border-line last:border-b-0">
                <td className={`${td} w-44`}>
                  <FlagBadge code={f.code} size="md" />
                </td>
                <td className={`${td} text-ink-2`}>{f.definition}</td>
                <td className={`${td} whitespace-nowrap text-ink-3`}>{f.level === 'domain' ? 'Per domain' : 'Per product'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section id="gates-h" title="Stages and the gates between them">
        <GateFlow />
        <table className="w-full border-collapse border-t border-line text-body">
          <thead>
            <tr className="border-b border-line">
              <th scope="col" className={th}>Gate</th>
              <th scope="col" className={th}>What passing it means</th>
              <th scope="col" className={th}>Opens</th>
            </tr>
          </thead>
          <tbody>
            {GATES.map((g) => (
              <tr key={g.gate} className="border-b border-line last:border-b-0" data-testid={`gate-${g.gate}`}>
                <th scope="row" className={`${td} w-48 text-left font-semibold whitespace-nowrap text-ink`}>
                  {g.gate} {g.name}
                </th>
                <td className={`${td} max-w-[68ch] text-ink-2`}>{g.meaning}</td>
                <td className={`${td} whitespace-nowrap`}>
                  <span className="inline-flex items-center gap-2 text-ink-2">
                    <StageMark stage={g.to} />
                    {g.gate === 'G5' ? 'New iteration' : g.to}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section id="status-h" title="Lifecycle stages">
        <table className="w-full border-collapse text-body">
          <thead>
            <tr className="border-b border-line">
              <th scope="col" className={th}>Stage</th>
              <th scope="col" className={th}>Starts when</th>
              <th scope="col" className={th}>Register status</th>
            </tr>
          </thead>
          <tbody>
            {STAGE_ORDER.map((st) => (
              <tr key={st} className="border-b border-line last:border-b-0">
                <td className={`${td} whitespace-nowrap`}>
                  <span className="inline-flex items-center gap-2.5 font-semibold text-ink">
                    <StageMark stage={st} size={20} />
                    {st}
                  </span>
                </td>
                <td className={`${td} text-ink-2`}>{STAGE_RULE[st][0]}</td>
                <td className={`${td} text-ink-3`}>{STAGE_RULE[st][1]}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="border-t border-line px-6 py-4 text-body text-ink-3">Each stage fills one more quarter of the circle, from 12 o'clock. The green gets brighter as the product moves forward. Ideation is a dotted ring. Failed or retired is a red double ring. A yellow dot on a bubble shows that the product needs attention.</p>
      </Section>

      <Section id="quarters-h" title="Quarters and weeks">
        <ul className="divide-y divide-line text-body text-ink-2">
          <li className="max-w-[80ch] px-6 py-4">The quarter selector shows each closed quarter on its last day. The dashboard calculates it from the gate dates: stages, certifications, targets, time to production and time to first consumer. The register keeps plans, flags and usage for the current week only. Thus a closed quarter shows no forecast, no flags and no usage.</li>
          <li className="max-w-[80ch] px-6 py-4">By week, the trend counts the products certified in the quarter until the end of each week (Monday to Sunday). The dashed line is the target pace. It goes up evenly from zero to the target on the last day of the quarter.</li>
        </ul>
      </Section>
    </div>
  );
}
