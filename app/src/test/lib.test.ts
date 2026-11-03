import { describe, expect, it } from 'vitest';
import { href, parseHash } from '@/lib/router';
import { filterProducts, flaggedProducts, metricValue } from '@/lib/select';
import { fmtDate, fmtValue } from '@/lib/format';
import { healthOf, pickQuarter, quarterOptions, quarterSnapshot } from '@/lib/quarter';
import golden from '../../../tests/fixtures/golden/2026-W41.json';
import type { Snapshot } from '@/types/snapshot';

const s = golden as unknown as Snapshot;

describe('router', () => {
  it('parses every route', () => {
    expect(parseHash('').view).toBe('exec');
    const exec = parseHash('#/?q=2026-Q3');
    expect(exec.view).toBe('exec');
    if (exec.view === 'exec') expect(exec.params.get('q')).toBe('2026-Q3');
    expect(parseHash('#/definitions')).toEqual({ view: 'definitions' });
    expect(parseHash('#/domain/market-access')).toEqual({ view: 'domain', id: 'market-access' });
    expect(parseHash('#/products/urn:dp:com:x')).toEqual({ view: 'product', urn: 'urn:dp:com:x' });
    const r = parseHash('#/products?domain=hcp&flag=OVERDUE');
    expect(r.view).toBe('products');
    if (r.view === 'products') expect(r.params.get('flag')).toBe('OVERDUE');
    expect(parseHash('#/nope').view).toBe('notfound');
  });
  it('builds hrefs that round-trip', () => {
    expect(href.products({ metric: 'certified_qtd', scope: 'org' })).toBe('#/products?metric=certified_qtd&scope=org');
    expect(parseHash(href.product('pending:eu-kol-network'))).toEqual({ view: 'product', urn: 'pending:eu-kol-network' });
    expect(href.exec()).toBe('#/');
    expect(href.exec('2026-Q3')).toBe('#/?q=2026-Q3');
  });
});

describe('select', () => {
  it('resolves a metric link to exactly the counted products', () => {
    const mv = metricValue(s, 'cycle_time_g1_g4', 'hcp')!;
    const { products } = filterProducts(s, new URLSearchParams('metric=cycle_time_g1_g4&scope=hcp'));
    expect(products.map((p) => p.urn).sort()).toEqual([...mv.urns!].sort());
    expect(products).toHaveLength(mv.n!);
  });
  it('combines filters', () => {
    const { products, chips } = filterProducts(s, new URLSearchParams('domain=hcp&status=Live'));
    expect(products.every((p) => p.domain === 'hcp' && p.status === 'Live')).toBe(true);
    expect(products.map((p) => p.name).sort()).toEqual(['HCP Engagement Mart', 'Rep Targeting Lists']);
    expect(chips.map((c) => c.label)).toEqual(['HCP', 'Live']);
  });
  it('orders flagged products with coloured flags first', () => {
    const f = flaggedProducts(s);
    expect(f).toHaveLength(7);
    expect(f[0].flags[0].code).toBe('OVERDUE');
    expect(f[1].flags[0].code).toBe('OVERDUE');
    expect(f[2].signal).toBe('orange');
  });
});

describe('format', () => {
  it('formats values by unit', () => {
    expect(fmtValue(0.5455, 'share')).toBe('55%');
    expect(fmtValue(173, 'days')).toBe('173');
    expect(fmtValue(189.5, 'days')).toBe('189.5');
    expect(fmtValue(null, 'count')).toBe('—');
    expect(fmtDate('2026-10-09')).toBe('9 Oct 2026');
  });
});

describe('coverage and platform filters', () => {
  it('opens exactly the products missing an input', () => {
    const { products, title } = filterProducts(s, new URLSearchParams('missing=dpo'));
    const item = s.reporting!.find((r) => r.kind === 'dpo' && r.scope === 'org')!;
    expect(products.map((p) => p.urn).sort()).toEqual([...item.missing].sort());
    expect(title).toBe('Products without an owner');
  });
});

describe('quarter selector', () => {
  it('offers the four trend quarters and falls back to the current one', () => {
    expect(quarterOptions(s)).toEqual(['2026-Q1', '2026-Q2', '2026-Q3', '2026-Q4']);
    expect(pickQuarter(s, '2026-Q3')).toBe('2026-Q3');
    expect(pickQuarter(s, '2025-Q1')).toBe('2026-Q4');
    expect(pickQuarter(s, null)).toBe('2026-Q4');
  });
  it('shows a closed quarter as it stood on its last day', () => {
    const q3 = quarterSnapshot(s, '2026-Q3');
    expect(q3.asOfDate).toBe('2026-09-30');
    expect(metricValue(q3, 'certified_qtd', 'org')!.value).toBe(4);
    expect(healthOf(q3, 'org')!.status).toBe('below-target');
    expect(q3.products.every((p) => p.flags.length === 0)).toBe(true);
    expect(q3.products.find((p) => p.urn === 'urn:dp:com:hcp-engagement-mart')!.lifecycle).toBe('In testing');
    expect(q3.products.length).toBeLessThan(s.products.length);
    expect(quarterSnapshot(s, '2026-Q4')).toBe(s);
  });
  it('filters by stage and by the late products of a scope', () => {
    const { products } = filterProducts(s, new URLSearchParams('stage=In+testing'));
    expect(products.length).toBe(4);
    expect(products.every((p) => p.lifecycle === 'In testing')).toBe(true);
    const late = filterProducts(s, new URLSearchParams('late=org'));
    expect(late.products.map((p) => p.urn).sort()).toEqual([...healthOf(s, 'org')!.lateUrns].sort());
  });
});
