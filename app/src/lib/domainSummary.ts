/* The summary figures for one domain, shared by the executive table and the Products page.
   Every figure is a snapshot value and links to the list of products behind it. */

import type { ProductRow, Snapshot } from '@/types/snapshot';
import { fmtValue } from '@/lib/format';
import { href } from '@/lib/router';
import { metricValue } from '@/lib/select';
import { STAGE_ORDER } from '@/lib/theme';

export interface SummaryFigure {
  key: string;
  value: string;
  /** Muted suffix shown after the value, e.g. "of 3". */
  suffix?: string;
  label: string;
  href: string;
  testId: string;
  count: number;
}

export function domainSummary(s: Snapshot, id: string): SummaryFigure[] {
  const products = s.products.filter((p) => p.domain === id);
  const m = (metric: string) => metricValue(s, metric, id);
  const fig = (metric: string, label: string, suffix?: string): SummaryFigure => {
    const mv = m(metric);
    return {
      key: metric,
      value: mv?.value === null || mv === undefined ? '–' : fmtValue(mv.value, metric === 'cycle_time_g1_g4' ? 'days' : 'count'),
      suffix,
      label,
      href: href.products({ metric, scope: id }),
      testId: `dh-${metric}-${id}`,
      count: mv?.urns?.length ?? 0,
    };
  };
  const cert = m('certified_qtd');
  return [
    { key: 'products', value: String(products.length), label: 'products', href: href.products({ domain: id }), testId: `dh-products-${id}`, count: products.length },
    fig('live_count', 'live'),
    fig('pipeline_count', 'in pipeline'),
    fig('certified_qtd', 'certified', `of ${cert?.target ?? '–'}`),
    fig('cycle_time_g1_g4', 'median time to production', m('cycle_time_g1_g4')?.value === null ? undefined : 'days'),
    fig('certified_unused', 'unused'),
  ];
}

export interface StageCount {
  stage: ProductRow['lifecycle'];
  count: number;
  href: string;
  testId: string;
}

/** How many of a domain's products are in each lifecycle stage, in stage order; stages with none are left out. */
export function domainStages(s: Snapshot, id: string): StageCount[] {
  const products = s.products.filter((p) => p.domain === id);
  return STAGE_ORDER.map((stage) => ({
    stage,
    count: products.filter((p) => p.lifecycle === stage).length,
    href: href.products({ domain: id, stage }),
    testId: `dh-stage-${stage.replace(/[^a-z]+/gi, '-').toLowerCase()}-${id}`,
  })).filter((c) => c.count > 0);
}
