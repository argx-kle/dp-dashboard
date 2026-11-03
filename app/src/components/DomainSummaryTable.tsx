/* Executive "Table" view: one summary row per domain, numbers first, each row opening with its
   disclosure triangle to the domain's products. Every number links to the products behind it. */

import { Fragment, useState } from 'react';
import ProductTable from '@/components/ProductTable';
import StageCounts from '@/components/StageCounts';
import { TriangleIcon } from '@/components/Icons';
import { useSnapshot } from '@/lib/context';
import { domainSummary } from '@/lib/domainSummary';
import { href } from '@/lib/router';
import { inPlay } from '@/lib/select';

const HEADERS = ['Products', 'Live', 'In pipeline', 'Certified', 'Time to production', 'Unused'];

export default function DomainSummaryTable() {
  const s = useSnapshot();
  const domains = s.domains.filter(inPlay(s));
  const [open, setOpen] = useState<Set<string>>(new Set());
  const allOpen = open.size === domains.length;
  const toggle = (id: string) => setOpen((o) => (o.has(id) ? new Set([...o].filter((x) => x !== id)) : new Set([...o, id])));

  return (
    <div>
      <div className="flex justify-end px-3 pb-2">
        <button type="button" onClick={() => setOpen(allOpen ? new Set() : new Set(domains.map((d) => d.id)))} className="cursor-pointer text-small text-link hover:text-ink" data-testid="toggle-all-domains">
          {allOpen ? 'Collapse all' : 'Expand all'}
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-separate border-spacing-0 text-body" aria-label="Domain summary">
          <thead>
            <tr>
              <th scope="col" className="border-b border-line px-4 py-3 text-left text-small font-medium text-ink-3">
                Domain
              </th>
              {HEADERS.map((h) => (
                <th key={h} scope="col" className="border-b border-line px-3 py-3 text-right text-small font-medium whitespace-nowrap text-ink-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {domains.map((d) => {
              const isOpen = open.has(d.id);
              const figures = domainSummary(s, d.id);
              const products = s.products.filter((p) => p.domain === d.id);
              return (
                <Fragment key={d.id}>
                  <tr className={`transition-colors duration-150 ${isOpen ? 'bg-panel-2' : 'hover:bg-panel-2'}`}>
                    <th scope="row" className="border-b border-line py-3.5 pr-4 pl-2 text-left font-normal">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => toggle(d.id)}
                          aria-expanded={isOpen}
                          aria-controls={`domain-rows-${d.id}`}
                          aria-label={`${isOpen ? 'Collapse' : 'Expand'} ${d.name} products`}
                          className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-control text-ink-2 hover:bg-panel-3 hover:text-ink"
                          data-testid={`domain-toggle-${d.id}`}
                        >
                          <TriangleIcon className={`transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`} />
                        </button>
                        <div>
                          <div className="flex items-center gap-2 whitespace-nowrap">
                            <a href={href.domain(d.id)} className="text-lead font-semibold text-ink no-underline hover:text-clear hover:underline" data-testid={`domain-link-${d.id}`}>
                              {d.name}
                            </a>
                          </div>
                          {!isOpen && <StageCounts id={d.id} className="mt-1" />}
                        </div>
                      </div>
                    </th>
                    {figures.map((f) => (
                      <td key={f.key} className="border-b border-line px-3 py-3.5 text-right whitespace-nowrap tnum">
                        {isOpen ? null : f.value === '–' ? (
                          <span className="text-lead text-ink-3">–</span>
                        ) : (
                          <a href={f.href} className="no-underline hover:underline" data-testid={f.testId} data-count={f.count} aria-label={`${d.name}, ${f.label}: ${f.value}${f.suffix ? ' ' + f.suffix : ''}. Open ${f.count} products`}>
                            <span className="text-lead font-semibold text-ink">{f.value}</span>
                            {f.suffix && <span className="text-small text-ink-3"> {f.suffix}</span>}
                          </a>
                        )}
                      </td>
                    ))}
                  </tr>
                  {isOpen && (
                    <tr id={`domain-rows-${d.id}`} data-testid={`domain-rows-${d.id}`}>
                      <td colSpan={HEADERS.length + 1} className="border-b border-line bg-bg/40 px-4 pt-1 pb-4">
                        <ProductTable products={products} compact caption={`${d.name} products`} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
