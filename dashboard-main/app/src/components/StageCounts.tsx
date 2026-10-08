/* A domain's products per lifecycle stage: a 12px stage mark and its count for each stage present, each
   linking to those products. Sits under the domain name on the executive table. */

import StageMark from '@/components/StageMark';
import { useSnapshot } from '@/lib/context';
import { domainStages } from '@/lib/domainSummary';

export default function StageCounts({ id, className = '' }: { id: string; className?: string }) {
  const s = useSnapshot();
  const name = s.domains.find((d) => d.id === id)?.name ?? id;
  return (
    <span className={`inline-flex items-center gap-x-2.5 ${className}`}>
      {domainStages(s, id).map((c) => (
        <a
          key={c.stage}
          href={c.href}
          className="inline-flex items-center gap-1 no-underline hover:underline"
          title={c.stage}
          aria-label={`${name}, ${c.stage.toLowerCase()}: ${c.count}. Open ${c.count} products`}
          data-testid={c.testId}
          data-count={c.count}
        >
          <StageMark stage={c.stage} size={12} />
          <span className="text-body font-semibold text-ink tnum">{c.count}</span>
        </a>
      ))}
    </span>
  );
}
