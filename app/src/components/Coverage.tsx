/* Data coverage: how much of the data behind the numbers exists. A figure built on missing inputs must never
   read like a delivery result, so every incomplete input says "5 of 6" and links to the products missing it. */

import { useSnapshot } from '@/lib/context';
import { href } from '@/lib/router';
import { COVERAGE, metricCoverage, reportingItem } from '@/lib/select';
import { hasGates } from '@/lib/platform';

/** When every input is at or above this share, the strip steps aside (the notes under each number stay). */
export const COVERAGE_COMPLETE = 0.8;

const ORDER = ['gates', 'plans', 'reviewed', 'dpo', 'usage', 'consumers', 'validation', 'nextdata', 'github'];
/** The platform inputs: all the strip shows while the register has no gate dates. */
const PLATFORM = ['validation', 'nextdata', 'github'];

/** One line under a number when the input it needs is incomplete: "Gate dates for 5 of 6 active products". */
export function CoverageNote({ id, scope, className = '' }: { id: string; scope: string; className?: string }) {
  const s = useSnapshot();
  const r = metricCoverage(s, id, scope);
  if (!r) return null;
  const c = COVERAGE[r.kind];
  return (
    <a
      href={href.products({ missing: r.kind, domain: scope === 'org' ? undefined : scope })}
      className={`block text-small text-ink-3 no-underline hover:text-ink hover:underline ${className}`}
      data-testid={`coverage-note-${id}-${scope}`}
      data-count={r.of - r.have}
    >
      {c.label} for {r.have} of {r.of} {c.of}
    </a>
  );
}

export default function ReportingStrip({ scope = 'org' }: { scope?: string }) {
  const s = useSnapshot();
  const items = (hasGates(s) ? ORDER : PLATFORM).map((k) => reportingItem(s, k, scope)).filter((r) => r && r.of > 0) as NonNullable<ReturnType<typeof reportingItem>>[];
  if (items.length === 0 || items.every((r) => r.have / r.of >= COVERAGE_COMPLETE)) return null;
  return (
    <section aria-labelledby={`coverage-h-${scope}`} className="overflow-hidden rounded-panel border border-line bg-panel print-break-avoid" data-testid="reporting-strip">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 px-6 pt-6">
        <h2 id={`coverage-h-${scope}`} className="text-heading font-semibold text-ink">
          Reporting coverage
        </h2>
        <p className="text-small text-ink-3">The numbers are only as complete as these inputs. Each figure opens the products still missing it.</p>
      </div>
      <ul className="mt-4 grid gap-px border-t border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
        {items.map((r) => {
          const c = COVERAGE[r.kind];
          const share = r.have / r.of;
          const gap = r.of - r.have;
          return (
            <li key={r.kind} className="flex flex-col gap-2 bg-panel px-6 py-4">
              <span className="text-small font-medium text-ink-2">{c.label}</span>
              <span className="flex items-baseline gap-1.5 tnum">
                {gap > 0 ? (
                  <a
                    href={href.products({ missing: r.kind, domain: scope === 'org' ? undefined : scope })}
                    className="text-heading font-semibold text-ink no-underline hover:text-clear"
                    data-testid={`coverage-${r.kind}`}
                    data-count={gap}
                    aria-label={`${c.label}: ${r.have} of ${r.of} ${c.of}. Open the ${gap} products missing it`}
                  >
                    {r.have}
                  </a>
                ) : (
                  <span className="text-heading font-semibold text-ink" data-testid={`coverage-${r.kind}`} data-count={0}>
                    {r.have}
                  </span>
                )}
                <span className="text-small text-ink-3">
                  of {r.of} {c.of}
                </span>
              </span>
              <span className="h-1 overflow-hidden rounded-full bg-track" aria-hidden="true">
                <span className="block h-full rounded-full bg-data-1" style={{ width: `${Math.round(share * 100)}%` }} />
              </span>
            </li>
          );
        })}
        {/* Fill the last row so the ruled grid never shows an empty slot of hairline colour. */}
        {Array.from({ length: (4 - (items.length % 4)) % 4 }, (_, i) => (
          <li key={`fill-${i}`} aria-hidden="true" className={`bg-panel ${i < items.length % 2 ? 'hidden sm:block' : 'hidden lg:block'}`} />
        ))}
      </ul>
    </section>
  );
}
