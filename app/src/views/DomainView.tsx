/* #/domain/:id  One domain: its quarter, its products, technical readiness, speed and adoption, coverage. */

import ClusterMap from '@/components/ClusterMap';
import AttentionList from '@/components/AttentionList';
import ProductTable from '@/components/ProductTable';
import StatStrip, { TechnicalReadiness } from '@/components/StatStrip';
import ReportingStrip from '@/components/Coverage';
import HealthBadge from '@/components/HealthBadge';
import { StageLegend } from '@/components/DomainClusters';
import { DomainRing, headline } from '@/components/QuarterSummary';
import { ArrowLeftIcon } from '@/components/Icons';
import { useSnapshot } from '@/lib/context';
import { plural, quarterLabel } from '@/lib/format';
import { href } from '@/lib/router';
import { healthOf } from '@/lib/quarter';
import { domainById, metricValue } from '@/lib/select';

export default function DomainView({ id }: { id: string }) {
  const s = useSnapshot();
  const d = domainById(s, id);
  if (!d) {
    return (
      <div className="py-16">
        <h1 className="text-title font-semibold text-ink">Unknown domain</h1>
        <p className="mt-2 text-lead text-ink-2">
          There is no domain called <code className="text-ink-3">{id}</code>. <a href={href.exec()}>Back to the executive overview</a>.
        </p>
      </div>
    );
  }
  const h = healthOf(s, id);
  const fc = metricValue(s, 'g4_forecast', id);
  const products = s.products.filter((p) => p.domain === id);
  const groups = [{ id, label: d.name, items: products, meta: plural(products.length, 'data product') }];

  return (
    <div className="space-y-6" data-testid="domain-view">
      <a href={href.exec()} className="inline-flex items-center gap-1.5 text-small text-ink-3 no-underline hover:text-ink">
        <ArrowLeftIcon width={14} height={14} /> Executive overview
      </a>
      <section className="grid gap-px overflow-hidden rounded-panel border border-line bg-line lg:grid-cols-[minmax(0,1fr)_auto]" aria-labelledby="domain-h">
        <div className="flex flex-col items-start gap-6 bg-panel p-6 sm:flex-row sm:items-center sm:gap-8">
          <DomainRing id={id} size={132} />
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 id="domain-h" className="text-title font-semibold text-ink">
                {d.name}
              </h1>
              {h && <HealthBadge status={h.status} size="md" />}
            </div>
            <p className="mt-1 text-body text-ink-3">
              {d.area !== d.name ? `${d.area} · ` : ''}
              {plural(products.length, 'data product')}
            </p>
            {h && (
              <p className="mt-2 text-lead text-pretty text-ink" data-testid="domain-verdict">
                {quarterLabel(s.quarter)}. {(({ lead, expected, target }) => [lead, expected, target].filter(Boolean).join(' '))(headline(h, s.quarter))}
              </p>
            )}
            {h && h.target !== null && (
              <p className="mt-1 text-body text-ink-2">
                <strong className="font-semibold text-ink">{h.certified}</strong> live so far,{' '}
                <a href={href.products({ metric: 'g4_forecast', scope: id })} className="text-ink-2">
                  <strong className="font-semibold text-ink">{fc?.value ?? 0}</strong> on plan
                </a>
                {h.late > 0 && (
                  <>
                    ,{' '}
                    <a href={href.products({ late: id })} className="text-ink-2">
                      <strong className="font-semibold text-ink">{h.late}</strong> late
                    </a>
                  </>
                )}
                .
              </p>
            )}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <section aria-labelledby="products-h" className="min-w-0 rounded-panel border border-line bg-panel">
          <h2 id="products-h" className="px-6 pt-6 text-heading font-semibold text-ink">
            Products
          </h2>
          <div className="px-6 pt-2 pb-6">
            <ClusterMap groups={groups} bubbleR={38} ariaLabel={`${d.name} products. Each circle is a product; its ring shows its lifecycle stage.`} testId="domain-cluster-map" />
            <div className="mt-3 border-t border-line pt-4">
              <StageLegend products={products} domain={id} />
            </div>
          </div>
        </section>
        <AttentionList domain={id} />
      </div>

      <TechnicalReadiness scope={id} />

      <StatStrip scope={id} />

      <ProductTable
        products={products}
        showDomain={false}
        caption={`${d.name} products`}
        title={`All ${d.name} products`}
        action={
          <a href={href.products({ domain: id })} className="text-small">
            Open in the product list
          </a>
        }
      />

      <ReportingStrip scope={id} />
    </div>
  );
}
