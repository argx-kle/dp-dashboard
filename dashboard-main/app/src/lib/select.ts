/* Pure selectors over the snapshot. The UI never computes a metric; it only looks values up. */

import type { DomainInfo, FlagDefinition, MetricDefinition, MetricValue, ProductRow, ReportingItem, Snapshot } from '@/types/snapshot';
import { SIGNALS, STAGES, type Stage } from '@/lib/theme';
import { healthOf } from '@/lib/quarter';

export const ORG = 'org';

export function metricDef(s: Snapshot, id: string): MetricDefinition | undefined {
  return s.registry.metrics.find((m) => m.id === id);
}

export function metricValue(s: Snapshot, id: string, scope: string): MetricValue | undefined {
  return s.metrics.find((m) => m.id === id && m.scope === scope);
}

/** Data coverage for one kind of input in one scope; undefined when the snapshot has none (its source is absent). */
export function reportingItem(s: Snapshot, kind: string, scope: string): ReportingItem | undefined {
  return s.reporting?.find((r) => r.kind === kind && r.scope === scope);
}

/** The coverage behind a metric, only when it is incomplete. */
export function metricCoverage(s: Snapshot, id: string, scope: string): ReportingItem | undefined {
  const kind = metricDef(s, id)?.coverage;
  const r = kind ? reportingItem(s, kind, scope) : undefined;
  return r && r.of > 0 && r.have < r.of ? r : undefined;
}

export const COVERAGE: Record<string, { label: string; of: string; missing: string }> = {
  gates: { label: 'Gate dates', of: 'active products', missing: 'Products without gate dates' },
  plans: { label: 'Planned GA dates', of: 'products not yet certified', missing: 'Products without a planned GA date' },
  reviewed: { label: 'Reviewed by their owner', of: 'active products', missing: 'Products never reviewed by their owner' },
  dpo: { label: 'Owner named', of: 'active products', missing: 'Products without an owner' },
  usage: { label: 'Usage figures', of: 'live products', missing: 'Live products without a usage figure' },
  consumers: { label: 'First consumer dates', of: 'live products', missing: 'Live products without a first consumer date' },
  validation: { label: 'Validation score', of: 'active products', missing: 'Products without a validation score' },
  nextdata: { label: 'Found in NextData', of: 'active products', missing: 'Products not found in NextData' },
  github: { label: 'GitHub repository', of: 'active products', missing: 'Products without a GitHub repository' },
};

export function domainById(s: Snapshot, id: string): DomainInfo | undefined {
  return s.domains.find((d) => d.id === id);
}

export function domainName(s: Snapshot, id: string): string {
  return domainById(s, id)?.name ?? id;
}

export function flagDef(s: Snapshot, code: string): FlagDefinition | undefined {
  return s.registry.flags.find((f) => f.code === code);
}

export function productByUrn(s: Snapshot, urn: string): ProductRow | undefined {
  return s.products.find((p) => p.urn === urn);
}

export interface Area {
  name: string;
  domains: DomainInfo[];
}

/** Areas (Commercial, TechOps, R&D, G&A) in registry order, each with its domains that pass `keep`. Areas left
    with no domain are dropped, so an empty area never shows. */
export function areas(s: Snapshot, keep: (d: DomainInfo) => boolean = () => true): Area[] {
  const out: Area[] = [];
  for (const d of s.domains) {
    if (!keep(d)) continue;
    const area = d.area ?? 'Commercial';
    const a = out.find((x) => x.name === area);
    if (a) a.domains.push(d);
    else out.push({ name: area, domains: [d] });
  }
  return out;
}

/** Areas for display: an area that is just one domain of the same name (TechOps, R&D, G&A today) needs no
    heading of its own; those domains share one unlabelled group, each still a separate domain. */
export function displayAreas(s: Snapshot, keep: (d: DomainInfo) => boolean = () => true): Area[] {
  const out: Area[] = [];
  const solo: Area[] = [];
  for (const a of areas(s, keep)) (a.domains.length === 1 && a.domains[0].name === a.name ? solo : out).push(a);
  // Separate domains sharing a row; the empty name means "no heading", each cluster names itself.
  if (solo.length) out.push({ name: '', domains: solo.flatMap((a) => a.domains) });
  return out;
}

export const hasProducts = (s: Snapshot) => (d: DomainInfo) => s.products.some((p) => p.domain === d.id);

/** Domains worth a line in the quarter summary: with products, or with a target to meet. */
export const inPlay = (s: Snapshot) => (d: DomainInfo) => hasProducts(s)(d) || (healthOf(s, d.id)?.target ?? 0) > 0;

