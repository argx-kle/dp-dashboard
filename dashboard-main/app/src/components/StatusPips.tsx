/* A product's lifecycle stage in words beside its stage mark; "in revision" when a live product is being
   reworked after a G5. */

import StageMark from '@/components/StageMark';
import { stageText } from '@/lib/theme';
import type { ProductRow } from '@/types/snapshot';

export default function StatusPips({ product, showLabel = true, className = '' }: { product: Pick<ProductRow, 'lifecycle' | 'status'>; showLabel?: boolean; className?: string }) {
  const ended = product.lifecycle === 'Failed / retired';
  const label = ended ? (product.status === 'Cancelled' ? 'Failed (cancelled)' : 'Retired') : product.lifecycle;
  return (
    <span className={`inline-flex items-center gap-2 whitespace-nowrap ${className}`}>
      <StageMark stage={product.lifecycle} />
      {showLabel && (
        <span className="text-small">
          <span style={{ color: stageText(product.lifecycle) }}>{label}</span>
          {product.status === 'Live · in revision' && <span className="text-ink-3"> · in revision</span>}
        </span>
      )}
    </span>
  );
}
