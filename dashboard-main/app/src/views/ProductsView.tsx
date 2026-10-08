/* #/products?…  Product list: search, filters, and a table grouped by domain. Filters and the
   search query live in the URL, so every number on the dashboard can link here. */

import { useEffect, useMemo, useRef, useState } from 'react';
import ProductTable from '@/components/ProductTable';
import StageMark from '@/components/StageMark';
import { CloseIcon, SearchIcon } from '@/components/Icons';
import { useSnapshot } from '@/lib/context';
import { href } from '@/lib/router';
import { search, type Range } from '@/lib/search';
import { productFields } from '@/lib/productSearch';
import { areas, filterProducts, hasProducts } from '@/lib/select';
import { stagesShown } from '@/lib/theme';

const RUNTIMES = ['Started', 'Failed', 'Unreachable', 'Not deployed', 'Not in NextData'];

function Pill({ to, on, children }: { to: string; on: boolean; children: React.ReactNode }) {
  return (
    <a
      href={to}
      aria-current={on ? 'true' : undefined}
      className={`inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-small no-underline transition-colors duration-150 ${on ? 'border-line-strong bg-panel-3 text-ink' : 'border-line text-ink-3 hover:border-line-strong hover:text-ink'}`}
    >
      {children}
    </a>
  );
}

export default function ProductsView({ params }: { params: URLSearchParams }) {
  const s = useSnapshot();
  const { products: filtered, chips, title } = filterProducts(s, params);
  const domain = params.get('domain') ?? undefined;
  const status = params.get('status') ?? undefined;
  const stage = params.get('stage') ?? undefined;
  const runtime = params.get('runtime') ?? undefined;
  const runtimes = RUNTIMES.filter((r) => s.products.some((p) => (p.nextdata?.runtime ?? 'Not in NextData') === r));
  const fromMetric = params.has('metric') || params.has('flagged');
  const [query, setQuery] = useState(params.get('q') ?? '');
  const input = useRef<HTMLInputElement>(null);
  const keep = (over: Record<string, string | undefined>) => href.products({ domain, status, stage, runtime, q: query || undefined, ...over });

  // Keep the query in the URL without adding history entries.
  useEffect(() => {
    const next = new URLSearchParams(params);
    if (query) next.set('q', query);
    else next.delete('q');
    const qs = next.toString();
    window.history.replaceState(null, '', qs ? `#/products?${qs}` : '#/products');
  }, [query, params]);

  // "/" focuses search from anywhere on the page.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName) && !t.isContentEditable) {
        e.preventDefault();
        input.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const { rows, highlight } = useMemo(() => {
    if (!query.trim()) return { rows: filtered, highlight: undefined };
    const hits = search(filtered, query, (p) => productFields(s, p));
    return { rows: hits.map((h) => h.item), highlight: new Map<string, Range[]>(hits.map((h) => [h.item.urn, h.ranges])) };
  }, [filtered, query, s]);
  const searching = query.trim().length > 0;

  return (
    <div data-testid="products-view">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-title font-semibold text-ink">{title}</h1>
          <p className="mt-1 text-lead text-ink-3 tnum" data-testid="products-count" data-count={rows.length}>
            {rows.length} {rows.length === 1 ? 'product' : 'products'}
            {searching ? ` match "${query.trim()}"` : fromMetric ? ' behind this number' : ''}
          </p>
        </div>
        {(chips.length > 0 || searching) && (
          <a href={href.products()} className="text-small" onClick={() => setQuery('')}>
            Clear filters
          </a>
        )}
      </div>

      <div className="no-print mt-6 space-y-4">
        <label className="relative block max-w-[640px]">
          <span className="sr-only">Search products</span>
          <SearchIcon width={18} height={18} className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-ink-3" />
          <input
            ref={input}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Escape' && setQuery('')}
            placeholder="Search by product, owner, domain, stage or flag, in any order"
            className="h-12 w-full rounded-control border border-line-strong bg-panel pr-12 pl-11 text-lead text-ink placeholder:text-ink-3 focus:border-clear focus:outline-none [&::-webkit-search-cancel-button]:hidden"
            data-testid="product-search"
            autoComplete="off"
            spellCheck={false}
          />
          {query ? (
            <button type="button" onClick={() => setQuery('')} aria-label="Clear search" className="absolute top-1/2 right-3 flex h-7 w-7 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full text-ink-3 hover:bg-panel-3 hover:text-ink">
              <CloseIcon width={16} height={16} />
            </button>
          ) : (
            <kbd className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 rounded-md border border-line-strong px-1.5 text-small text-ink-3">/</kbd>
          )}
        </label>

        {!fromMetric && (
          <div className="space-y-3" role="group" aria-label="Filters">
            <div className="flex flex-wrap items-center gap-2">
              <span className="w-16 text-small text-ink-3">Domain</span>
              <Pill to={keep({ domain: undefined })} on={!domain}>
                All
              </Pill>
              {areas(s, hasProducts(s))
                .flatMap((a) => a.domains)
                .map((d) => (
                  <Pill key={d.id} to={keep({ domain: d.id })} on={domain === d.id}>
                    {d.name}
                  </Pill>
                ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="w-16 text-small text-ink-3">Stage</span>
              <Pill to={keep({ stage: undefined, status: undefined })} on={!stage && !status}>
                All
              </Pill>
              {stagesShown(s.products).map((st) => (
                <Pill key={st} to={keep({ stage: st, status: undefined })} on={stage === st}>
                  <StageMark stage={st} size={14} />
                  {st}
                </Pill>
              ))}
            </div>
            {s.products.some((p) => p.nextdata) && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="w-16 text-small text-ink-3">NextData</span>
                <Pill to={keep({ runtime: undefined })} on={!runtime}>
                  All
                </Pill>
                {runtimes.map((r) => (
                  <Pill key={r} to={keep({ runtime: r })} on={runtime === r}>
                    {r}
                  </Pill>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-6">
        <ProductTable
          products={rows}
          groupByDomain
          forceOpen={searching}
          highlight={highlight}
          caption={title}
          empty={
            searching ? (
              <>
                Nothing matches "{query.trim()}".{' '}
                <button type="button" className="cursor-pointer text-link underline" onClick={() => setQuery('')}>
                  Clear search
                </button>
              </>
            ) : undefined
          }
        />
      </div>
    </div>
  );
}
