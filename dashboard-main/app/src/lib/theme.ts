/* JS-side colour roles for SVG and motion (motion cannot interpolate CSS variables).
   Values mirror styles/tokens.css. */

import type { ProductRow } from '@/types/snapshot';

export type Signal = ProductRow['signal'];

export const C = {
  bg: '#001A22',
  panel: '#002834',
  panel2: '#06323F',
  panel3: '#0B3C4A',
  line: '#134451',
  lineStrong: '#22596A',
  ink: '#F2FAFC',
  ink2: '#C5DBE2',
  ink3: '#93B2BC',
  onLight: '#001A22',
  clear: '#D2F1FA',
  link: '#74CBE5',
  data1: '#74CBE5',
  data2: '#2397B8',
  track: '#0B3C4A',
};

/* The pipeline's product signal (ProductRow.signal) is no longer drawn: it only ranks the attention list,
   most severe flag first. Its colours are the brand semantic colours that domain health uses. */
export const SIGNALS: Record<Signal, { color: string; rank: number }> = {
  red: { color: '#E55E5E', rank: 4 },
  orange: { color: '#FF7B24', rank: 3 },
  yellow: { color: '#FFE224', rank: 2 },
  unreported: { color: '#93B2BC', rank: 1.5 },
  green: { color: '#76CB5F', rank: 1 },
  grey: { color: '#9FA5AD', rank: 0 },
};

/* Ring shapes for the two stages that are not progress: Ideation (dotted, not started) and Failed / retired
   (red double, ended). */
export type RingKind = 'double' | 'dotted' | 'thin' | 'solid';

/* Lifecycle stages: each stage fills one more quarter of the circle, clockwise from 12 o'clock, on one green
   ramp that gets brighter as the product advances (product-owner choice 2026-10-08, round 5). Colour and fill
   say the same thing, so the mark never relies on colour alone. All text colours pass 4.5:1 on the panel. */
export type Stage = ProductRow['lifecycle'];

export const STAGE_ORDER: Stage[] = ['Ideation', 'In design', 'In development', 'In testing', 'Live', 'Failed / retired'];

export const STAGES: Record<Stage, { color: string; quarters: number; ring?: RingKind; ended?: boolean }> = {
  Ideation: { color: '#7F968B', quarters: 0, ring: 'dotted' },
  'In design': { color: '#52A077', quarters: 1 },
  'In development': { color: '#5DB884', quarters: 2 },
  'In testing': { color: '#79D49B', quarters: 3 },
  Live: { color: '#A8F0BC', quarters: 4 },
  'Failed / retired': { color: '#E55E5E', quarters: 0, ring: 'double', ended: true },
};

/** Products with a flag carry a yellow attention dot on the map. */
export const ATTENTION = '#FFE224';

/** The stage a product enters when it passes each gate. */
export const STAGE_AFTER_GATE: Record<string, Stage> = { G1: 'In design', G2: 'In development', G3: 'In testing', G4: 'Live', G5: 'In design', G6: 'Failed / retired' };

export const GATE_NAMES: Record<string, string> = { G1: 'Intake', G2: 'Contract', G3: 'Build', G4: 'Certify', G5: 'Revise', G6: 'Retire' };

/** "G4 Certify" */
export const gateLabel = (gate: string) => `${gate} ${GATE_NAMES[gate] ?? ''}`.trim();

/** Stages shown in legends and filters: every stage up to Live, plus Failed / retired while some product has it. */
export const stagesShown = (products: { lifecycle: Stage }[]): Stage[] =>
  STAGE_ORDER.filter((st) => st !== 'Failed / retired' || products.some((p) => p.lifecycle === st));

/* Domain health, a forecast for the current quarter (pace against what was expected by today) and a result
   for a closed one. Computed by the pipeline (HealthItem). Each has an icon and a colour, always with its word. */
export type Health = 'ahead' | 'on-track' | 'at-risk' | 'off-track' | 'above-target' | 'met-target' | 'below-target' | 'no-target';
export type HealthIcon = 'trend-up' | 'check' | 'alert' | 'stop' | 'trend-down' | 'minus';

export const HEALTH: Record<Health, { label: string; color: string; icon: HealthIcon; rank: number }> = {
  'off-track': { label: 'Off track', color: SIGNALS.red.color, icon: 'stop', rank: 4 },
  'below-target': { label: 'Below target', color: SIGNALS.red.color, icon: 'trend-down', rank: 4 },
  'at-risk': { label: 'Behind', color: SIGNALS.orange.color, icon: 'alert', rank: 3 },
  'on-track': { label: 'On track', color: SIGNALS.green.color, icon: 'check', rank: 2 },
  'met-target': { label: 'Met target', color: SIGNALS.green.color, icon: 'check', rank: 2 },
  ahead: { label: 'Ahead', color: SIGNALS.green.color, icon: 'trend-up', rank: 1 },
  'above-target': { label: 'Above target', color: SIGNALS.green.color, icon: 'trend-up', rank: 1 },
  'no-target': { label: 'No target', color: C.ink3, icon: 'minus', rank: 0 },
};

/** The board's columns, most urgent first. */
export const HEALTH_COLUMNS: Record<'open' | 'closed', Health[]> = {
  open: ['off-track', 'at-risk', 'on-track', 'ahead'],
  closed: ['below-target', 'met-target', 'above-target'],
};

/** A stage's colour for text: the ring colour, with Failed / retired's red lightened so small words stay readable. */
export const stageText = (stage: Stage) => (stage === 'Failed / retired' ? 'color-mix(in srgb, #E55E5E 70%, #F2FAFC)' : STAGES[stage].color);

/** A flag's colour: the signal the registry gives it (red, orange or yellow). */
export const flagColor = (signal: string | undefined) => (signal && signal in SIGNALS ? SIGNALS[signal as Signal].color : C.ink3);
