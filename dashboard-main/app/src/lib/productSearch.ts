/* What a product is searchable by, and how much each field counts. */

import type { ProductRow, Snapshot } from '@/types/snapshot';
import type { SearchField } from '@/lib/search';
import { domainName, flagDef } from '@/lib/select';

export function productFields(s: Snapshot, p: ProductRow): SearchField[] {
  return [
    { key: 'name', text: p.name, weight: 3 },
    { key: 'dpo', text: p.dpo ?? 'no dpo', weight: 2 },
    { key: 'domain', text: domainName(s, p.domain), weight: 1.5 },
    { key: 'status', text: p.status, weight: 1 },
    { key: 'stage', text: p.lifecycle, weight: 1.2 },
    { key: 'flags', text: p.flags.map((f) => flagDef(s, f.code)?.label ?? f.code).join(' · '), weight: 1.2 },
    { key: 'urn', text: p.urn, weight: 0.8 },
  ];
}
