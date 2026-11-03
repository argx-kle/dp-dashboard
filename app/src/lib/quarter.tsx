/* The quarter selector. The pipeline rebuilds every closed trend quarter as it stood on its last day
   (snapshot.quarters); quarterSnapshot() overlays that view on the snapshot, so every selector and component
   below the executive overview reads the chosen quarter without knowing it was chosen. */

import { createContext, useContext } from 'react';
import type { HealthItem, Snapshot } from '@/types/snapshot';

export interface QuarterState {
  /** The quarter on screen, e.g. 2026-Q3. */
  quarter: string;
  /** The quarter the snapshot was built in. */
  current: string;
  /** A closed quarter: nothing is forecast, flags and usage are not known. */
  closed: boolean;
  /** Quarters the selector offers, oldest first. */
  options: string[];
}

export const QuarterContext = createContext<QuarterState | null>(null);

export function useQuarter(): QuarterState | null {
  return useContext(QuarterContext);
}

export function quarterOptions(s: Snapshot): string[] {
  const closed = new Set((s.quarters ?? []).map((q) => q.quarter));
  return Array.from(new Set(s.trend.map((t) => t.quarter)))
    .filter((q) => q === s.quarter || closed.has(q))
    .sort();
}

/** The quarter a #/?q= value asks for, or the snapshot's own quarter when it names none we have. */
export function pickQuarter(s: Snapshot, q: string | null): string {
  return q && quarterOptions(s).includes(q) ? q : s.quarter;
}

const DAY = 86_400_000;

export function quarterSnapshot(s: Snapshot, quarter: string): Snapshot {
  const view = s.quarters?.find((v) => v.quarter === quarter);
  if (quarter === s.quarter || !view) return s;
  const states = new Map(view.products.map((p) => [p.urn, p]));
  const asOf = view.asOfDate;
  const products = s.products
    .filter((p) => states.has(p.urn))
    .map((p) => {
      const st = states.get(p.urn)!;
      return {
        ...p,
        lifecycle: st.lifecycle,
        status: st.status,
        lastGate: st.lastGate,
        firstG4Date: st.firstG4Date,
        gates: p.gates.filter((g) => g.date <= asOf),
        daysInStage: st.lastGate ? Math.max(0, Math.round((Date.parse(asOf) - Date.parse(st.lastGate.date)) / DAY)) : 0,
        nextGate: undefined,
        plannedGA: undefined,
        activeUsers30d: undefined,
        flags: [],
      };
    });
  return { ...s, quarter, asOfDate: asOf, metrics: view.metrics, products, reporting: undefined, changes: [] };
}

export function healthOf(s: Snapshot, scope: string): HealthItem | undefined {
  return s.health?.find((h) => h.quarter === s.quarter && h.scope === scope);
}
