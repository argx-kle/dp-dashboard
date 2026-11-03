import type { MetricDefinition } from '@/types/snapshot';

export type Unit = MetricDefinition['unit'];

export function fmtValue(value: number | null | undefined, unit: Unit): string {
  if (value === null || value === undefined) return '—';
  if (unit === 'share') return `${Math.round(value * 100)}%`;
  if (Number.isInteger(value)) return value.toLocaleString('en-GB');
  return value.toLocaleString('en-GB', { maximumFractionDigits: 1 });
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function fmtDate(iso: string | undefined | null): string {
  if (!iso) return '—';
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  if (!y || !m || !d) return iso;
  return `${d} ${MONTHS[m - 1]} ${y}`;
}

/** "20 Sep", or "20 Sep 2025" when the year differs from the reference year. */
export function fmtShort(iso: string | undefined | null, refYear?: number): string {
  if (!iso) return '—';
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  if (!y || !m || !d) return iso;
  return refYear && y !== refYear ? `${d} ${MONTHS[m - 1]} ${y}` : `${d} ${MONTHS[m - 1]}`;
}

/** Registry reason texts carry ISO dates; show them the way people read dates. */
export function humanize(text: string, refYear?: number): string {
  return text.replace(/\b(\d{4}-\d{2}-\d{2})\b/g, (iso) => fmtShort(iso, refYear));
}

export function fmtDateTime(iso: string | undefined | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}, ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

/** "8 Oct 2026, 11:00 CEST": the viewer's local time with its zone, so nobody has to convert. */
export function fmtDateTimeZone(iso: string | undefined | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  let zone = '';
  try {
    zone = new Intl.DateTimeFormat('en-GB', { timeZoneName: 'short' }).formatToParts(d).find((p) => p.type === 'timeZoneName')?.value ?? '';
  } catch {
    zone = '';
  }
  return `${fmtDateTime(iso)}${zone ? ` ${zone}` : ''}`;
}

/** "31 December": the last day of a quarter in words. */
export function quarterEnd(quarter: string): string {
  return { 1: '31 March', 2: '30 June', 3: '30 September', 4: '31 December' }[Number(quarter.slice(-1)) as 1] ?? 'quarter end';
}

export function quarterLabel(quarter: string): string {
  const m = quarter.match(/^(\d{4})-Q([1-4])$/);
  return m ? `Q${m[2]} ${m[1]}` : quarter;
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${n} ${n === 1 ? one : many}`;
}
