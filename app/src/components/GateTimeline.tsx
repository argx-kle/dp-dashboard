/* A product's stage history on the react-bits Stepper: each governance gate (G1 to G6) is shown as the business
   stage it opens, with the gate named inside for the evidence trail. Select a step to see its passes or its plan. */

import Stepper, { type StepSpec, type StepState } from '@/components/reactbits/Stepper';
import { fmtDate } from '@/lib/format';
import type { ProductRow } from '@/types/snapshot';

const GATES = [
  { id: 'G1', name: 'Intake', stage: 'In design' },
  { id: 'G2', name: 'Contract', stage: 'In development' },
  { id: 'G3', name: 'Build', stage: 'In testing' },
  { id: 'G4', name: 'Certify (GA)', stage: 'Live' },
  { id: 'G5', name: 'Revise', stage: 'Revision' },
  { id: 'G6', name: 'Retire', stage: 'Retired' },
];

function inferNext(p: ProductRow): string | null {
  if (p.status === 'Cancelled' || p.status === 'Retired') return null;
  const last = p.lastGate?.gate;
  if (!last) return 'G1';
  if (last === 'G4') return null;
  if (last === 'G5') return 'G2';
  const n = Number(last[1]);
  return n < 4 ? `G${n + 1}` : null;
}

export default function GateTimeline({ product }: { product: ProductRow }) {
  const next = product.nextGate?.gate ?? inferNext(product);
  const steps: StepSpec[] = GATES.map((g) => {
    const passes = product.gates.filter((x) => x.gate === g.id);
    const last = passes.at(-1);
    let state: StepState = 'inactive';
    if (passes.length) state = 'complete';
    else if (next === g.id) state = 'active';
    else if (g.id === 'G5' || g.id === 'G6') state = 'skipped';
    const planned = next === g.id ? product.nextGate : undefined;
    return {
      id: g.id,
      label: g.stage,
      sublabel: last ? `${fmtDate(last.date)}${passes.length > 1 ? ` · ${passes.length} passes` : ''}` : planned ? `plan ${fmtDate(planned.plannedDate)}` : `gate ${g.id}`,
      state,
      content: (
        <div className="rounded-control border border-line bg-panel-2 px-4 py-3.5 text-body">
          <div className="font-semibold text-ink">
            {g.stage} <span className="font-normal text-ink-3">· gate {g.id} {g.name}</span>
          </div>
          {passes.length > 0 ? (
            <ul className="mt-1.5 space-y-1 text-ink-2">
              {passes.map((p, i) => (
                <li key={i}>
                  Passed <span className="text-ink">{fmtDate(p.date)}</span>
                  {product.iteration > 1 && <span className="text-ink-3"> · iteration {p.iteration}</span>}
                  {p.g5Path && <span className="text-ink-3"> · {p.g5Path}</span>}
                  {' · '}
                  {p.evidenceUrl ? (
                    <a href={p.evidenceUrl} target="_blank" rel="noreferrer">
                      evidence
                    </a>
                  ) : (
                    <span className="text-sig-yellow">no evidence link</span>
                  )}
                </li>
              ))}
            </ul>
          ) : planned ? (
            <p className="mt-1.5 text-ink-2">
              Planned <span className="text-ink">{fmtDate(planned.plannedDate)}</span>
              {planned.baselineDate !== planned.plannedDate && <span className="text-ink-3"> · first planned {fmtDate(planned.baselineDate)}</span>}
              <span className="text-ink-3"> · {planned.slips === 0 ? 'never moved' : `moved later ${planned.slips} ${planned.slips === 1 ? 'time' : 'times'}`}</span>
              {planned.overdueDays > 0 ? <span className="ml-2 font-semibold text-sig-red">{planned.overdueDays} days late</span> : <span className="ml-2 text-ink-3">{-planned.overdueDays} days to go</span>}
            </p>
          ) : state === 'active' ? (
            <p className="mt-1.5 text-ink-3">Next stage, no date planned yet.</p>
          ) : (
            <p className="mt-1.5 text-ink-3">{g.id === 'G5' ? 'No revision recorded.' : g.id === 'G6' ? 'Not retired.' : 'Not reached yet.'}</p>
          )}
        </div>
      ),
    };
  });
  return <Stepper steps={steps} ariaLabel={`Stage history for ${product.name}`} />;
}
