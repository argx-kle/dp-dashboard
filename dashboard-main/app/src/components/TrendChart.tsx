/* Delivery trend, by quarter or by week, in the same language as the rings: certified solid, the current
   quarter's on-plan forecast faint on top, the shortfall to target outlined in red, a target tick.

   Quarters: certified per quarter for the last four; click a quarter to open it.
   Weeks: the chosen quarter week by week, cumulative, against a dashed target pace from zero to the target at
   the quarter end, so velocity shows as the slope and a recovery shows as the columns climbing back over the
   pace. Switching units unfolds the quarter's bar into its weeks (and folds them back): one y scale serves
   both, so the bar's silhouette is exactly the last week's column. Hover or focus a column for the breakdown
   by domain; a table carries the same numbers. */

import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { useSnapshot } from '@/lib/context';
import { fmtShort, quarterLabel } from '@/lib/format';
import { useQuarter } from '@/lib/quarter';
import { href } from '@/lib/router';
import { domainName } from '@/lib/select';
import { C, HEALTH, SIGNALS, type Health } from '@/lib/theme';
import { useWidth } from '@/lib/useWidth';
import type { Snapshot } from '@/types/snapshot';

type Unit = 'quarters' | 'weeks';

const PLOT = 220;
const PAD = { top: 28, right: 24, bottom: 40, left: 36 };
const H = PLOT + PAD.top + PAD.bottom;
const EASE = [0.16, 1, 0.3, 1] as const;
const DAY = 86_400_000;

interface Week {
  week: string;
  label: string;
  start: string;
  end: string;
  /** Cumulative certified at the end of the week; null for a week still ahead. */
  value: number | null;
  byDomain: Record<string, number>;
}

const iso = (t: number) => new Date(t).toISOString().slice(0, 10);

function isoWeek(t: number): string {
  const d = new Date(t);
  const day = (d.getUTCDay() + 6) % 7;
  const thursday = t - day * DAY + 3 * DAY;
  const year = new Date(thursday).getUTCFullYear();
  const jan4 = Date.UTC(year, 0, 4);
  const week1 = jan4 - ((new Date(jan4).getUTCDay() + 6) % 7) * DAY;
  return `${year}-W${String(1 + Math.round((thursday - 3 * DAY - week1) / (7 * DAY))).padStart(2, '0')}`;
}

/** Every ISO week overlapping the quarter, with the pipeline's cumulative count where the week has happened. */
function weeksOf(s: Snapshot, quarter: string): Week[] {
  const [y, q] = [Number(quarter.slice(0, 4)), Number(quarter.slice(-1))];
  const qStart = Date.UTC(y, 3 * (q - 1), 1);
  const qEnd = Date.UTC(q === 4 ? y + 1 : y, q === 4 ? 0 : 3 * q, 1) - DAY;
  const points = new Map((s.weekly ?? []).filter((w) => w.quarter === quarter).map((w) => [w.week, w]));
  const out: Week[] = [];
  for (let monday = qStart - ((new Date(qStart).getUTCDay() + 6) % 7) * DAY; monday <= qEnd; monday += 7 * DAY) {
    const id = isoWeek(monday);
    const p = points.get(id);
    out.push({ week: id, label: `W${Number(id.slice(-2))}`, start: iso(Math.max(monday, qStart)), end: iso(Math.min(monday + 6 * DAY, qEnd)), value: p ? p.certified : null, byDomain: p?.byDomain ?? {} });
  }
  return out;
}

