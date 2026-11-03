import { describe, expect, it } from 'vitest';
import { matchToken, search, tokens } from '@/lib/search';
import { productFields } from '@/lib/productSearch';
import golden from '../../../tests/fixtures/golden/2026-W41.json';
import type { Snapshot } from '@/types/snapshot';

const s = golden as unknown as Snapshot;
const names = (q: string) => search(s.products, q, (p) => productFields(s, p)).map((h) => h.item.name);

describe('search engine', () => {
  it('ignores word order', () => {
    expect(names('insights market')[0]).toBe('Market Access Insights');
    expect(names('market insights')[0]).toBe('Market Access Insights');
  });
  it('matches letters in order with gaps (fuzzy subsequence)', () => {
    expect(names('pj360')[0]).toBe('Patient Journey 360');
    expect(names('hcpmart')[0]).toBe('HCP Engagement Mart');
  });
  it('searches owners, domains, statuses and flags as well as names', () => {
    expect(names('lukas overdue')).toEqual(['Market Access Insights']);
    expect(names('techops live')).toContain('Manufacturing Batch Genealogy');
    expect(names('no dpo')).toEqual(expect.arrayContaining(['Field Force Activity', 'Study Budget Forecast']));
  });
  it('forgives one typo in longer words', () => {
    expect(names('pharmacovigilence')[0]).toBe('Pharmacovigilance Signals');
    expect(names('genealgoy')[0]).toBe('Manufacturing Batch Genealogy');
  });
  it('returns nothing for nonsense and everything for an empty query', () => {
    expect(names('zzqqxx')).toEqual([]);
    expect(names('   ')).toHaveLength(25);
  });
  it('reports highlight ranges in the name', () => {
    const hit = search(s.products, 'journey', (p) => productFields(s, p))[0];
    expect(hit.item.name.slice(hit.ranges[0][0], hit.ranges[0][1]).toLowerCase()).toBe('journey');
  });
  it('tokenises and normalises accents', () => {
    expect(tokens('  Héadcount,  cost ')).toEqual(['headcount', 'cost']);
    expect(matchToken('ghi', 'abc')).toBeNull();
  });
});
