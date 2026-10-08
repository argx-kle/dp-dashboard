/* Executive "Domains" panel: cluster map by default, the domain table on request (and in print).
   The map groups domains under their area (Commercial, TechOps, R&D, G&A) and shows only domains with
   products in them. Health is the domain's verdict on its label; each bubble is a product in its stage. */

import { useState } from 'react';
import ClusterMap, { type ClusterGroup } from '@/components/ClusterMap';
import DomainSummaryTable from '@/components/DomainSummaryTable';
import StageMark from '@/components/StageMark';
import { useSnapshot } from '@/lib/context';
import { fmtDate, plural } from '@/lib/format';
import { href } from '@/lib/router';
import { displayAreas, hasProducts } from '@/lib/select';
import { ATTENTION, stagesShown } from '@/lib/theme';
import type { ProductRow } from '@/types/snapshot';

export function StageLegend({ products, domain }: { products: ProductRow[]; domain?: string }) {
  return (
    <ul className="m-0 flex list-none flex-wrap items-center gap-x-5 gap-y-2 p-0 text-small text-ink-2" aria-label="Lifecycle stages">
      {stagesShown(products).map((st) => {
        const n = products.filter((p) => p.lifecycle === st).length;
        return (
          <li key={st}>
            <a href={href.products({ stage: st, domain })} className="inline-flex items-center gap-1.5 text-ink-2 no-underline hover:text-ink" data-testid={`legend-count-${st}`} data-count={n} aria-label={`${n} ${st.toLowerCase()}`}>
              <StageMark stage={st} />
              {st}
              <span className="font-semibold text-ink tnum">{n}</span>
            </a>
          </li>
        );
      })}
      {products.some((p) => p.flags.length > 0) && (
        <li>
          <a href={href.products({ flagged: '1', domain })} className="inline-flex items-center gap-1.5 text-ink-2 no-underline hover:text-ink" data-testid="legend-count-attention" data-count={products.filter((p) => p.flags.length > 0).length}>
            <svg width="12" height="12" viewBox="-6 -6 12 12" aria-hidden="true">
              <circle r={4.2} fill={ATTENTION} stroke="#001A22" strokeWidth={1.5} />
            </svg>
            Needs attention
            <span className="font-semibold text-ink tnum">{products.filter((p) => p.flags.length > 0).length}</span>
          </a>
        </li>
      )}
    </ul>
  );
}

function Segmented({ value, onChange }: { value: 'map' | 'table'; onChange: (v: 'map' | 'table') => void }) {
  return (
    <div role="radiogroup" aria-label="Show domains as" className="no-print inline-flex rounded-full border border-line bg-bg p-0.5 text-small font-medium">
      {(['map', 'table'] as const).map((v) => (
        <button
          key={v}
          type="button"
          role="radio"
          aria-checked={value === v}
          onClick={() => onChange(v)}
          data-testid={`domains-view-${v}`}
          className={`cursor-pointer rounded-full px-3.5 py-1 transition-colors duration-150 ${value === v ? 'bg-panel-3 text-ink' : 'text-ink-3 hover:text-ink'}`}
        >
          {v === 'map' ? 'Map' : 'Table'}
        </button>
      ))}
    </div>
  );
}

export default function DomainClusters() {
  const s = useSnapshot();
  const [view, setView] = useState<'map' | 'table'>('map');
  const shown = displayAreas(s, hasProducts(s));
  const group = (id: string, name: string): ClusterGroup => {
    const items = s.products.filter((p) => p.domain === id);
    return {
      id,
      label: name,
      href: href.domain(id),
      meta: plural(items.length, 'data product'),
      items,
    };
  };

  return (
    <section aria-labelledby="domains-h" className="flex min-w-0 flex-col rounded-panel border border-line bg-panel print-break-avoid">
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 pt-6">
        <h2 id="domains-h" className="text-heading font-semibold text-ink">
          Products by domain <span className="ml-1 text-small font-normal text-ink-3">as of {fmtDate(s.asOfDate)}</span>
        </h2>
        <Segmented value={view} onChange={setView} />
      </div>
      <div className={view === 'map' ? 'flex flex-1 flex-col px-6 pt-2 pb-6 print:hidden' : 'hidden'}>
        <div className="flex-1 space-y-2" data-testid="cluster-map">
          {shown.length === 0 && <p className="py-10 text-center text-body text-ink-3">No products in this quarter yet.</p>}
          {shown.map((a) => (
            <div key={a.name || 'other'} data-testid={`map-area-${a.name || 'other'}`}>
              {shown.length > 1 && (
                <div className="flex items-center gap-3 pt-3">
                  {a.name && <h3 className="text-small font-medium whitespace-nowrap text-ink-3">{a.name}</h3>}
                  <span className="h-px flex-1 bg-line" aria-hidden="true" />
                </div>
              )}
              <ClusterMap
                groups={a.domains.map((d) => group(d.id, d.name))}
                ariaLabel={`${a.name || a.domains.map((d) => d.name).join(', ')} data products by domain. Each circle is a product; its ring shows its lifecycle stage, a yellow dot that it needs attention.`}
                testId={`cluster-map-${a.name || 'other'}`}
              />
            </div>
          ))}
        </div>
        <div className="mt-auto border-t border-line pt-4">
          <StageLegend products={s.products} />
        </div>
      </div>
      <div className={view === 'table' ? 'px-3 pt-3 pb-3' : 'hidden print:block print:p-4'}>
        <DomainSummaryTable />
      </div>
    </section>
  );
}