/** Domains behind this quarter (off track or at risk; below target once closed), most severe first. */
export function domainsNotOnTrack(s: Snapshot): { id: string; status: string }[] {
  const rank: Record<string, number> = { 'off-track': 0, 'below-target': 0, 'at-risk': 1 };
  return s.domains
    .map((d) => ({ id: d.id, status: healthOf(s, d.id)?.status ?? '' }))
    .filter((x) => x.status in rank)
    .sort((a, b) => rank[a.status] - rank[b.status]);
}

/** Products with at least one flag: most severe signal first, then most days overdue, then name. */
export function flaggedProducts(s: Snapshot, domain?: string): ProductRow[] {
  return s.products
    .filter((p) => p.flags.length > 0 && (!domain || p.domain === domain))
    .sort(
      (a, b) =>
        SIGNALS[b.signal].rank - SIGNALS[a.signal].rank ||
        (b.nextGate?.overdueDays ?? -999) - (a.nextGate?.overdueDays ?? -999) ||
        a.name.localeCompare(b.name),
    );
}

export interface Filter {
  products: ProductRow[];
  chips: { key: string; label: string }[];
  title: string;
}

/** Resolve #/products?… parameters into a product list. Every parameter narrows the list. */
export function filterProducts(s: Snapshot, params: URLSearchParams): Filter {
  let products = s.products;
  const chips: { key: string; label: string }[] = [];
  let title = 'All products';

  const metricId = params.get('metric');
  const scope = params.get('scope') ?? ORG;
  if (metricId) {
    const mv = metricValue(s, metricId, scope);
    const def = metricDef(s, metricId);
    const urns = new Set(mv?.urns ?? []);
    products = products.filter((p) => urns.has(p.urn));
    title = `${def?.label ?? metricId}${scope === ORG ? '' : `, ${domainName(s, scope)}`}`;
    chips.push({ key: 'metric', label: def?.shortLabel ?? metricId });
    if (scope !== ORG) chips.push({ key: 'scope', label: domainName(s, scope) });
  }
  const domain = params.get('domain');
  if (domain) {
    products = products.filter((p) => p.domain === domain);
    chips.push({ key: 'domain', label: domainName(s, domain) });
    if (!metricId) title = `${domainName(s, domain)} products`;
  }
  const status = params.get('status');
  if (status) {
    products = products.filter((p) => p.status === status);
    chips.push({ key: 'status', label: status });
    if (!metricId) title = `${status} products`;
  }
  const stage = params.get('stage') as Stage | null;
  if (stage && STAGES[stage]) {
    products = products.filter((p) => p.lifecycle === stage);
    chips.push({ key: 'stage', label: stage });
    if (!metricId && !status) title = `${stage} products`;
  }
  const late = params.get('late');
  if (late) {
    const urns = new Set(healthOf(s, late)?.lateUrns ?? []);
    products = products.filter((p) => urns.has(p.urn));
    chips.push({ key: 'late', label: 'Late, could still go live this quarter' });
    if (late !== ORG) chips.push({ key: 'scope', label: domainName(s, late) });
    if (!metricId) title = `Late products${late === ORG ? '' : `, ${domainName(s, late)}`}`;
  }
  if (params.get('flagged')) {
    const order = new Map(flaggedProducts(s).map((p, i) => [p.urn, i]));
    products = products.filter((p) => order.has(p.urn)).sort((a, b) => order.get(a.urn)! - order.get(b.urn)!);
    chips.push({ key: 'flagged', label: 'Needs attention' });
    if (!metricId) title = 'Products needing attention';
  }
  const flag = params.get('flag');
  if (flag) {
    products = products.filter((p) => p.flags.some((f) => f.code === flag));
    chips.push({ key: 'flag', label: flagDef(s, flag)?.label ?? flag });
    if (!metricId) title = `${flagDef(s, flag)?.label ?? flag} products`;
  }
  const dpo = params.get('dpo');
  if (dpo) {
    products = products.filter((p) => p.dpo === dpo);
    chips.push({ key: 'dpo', label: dpo });
  }
  const missing = params.get('missing');
  if (missing && COVERAGE[missing]) {
    const urns = new Set(reportingItem(s, missing, 'org')?.missing ?? []);
    products = products.filter((p) => urns.has(p.urn));
    chips.push({ key: 'missing', label: COVERAGE[missing].missing });
    if (!metricId) title = COVERAGE[missing].missing;
  }
  const runtime = params.get('runtime');
  if (runtime) {
    products = products.filter((p) => (p.nextdata?.runtime ?? 'Not in NextData') === runtime);
    chips.push({ key: 'runtime', label: runtime });
    if (!metricId) title = runtime === 'Not deployed' || runtime === 'Not in NextData' ? `${runtime} products` : `Products ${runtime.toLowerCase()} in NextData`;
  }
  return { products, chips, title };
}

export const STATUS_ORDER: ProductRow['status'][] = ['In design', 'In build', 'In certification', 'Live', 'Live · in revision', 'Retired', 'Cancelled'];
