/* Platform facts per product, from the GitHub extract and NextData: how far a product has got on the promotion
   path (its platform stage) and what is failing now. Used in place of the governance-gate lifecycle while the
   register has no gate dates: the pipeline still computes the lifecycle, the app just does not show it. */

import type { ProductRow, Snapshot } from '@/types/snapshot';
import { C, type RingKind } from '@/lib/theme';

/** Gate-based views (quarter, lifecycle stages, flags, trend) show only once the register has gate dates. */
export const hasGates = (s: Snapshot) => s.products.some((p) => p.gates.length > 0);

export interface PathStep {
  id: string;
  label: string;
  prod: boolean;
}

const DEFAULT_PATH: PathStep[] = [
  { id: 'iac-apply-d', label: 'Dev', prod: false },
  { id: 'iac-apply-v', label: 'Validation', prod: false },
  { id: 'iac-apply-p', label: 'Production', prod: true },
];

/** The promotion path in order (registry/platform.yaml, via the Delivery section). */
export function promotionPath(s: Snapshot): PathStep[] {
  const path = s.delivery?.envs.filter((e) => e.path).map((e) => ({ id: e.id, label: e.label, prod: e.prod }));
  return path?.length ? path : DEFAULT_PATH;
}

export const envLabel = (s: Snapshot, id: string) => s.delivery?.envs.find((e) => e.id === id)?.label ?? id;

export interface PlatformStage {
  key: string; // 'none' | 'repository' | an environment id
  label: string;
  step: number; // -1 not on GitHub, 0 repository only, 1..steps the furthest environment reached
  steps: number;
  color: string;
  ring?: RingKind;
}

/* The lifecycle's green ramp (theme STAGES), brighter as the product gets closer to production. */
const RAMP = ['#52A077', '#5DB884', '#79D49B', '#A8F0BC'];
const NONE = { key: 'none', label: 'Not on GitHub', color: C.ink3, ring: 'thin' as RingKind };
const REPO = { key: 'repository', label: 'Repository', color: '#7F968B', ring: 'dotted' as RingKind };

/** Every platform stage in order: not on GitHub, repository only, then each step of the path. */
export function platformStages(s: Snapshot): PlatformStage[] {
  const path = promotionPath(s);
  const n = path.length;
  return [
    { ...NONE, step: -1, steps: n },
    { ...REPO, step: 0, steps: n },
    ...path.map((e, i) => ({ key: e.id, label: e.label, step: i + 1, steps: n, color: RAMP[Math.round((i * (RAMP.length - 1)) / Math.max(1, n - 1))] })),
  ];
}

export function platformStage(s: Snapshot, p: ProductRow): PlatformStage {
  const all = platformStages(s);
  if (!p.github) return all[0];
  return all.find((st) => st.key === p.github!.reached) ?? all[1];
}

const RUNTIME_FAILING = new Set(['Failed', 'Unreachable']);

/** Why a product is failing now, one short reason per source; empty when nothing is. */
export function failingReasons(s: Snapshot, p: ProductRow): string[] {
  const out = (p.github?.failingNow ?? []).map((e) => `${envLabel(s, e)} deploys failing`);
  if (p.nextdata && RUNTIME_FAILING.has(p.nextdata.runtime)) out.push(`${p.nextdata.runtime} in NextData`);
  return out;
}

/** Products failing now, the furthest along the path first (a broken production hurts most). */
export function failingProducts(s: Snapshot, domain?: string): ProductRow[] {
  return s.products
    .filter((p) => (!domain || p.domain === domain) && failingReasons(s, p).length > 0)
    .sort((a, b) => platformStage(s, b).step - platformStage(s, a).step || failingReasons(s, b).length - failingReasons(s, a).length || a.name.localeCompare(b.name));
}