function UnitSwitch({ value, onChange }: { value: Unit; onChange: (u: Unit) => void }) {
  const reduced = useReducedMotion();
  return (
    <div role="radiogroup" aria-label="Show the trend by" className="no-print inline-flex rounded-full border border-line bg-bg p-0.5 text-small font-medium">
      {(['quarters', 'weeks'] as const).map((u) => (
        <button
          key={u}
          type="button"
          role="radio"
          aria-checked={value === u}
          onClick={() => onChange(u)}
          data-testid={`trend-unit-${u}`}
          className={`relative cursor-pointer rounded-full px-3.5 py-1 transition-colors duration-150 ${value === u ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}
        >
          {value === u && <motion.span layoutId="trend-unit-pill" className="absolute inset-0 rounded-full bg-panel-3" transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 420, damping: 36 }} aria-hidden="true" />}
          <span className="relative">{u === 'quarters' ? 'Quarters' : 'Weeks'}</span>
        </button>
      ))}
    </div>
  );
}

function Key({ swatch, children }: { swatch: React.ReactNode; children: React.ReactNode }) {
  return (
    <li className="inline-flex items-center gap-2">
      {swatch}
      {children}
    </li>
  );
}

export default function TrendChart() {
  const s = useSnapshot();
  const qs = useQuarter();
  const reduced = useReducedMotion() ?? false;
  const [unit, setUnit] = useState<Unit>('quarters');
  const [hover, setHover] = useState<number | null>(null);
  const [wrapRef, W] = useWidth<HTMLDivElement>(760);
  // On first paint every bar grows from the axis; after a switch back from weeks, the selected quarter's bar
  // reappears where its weeks fold into it.
  const first = useRef(true);
  useEffect(() => {
    first.current = false;
  }, []);

  const current = qs?.current ?? s.quarter;
  const selected = s.quarter;
  const quarters = Array.from(new Set(s.trend.map((t) => t.quarter))).sort();
  const totals = quarters.map((q) => s.trend.filter((t) => t.quarter === q).reduce((a, t) => a + t.certified, 0));
  const targets = quarters.map((q) => {
    const ts = s.trend.filter((t) => t.quarter === q && t.target !== null);
    return ts.length ? ts.reduce((a, t) => a + (t.target ?? 0), 0) : null;
  });
  const cur = quarters.indexOf(current);
  const sel = Math.max(0, quarters.indexOf(selected));
  const forecast = s.health?.find((h) => h.quarter === current && h.scope === 'org')?.forecast ?? 0;
  const curShort = cur >= 0 && targets[cur] !== null ? Math.max(0, targets[cur]! - totals[cur] - forecast) : 0;

  // One y scale for both units, so a quarter's bar and its last week's column are the same height.
  const yMax = Math.max(2, ...totals.map((t, i) => t + (i === cur ? forecast : 0)), ...targets.map((t) => t ?? 0));
  const step = yMax <= 6 ? 1 : yMax <= 12 ? 2 : 5;
  const top = Math.ceil(yMax / step) * step;
  const innerW = W - PAD.left - PAD.right;
  const y = (v: number) => PAD.top + PLOT - (v / top) * PLOT;
  const ticks = Array.from({ length: top / step + 1 }, (_, i) => i * step);

  // Quarters geometry.
  const qSlot = innerW / quarters.length;
  const BAR = Math.max(28, Math.min(60, qSlot * 0.36));
  const qx = (i: number) => PAD.left + qSlot * i + qSlot / 2;

  // Weeks geometry, for the selected quarter.
  const weeks = weeksOf(s, selected);
  const wSlot = innerW / weeks.length;
  const WBAR = Math.max(10, Math.min(36, wSlot * 0.6));
  const wx = (j: number) => PAD.left + wSlot * j + wSlot / 2;
  const selTarget = targets[sel];
  const isCurrent = selected === current;
  const lastActual = weeks.reduce((a, w, j) => (w.value !== null ? j : a), -1);
  // Expected by the end of each week: target x share of the quarter elapsed, the same formula as the verdict.
  const qStart = Date.parse(weeks[0].start);
  const qDays = (Date.parse(weeks[weeks.length - 1].end) - qStart) / DAY + 1;
  const pace = (j: number) => (selTarget ?? 0) * Math.min(1, ((Date.parse(weeks[j].end) - qStart) / DAY + 1) / qDays);
  const health = (q: string) => s.health?.find((h) => h.quarter === q && h.scope === 'org');
  const healthColor = (q: string) => {
    const h = health(q);
    return h && h.status !== 'no-target' ? HEALTH[h.status as Health].color : C.clear;
  };
  const showEvery = wSlot >= 44 ? 1 : 2;

  const bar = (x: number, w: number, from: number, to: number) => ({ x: x - w / 2, y: y(to), width: w, height: Math.max(0, y(from) - y(to)) });
  const fade = reduced ? { duration: 0 } : { duration: 0.25 };

  const openQuarter = (q: string) => {
    window.location.hash = href.exec(q === current ? undefined : q);
  };

  const ariaWeeks = weeks.map((w, j) => `${w.label}: ${w.value === null ? 'ahead' : `${w.value} certified`}${selTarget !== null ? `, pace ${Math.round(pace(j) * 10) / 10}` : ''}`).join('; ');
  const ariaQuarters = quarters.map((q, i) => `${quarterLabel(q)}: ${totals[i]} certified${i === cur ? `, ${forecast} forecast` : ''}${targets[i] !== null ? `, target ${targets[i]}` : ''}`).join('; ');

  return (
    <section aria-labelledby="trend-h" className="rounded-panel border border-line bg-panel p-6 print-break-avoid" data-testid="trend-chart" data-unit={unit}>
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <h2 id="trend-h" className="text-heading font-semibold text-ink">
            {unit === 'quarters' ? 'Certified per quarter' : `${quarterLabel(selected)}, week by week`}
          </h2>
          <UnitSwitch value={unit} onChange={(u) => { setHover(null); setUnit(u); }} />
        </div>
        <ul className="m-0 flex list-none flex-wrap items-center gap-x-5 gap-y-2 p-0 text-small text-ink-2" aria-label="Legend">
          <Key swatch={<span className="inline-block h-3 w-3 rounded-[3px] bg-data-1" aria-hidden="true" />}>{unit === 'weeks' ? 'Certified so far' : 'Certified'}</Key>
          {(unit === 'quarters' || isCurrent) && forecast > 0 && <Key swatch={<span className="inline-block h-3 w-3 rounded-[3px] bg-data-2/50" aria-hidden="true" />}>{unit === 'weeks' ? 'On plan by quarter end' : 'Forecast this quarter'}</Key>}
          {(unit === 'quarters' || isCurrent) && curShort > 0 && <Key swatch={<span className="inline-block h-3 w-3 rounded-[3px] border-[1.5px] border-dashed border-sig-red" aria-hidden="true" />}>Short of target</Key>}
          {unit === 'weeks' && selTarget !== null && (
            <Key swatch={<svg width="18" height="10" aria-hidden="true"><path d="M1 9 L17 1" stroke={C.ink2} strokeWidth="1.5" strokeDasharray="3 3" /></svg>}>Target pace</Key>
          )}
          <Key swatch={<span className="inline-block h-0.5 w-4 rounded bg-ink-2" aria-hidden="true" />}>Target</Key>
        </ul>
      </div>
      <div ref={wrapRef} className="relative mt-5">
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="block" role="group" aria-label={unit === 'weeks' ? `${quarterLabel(selected)} by week, cumulative: ${ariaWeeks}` : ariaQuarters}>
          <defs>
            <clipPath id="trend-plot">
              <rect x={0} y={0} width={W} height={y(0)} />
            </clipPath>
          </defs>
          {ticks.map((v) => (
            <g key={v}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke={v === 0 ? C.lineStrong : C.line} strokeWidth={1} />
              <text x={PAD.left - 10} y={y(v) + 4} textAnchor="end" fontSize={13} fill={C.ink3} style={{ fontVariantNumeric: 'tabular-nums' }}>
                {v}
              </text>
            </g>
          ))}

          <g clipPath="url(#trend-plot)">
            {/* Quarters: every quarter's bar. In weeks mode the other quarters fall away and the selected one
                hands over to its weeks. */}
            <AnimatePresence initial={!reduced}>
              {unit === 'quarters' &&
                quarters.map((q, i) => {
                  const g = bar(qx(i), BAR, 0, totals[i]);
                  const dim = hover !== null && hover !== i ? 0.45 : 1;
                  return (
                    <motion.rect
                      key={`q-${q}`}
                      rx={4}
                      fill={C.data1}
                      initial={reduced ? false : i === sel && !first.current ? { ...g, opacity: 0 } : { ...g, y: y(0), height: 0, opacity: 1 }}
                      animate={{ ...g, height: g.height + (totals[i] > 0 ? 4 : 0), opacity: dim * (i === sel ? 1 : 0.55) }}
                      exit={i === sel ? { opacity: 0, transition: { duration: 0.15, delay: 0.05 } } : { y: y(0), height: 0, opacity: 0, transition: fade }}
                      transition={reduced ? { duration: 0 } : { duration: 0.6, delay: i === sel && !first.current ? 0.45 : 0.05 + i * 0.06, ease: EASE }}
                    />
                  );
                })}
            </AnimatePresence>

            {/* Weeks: each column unfolds out of the quarter's bar to its own slot and height. */}
            <AnimatePresence initial={false}>
              {unit === 'weeks' &&
                weeks.map((w, j) => {
                  if (w.value === null) return null;
                  const g = bar(wx(j), WBAR, 0, w.value);
                  const from = bar(qx(sel), BAR, 0, totals[sel]);
                  const dim = hover !== null && hover !== j ? 0.45 : 1;
                  return (
                    <motion.rect
                      key={`w-${selected}-${w.week}`}
                      rx={3}
                      fill={C.data1}
                      initial={reduced ? false : { ...from, height: from.height + 4, opacity: 0.9 }}
                      animate={{ ...g, height: g.height + (w.value > 0 ? 3 : 0), opacity: dim }}
                      exit={reduced ? { opacity: 0 } : { ...from, height: from.height + 4, opacity: 0, transition: { duration: 0.45, ease: EASE } }}
                      transition={reduced ? { duration: 0 } : { duration: 0.75, delay: 0.02 * j, ease: EASE }}
                    />
                  );
                })}
            </AnimatePresence>
          </g>

          {/* Quarters: forecast, shortfall, targets, values, labels. */}
          <AnimatePresence initial={!reduced}>
            {unit === 'quarters' && (
              <motion.g key="q-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { duration: 0.3, delay: reduced ? 0 : 0.35 } }} exit={{ opacity: 0, transition: fade }}>
                {quarters.map((q, i) => {
                  const isCur = i === cur;
                  const t = targets[i];
                  const stackTop = totals[i] + (isCur ? forecast : 0);
                  const short = isCur ? curShort : 0;
                  const dim = hover !== null && hover !== i ? 0.45 : 1;
                  return (
                    <g key={q} opacity={dim} style={{ transition: 'opacity 150ms' }}>
                      {isCur && forecast > 0 && <rect {...bar(qx(i), BAR, totals[i], stackTop)} rx={4} fill={C.data2} fillOpacity={0.5} />}
                      {short > 0 && (
                        <rect x={qx(i) - BAR / 2 + 0.75} y={y(stackTop + short) + 0.75} width={BAR - 1.5} height={y(stackTop) - y(stackTop + short) - 1.5} rx={4} fill="none" stroke={SIGNALS.red.color} strokeOpacity={0.85} strokeWidth={1.5} strokeDasharray="4 3" />
                      )}
                      {t !== null && <line x1={qx(i) - BAR / 2 - 8} x2={qx(i) + BAR / 2 + 8} y1={y(t)} y2={y(t)} stroke={C.ink2} strokeWidth={2} strokeLinecap="round" />}
                      {t !== null && (
                        <text x={qx(i) + BAR / 2 + 14} y={y(t) + 4} fontSize={13} fill={C.ink3}>
                          {qSlot >= 150 ? `target ${t}` : t}
                        </text>
                      )}
                      {totals[i] > 0 && y(0) - y(totals[i]) >= 22 ? (
                        <text x={qx(i)} y={y(totals[i]) + 17} textAnchor="middle" fontSize={15} fontWeight={600} fill={C.onLight}>
                          {totals[i]}
                        </text>
                      ) : (
                        <text x={qx(i)} y={y(totals[i]) - 8} textAnchor="middle" fontSize={15} fontWeight={600} fill={C.ink}>
                          {totals[i]}
                        </text>
                      )}
                      {isCur && forecast > 0 && y(totals[i]) - y(stackTop) >= 22 && (
                        <text x={qx(i)} y={y(stackTop) + 17} textAnchor="middle" fontSize={13} fontWeight={600} fill={C.ink}>
                          +{forecast}
                        </text>
                      )}
                      <text x={qx(i)} y={H - PAD.bottom + 24} textAnchor="middle" fontSize={13} fill={i === sel ? C.ink : C.ink3} fontWeight={i === sel ? 600 : 400}>
                        {qSlot < 120 ? `Q${q.slice(-1)}` : quarterLabel(q)}
                        {isCur && qSlot >= 120 ? ', to date' : ''}
                      </text>
                      {i === sel && <line x1={qx(i) - 14} x2={qx(i) + 14} y1={H - PAD.bottom + 32} y2={H - PAD.bottom + 32} stroke={healthColor(q)} strokeWidth={3} strokeLinecap="round" />}
                    </g>
                  );
                })}
              </motion.g>
            )}
          </AnimatePresence>

          {/* Weeks: target pace, target, what is still on plan, values, labels. */}
          <AnimatePresence initial={!reduced}>
            {unit === 'weeks' && (
              <motion.g key={`w-overlay-${selected}`} initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { duration: 0.3, delay: reduced ? 0 : 0.45 } }} exit={{ opacity: 0, transition: fade }}>
                {selTarget !== null && (
                  <>
                    {/* Drawn left to right by a widening clip, so the dashes keep their rhythm (pathLength would replace them). */}
                    <clipPath id="trend-pace">
                      <motion.rect x={PAD.left} y={0} height={H} initial={reduced ? false : { width: 0 }} animate={{ width: innerW }} transition={reduced ? { duration: 0 } : { duration: 0.9, delay: 0.5, ease: EASE }} />
                    </clipPath>
                    <path d={`M ${PAD.left} ${y(0)} ${weeks.map((_, j) => `L ${wx(j)} ${y(pace(j))}`).join(' ')}`} fill="none" stroke={C.ink2} strokeWidth={1.5} strokeDasharray="5 5" clipPath="url(#trend-pace)" />
                    <line x1={PAD.left} x2={W - PAD.right} y1={y(selTarget)} y2={y(selTarget)} stroke={C.ink2} strokeWidth={1} strokeOpacity={0.4} />
                    <text x={W - PAD.right} y={y(selTarget) - 8} textAnchor="end" fontSize={13} fill={C.ink3}>
                      target {selTarget}
                    </text>
                  </>
                )}
                {isCurrent && lastActual >= 0 && (forecast > 0 || curShort > 0) && (() => {
                  const j = weeks.length - 1;
                  const base = weeks[lastActual].value ?? 0;
                  const stackTop = base + forecast;
                  return (
                    <g>
                      {/* Where the quarter ends if the plan holds: today's count, faint, with the forecast on top. */}
                      {base > 0 && <rect {...bar(wx(j), WBAR, 0, base)} rx={3} fill={C.data1} fillOpacity={0.28} />}
                      {forecast > 0 && <rect {...bar(wx(j), WBAR, base, stackTop)} rx={3} fill={C.data2} fillOpacity={0.5} />}
                      {curShort > 0 && <rect x={wx(j) - WBAR / 2 + 0.75} y={y(stackTop + curShort) + 0.75} width={WBAR - 1.5} height={y(stackTop) - y(stackTop + curShort) - 1.5} rx={3} fill="none" stroke={SIGNALS.red.color} strokeOpacity={0.85} strokeWidth={1.5} strokeDasharray="4 3" />}
                      {forecast > 0 && y(base) - y(stackTop) >= 20 && (
                        <text x={wx(j)} y={y(stackTop) + 16} textAnchor="middle" fontSize={12} fontWeight={600} fill={C.ink}>
                          +{forecast}
                        </text>
                      )}
                    </g>
                  );
                })()}
                {weeks.map((w, j) => {
                  const prev = j > 0 ? weeks[j - 1].value : 0;
                  const changed = w.value !== null && (w.value !== prev || j === lastActual);
                  const ahead = w.value === null;
                  return (
                    <g key={w.week} opacity={hover !== null && hover !== j ? 0.45 : 1} style={{ transition: 'opacity 150ms' }}>
                      {changed && w.value! > 0 && (
                        <text x={wx(j)} y={y(w.value!) - 8} textAnchor="middle" fontSize={13} fontWeight={600} fill={C.ink}>
                          {w.value}
                        </text>
                      )}
                      {ahead && <rect x={wx(j) - WBAR / 2} y={y(0) - 2} width={WBAR} height={2} rx={1} fill={C.lineStrong} />}
                      {(j % showEvery === 0 || j === lastActual) && (
                        <text x={wx(j)} y={H - PAD.bottom + 24} textAnchor="middle" fontSize={12} fill={j === lastActual && isCurrent ? C.ink : C.ink3} fillOpacity={ahead ? 0.6 : 1} fontWeight={j === lastActual && isCurrent ? 600 : 400}>
                          {w.label}
                        </text>
                      )}
                      {j === lastActual && isCurrent && <line x1={wx(j) - 10} x2={wx(j) + 10} y1={H - PAD.bottom + 32} y2={H - PAD.bottom + 32} stroke={healthColor(selected)} strokeWidth={3} strokeLinecap="round" />}
                    </g>
                  );
                })}
              </motion.g>
            )}
          </AnimatePresence>

          {/* Hit targets: the whole slot, so the reader aims at a quarter or a week, not a bar. */}
          {unit === 'quarters'
            ? quarters.map((q, i) => (
                <rect
                  key={q}
                  x={PAD.left + qSlot * i}
                  y={PAD.top}
                  width={qSlot}
                  height={PLOT}
                  fill="transparent"
                  tabIndex={0}
                  role="button"
                  aria-label={`${quarterLabel(q)}: ${totals[i]} certified, target ${targets[i] ?? 'none'}. Open this quarter`}
                  data-testid={`trend-quarter-${q}`}
                  onPointerEnter={() => setHover(i)}
                  onPointerLeave={() => setHover(null)}
                  onFocus={() => setHover(i)}
                  onBlur={() => setHover(null)}
                  onClick={() => openQuarter(q)}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), openQuarter(q))}
                  style={{ cursor: 'pointer', outline: 'none' }}
                />
              ))
            : weeks.map((w, j) => (
                <rect
                  key={w.week}
                  x={PAD.left + wSlot * j}
                  y={PAD.top}
                  width={wSlot}
                  height={PLOT}
                  fill="transparent"
                  tabIndex={w.value === null ? -1 : 0}
                  role="img"
                  aria-label={`${w.label}, to ${fmtShort(w.end)}: ${w.value === null ? 'still ahead' : `${w.value} certified so far`}`}
                  data-testid={`trend-week-${w.week}`}
                  data-value={w.value ?? ''}
                  onPointerEnter={() => w.value !== null && setHover(j)}
                  onPointerLeave={() => setHover(null)}
                  onFocus={() => setHover(j)}
                  onBlur={() => setHover(null)}
                  style={{ outline: 'none' }}
                />
              ))}
        </svg>

        {hover !== null && unit === 'quarters' && quarters[hover] && (
          <div
            role="tooltip"
            className="pointer-events-none absolute z-20 w-60 rounded-control border border-line-strong bg-panel-2 p-4 shadow-[0_16px_32px_-12px_rgba(0,8,12,0.7)]"
            style={{ left: qx(hover) + (hover >= quarters.length - 1 ? -BAR / 2 - 252 : BAR / 2 + 12), top: PAD.top }}
          >
            <div className="text-small text-ink-3">{quarterLabel(quarters[hover])}</div>
            <div className="mt-0.5 text-lead font-semibold text-ink">
              {totals[hover]} certified <span className="text-small font-normal text-ink-3">of {targets[hover] ?? '–'} target</span>
            </div>
            {hover === cur && (
              <div className="mt-0.5 text-small text-ink-2">
                {forecast} forecast{curShort > 0 ? `, ${curShort} short` : ''}
              </div>
            )}
            <ul className="mt-2 space-y-1 border-t border-line pt-2">
              {s.domains
                .filter((d) => s.trend.some((p) => p.quarter === quarters[hover] && p.domain === d.id && (p.certified > 0 || p.target)))
                .map((d) => {
                  const t = s.trend.find((p) => p.quarter === quarters[hover] && p.domain === d.id);
                  return (
                    <li key={d.id} className="flex justify-between text-small text-ink-2">
                      <span>{d.name}</span>
                      <span className="tnum">
                        <strong className="font-semibold text-ink">{t?.certified ?? 0}</strong> / {t?.target ?? '–'}
                      </span>
                    </li>
                  );
                })}
            </ul>
            <div className="mt-2 text-small text-ink-3">{hover === sel ? 'Showing this quarter' : 'Click to open this quarter'}</div>
          </div>
        )}
        {hover !== null && unit === 'weeks' && weeks[hover]?.value != null && (() => {
          const w = weeks[hover];
          const p = selTarget !== null ? pace(hover) : null;
          const diff = p !== null ? w.value! - p : null;
          const left = wx(hover) + (wx(hover) > W - 280 ? -WBAR / 2 - 252 : WBAR / 2 + 12);
          return (
            <div role="tooltip" className="pointer-events-none absolute z-20 w-60 rounded-control border border-line-strong bg-panel-2 p-4 shadow-[0_16px_32px_-12px_rgba(0,8,12,0.7)]" style={{ left, top: PAD.top }} data-testid="trend-week-tooltip">
              <div className="text-small text-ink-3">
                {w.label}, {fmtShort(w.start)} to {fmtShort(w.end)}
              </div>
              <div className="mt-0.5 text-lead font-semibold text-ink">
                {w.value} certified <span className="text-small font-normal text-ink-3">so far</span>
              </div>
              {diff !== null && (
                <div className="mt-0.5 text-small text-ink-2">
                  {Math.abs(diff) < 0.5 ? 'On the target pace' : diff > 0 ? `${Math.round(diff * 10) / 10} ahead of the target pace` : `${Math.round(-diff * 10) / 10} behind the target pace`}
                </div>
              )}
              {Object.keys(w.byDomain).length > 0 && (
                <ul className="mt-2 space-y-1 border-t border-line pt-2">
                  {Object.entries(w.byDomain).map(([id, n]) => (
                    <li key={id} className="flex justify-between text-small text-ink-2">
                      <span>{domainName(s, id)}</span>
                      <strong className="font-semibold text-ink tnum">{n}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })()}

        <div className="sr-only">
          {unit === 'quarters' ? (
            <table>
              <caption>Certified per quarter by domain, with targets</caption>
              <thead>
                <tr>
                  <th>Quarter</th>
                  {s.domains.map((d) => (
                    <th key={d.id}>{d.name}</th>
                  ))}
                  <th>Total</th>
                  <th>Target</th>
                </tr>
              </thead>
              <tbody>
                {quarters.map((q, i) => (
                  <tr key={q}>
                    <td>{quarterLabel(q)}</td>
                    {s.domains.map((d) => (
                      <td key={d.id}>{s.trend.find((t) => t.quarter === q && t.domain === d.id)?.certified ?? 0}</td>
                    ))}
                    <td>{totals[i]}</td>
                    <td>{targets[i] ?? '–'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table>
              <caption>{quarterLabel(selected)}: certified so far at the end of each week, with the target pace</caption>
              <thead>
                <tr>
                  <th>Week</th>
                  <th>Certified so far</th>
                  <th>Target pace</th>
                </tr>
              </thead>
              <tbody>
                {weeks.map((w, j) => (
                  <tr key={w.week}>
                    <td>
                      {w.label}, to {fmtShort(w.end)}
                    </td>
                    <td>{w.value ?? 'ahead'}</td>
                    <td>{selTarget === null ? '–' : Math.round(pace(j) * 10) / 10}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </section>
  );
}
