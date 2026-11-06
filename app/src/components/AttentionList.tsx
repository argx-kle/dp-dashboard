/* Needs attention: flagged products, most severe first, each with its flag, reason, stage and owner.
   On a wide screen the list fills the height of the panel beside it (map or table) and shows as many whole items
   as fit; a footer names the rest. No inner scroll. Hovering an item lights the product on the cluster map. */

import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import StageMark, { PlatformMark } from '@/components/StageMark';
import { failingProducts, failingReasons, platformStage } from '@/lib/platform';
import { AlertIcon, ArrowRightIcon, FLAG_ICONS } from '@/components/Icons';
import { useSnapshot } from '@/lib/context';
import { useFocusTarget } from '@/lib/focus';
import { href } from '@/lib/router';
import { fmtShort, humanize, plural, quarterLabel } from '@/lib/format';
import { domainName, flaggedProducts, flagDef } from '@/lib/select';
import { SIGNALS, flagColor, stageText } from '@/lib/theme';
import type { ProductRow } from '@/types/snapshot';

/** Items shown when the list does not sit beside a panel (narrow screens). */
export const STACKED_ITEMS = 6;
const WIDE = '(min-width: 1280px)';

function useWide(): boolean {
  const [wide, setWide] = useState(() => typeof window !== 'undefined' && !!window.matchMedia?.(WIDE).matches);
  useLayoutEffect(() => {
    const mq = window.matchMedia?.(WIDE);
    if (!mq) return;
    const on = () => setWide(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return wide;
}

/** How many whole items fit in the section, leaving room for the footer when some do not. */
function useFit(count: number, wide: boolean) {
  const section = useRef<HTMLElement>(null);
  const head = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const [fit, setFit] = useState(Math.min(count, STACKED_ITEMS));
  useLayoutEffect(() => {
    if (!wide) {
      setFit(Math.min(count, STACKED_ITEMS));
      return;
    }
    const measure = () => {
      const sec = section.current;
      const ul = list.current;
      if (!sec || !ul) return;
      const heights = Array.from(ul.children).map((li) => (li as HTMLElement).offsetHeight);
      const avail = sec.clientHeight - (head.current?.offsetHeight ?? 0);
      if (heights.reduce((a, h) => a + h, 0) <= avail) return setFit(count);
      const room = avail - 76; // the footer naming the rest
      let used = 0;
      let n = 0;
      for (const h of heights) {
        if (used + h > room) break;
        used += h;
        n++;
      }
      setFit(Math.max(1, n));
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (section.current) ro.observe(section.current);
    return () => ro.disconnect();
  }, [count, wide]);
  return { section, head, list, fit };
}

/** The column frame: on a wide screen it takes the height of its grid row, never sets it. */
function Frame({ sectionRef, headRef, title, count, testId, children }: { sectionRef: React.RefObject<HTMLElement | null>; headRef: React.RefObject<HTMLDivElement | null>; title: string; count: ReactNode; testId?: string; children: ReactNode }) {
  return (
    <div className="relative min-w-0">
      <section ref={sectionRef} aria-labelledby={`${testId}-h`} className="flex flex-col overflow-hidden rounded-panel border border-line bg-panel print-break-avoid xl:absolute xl:inset-0" data-testid={testId}>
        <div ref={headRef} className="flex items-baseline justify-between gap-3 px-6 pt-6 pb-3">
          <h2 id={`${testId}-h`} className="text-heading font-semibold text-ink">
            {title}
          </h2>
          {count}
        </div>
        {children}
      </section>
    </div>
  );
}

function Item({ urn, icon, children, hidden }: { urn: string; icon: ReactNode; children: ReactNode; hidden: boolean }) {
  const { focus, setFocus } = useFocusTarget();
  return (
    <li
      className={`border-t border-line/60 ${hidden ? 'invisible' : ''}`}
      aria-hidden={hidden || undefined}
      onPointerEnter={() => setFocus(urn)}
      onPointerLeave={() => setFocus(null)}
      onFocus={() => setFocus(urn)}
      onBlur={() => setFocus(null)}
      data-urn={urn}
    >
      <div className={`grid grid-cols-[18px_minmax(0,1fr)] gap-x-3 px-6 py-3 transition-colors duration-150 ${focus === urn ? 'bg-panel-3' : 'hover:bg-panel-2'}`}>
        <span className="pt-[3px]">{icon}</span>
        <div className="min-w-0">{children}</div>
      </div>
    </li>
  );
}

export default function AttentionList({ domain }: { domain?: string }) {
  const s = useSnapshot();
  const wide = useWide();
  const all = flaggedProducts(s, domain);
  const { section, head, list, fit } = useFit(all.length, wide);
  const items = wide ? all : all.slice(0, fit);
  const rest = all.slice(fit);
  const year = Number(s.asOfDate.slice(0, 4));

  return (
    <Frame
      sectionRef={section}
      headRef={head}
      title="Needs attention"
      testId="attention"
      count={
        <span className="text-small text-ink-3 tnum" data-testid="needs-attention-count">
          {plural(all.length, 'product')}
        </span>
      }
    >
      {all.length === 0 ? (
        <p className="px-6 pb-6 text-body text-ink-3">Nothing flagged this week.</p>
      ) : (
        <>
          <ul ref={list} className="m-0 min-h-0 flex-1 list-none overflow-hidden p-0" aria-label="Products needing attention">
            {items.map((p: ProductRow, i) => {
              const first = p.flags[0];
              const def = flagDef(s, first.code);
              const Icon = FLAG_ICONS[first.code] ?? AlertIcon;
              return (
                <Item key={p.urn} urn={p.urn} hidden={i >= fit} icon={<Icon width={16} height={16} style={{ color: flagColor(def?.signal) }} aria-hidden="true" />}>
                  <a href={href.product(p.urn)} className="block truncate text-body font-semibold text-ink no-underline hover:underline" data-testid={i < fit ? 'needs-attention-item' : undefined} tabIndex={i < fit ? undefined : -1}>
                    {p.name}
                  </a>
                  <p className="mt-0.5 text-small text-pretty text-ink-2">
                    <span className="font-semibold text-ink">{def?.label}</span> {humanize(first.reason, year)}
                    {p.flags.length > 1 && <span className="text-ink-3"> +{p.flags.length - 1} more</span>}
                  </p>
                  <p className="mt-0.5 text-small text-ink-3">
                    <strong className="font-semibold" style={{ color: stageText(p.lifecycle) }}>
                      {p.lifecycle}
                    </strong>{' '}
                    · {domainName(s, p.domain)} · {p.dpo ?? 'no owner'}
                  </p>
                </Item>
              );
            })}
          </ul>
          {rest.length > 0 && (
            <a
              href={href.products({ flagged: '1', domain })}
              className="flex shrink-0 items-center justify-between gap-3 border-t border-line px-6 py-3.5 text-small text-ink-2 no-underline transition-colors hover:bg-panel-2 hover:text-ink"
              data-testid="needs-attention-more"
              data-count={rest.length}
            >
              <span className="line-clamp-2 text-pretty">
                <span className="font-semibold text-ink">{rest.length} more:</span> {rest.map((p) => p.name).join(', ')}
              </span>
              <ArrowRightIcon width={14} height={14} className="shrink-0" />
            </a>
          )}
        </>
      )}
    </Frame>
  );
}

/** For a closed quarter, in place of the attention list: what went live in it, newest first. Flags are only
    known for the current week, so a past quarter shows its deliveries instead. */
export function DeliveredList() {
  const s = useSnapshot();
  const wide = useWide();
  const urns = new Set(s.metrics.find((m) => m.id === 'certified_qtd' && m.scope === 'org')?.urns ?? []);
  const all = s.products.filter((p) => urns.has(p.urn)).sort((a, b) => (b.firstG4Date ?? '').localeCompare(a.firstG4Date ?? ''));
  const { section, head, list, fit } = useFit(all.length, wide);
  const items = wide ? all : all.slice(0, fit);
  const rest = all.slice(fit);
  const year = Number(s.asOfDate.slice(0, 4));
  return (
    <Frame sectionRef={section} headRef={head} title={`Went live in ${quarterLabel(s.quarter)}`} testId="delivered-list" count={<span className="text-small text-ink-3 tnum">{plural(all.length, 'product')}</span>}>
      {all.length === 0 ? (
        <p className="px-6 pb-6 text-body text-ink-3">Nothing went live this quarter.</p>
      ) : (
        <>
          <ul ref={list} className="m-0 min-h-0 flex-1 list-none overflow-hidden p-0">
            {items.map((p, i) => (
              <Item key={p.urn} urn={p.urn} hidden={i >= fit} icon={<StageMark stage="Live" size={16} />}>
                <a href={href.product(p.urn)} className="block truncate text-body font-semibold text-ink no-underline hover:underline" data-testid={i < fit ? 'delivered-item' : undefined} tabIndex={i < fit ? undefined : -1}>
                  {p.name}
                </a>
                <p className="mt-0.5 text-small text-ink-3">
                  Live {fmtShort(p.firstG4Date, year)} · {domainName(s, p.domain)}
                </p>
              </Item>
            ))}
          </ul>
          {rest.length > 0 && (
            <a href={href.products({ metric: 'certified_qtd', scope: 'org' })} className="flex shrink-0 items-center justify-between gap-3 border-t border-line px-6 py-3.5 text-small text-ink-2 no-underline hover:bg-panel-2 hover:text-ink">
              <span className="line-clamp-2">
                <span className="font-semibold text-ink">{rest.length} more:</span> {rest.map((p) => p.name).join(', ')}
              </span>
              <ArrowRightIcon width={14} height={14} className="shrink-0" />
            </a>
          )}
        </>
      )}
    </Frame>
  );
}

/** While the register has no gate dates, in place of the attention list: products whose latest deployment failed
    in a step of the promotion path, or that NextData reports Failed or Unreachable; the furthest along first. */
export function FailingList({ domain }: { domain?: string }) {
  const s = useSnapshot();
  const wide = useWide();
  const all = failingProducts(s, domain);
  const { section, head, list, fit } = useFit(all.length, wide);
  const items = wide ? all : all.slice(0, fit);
  const rest = all.slice(fit);
  return (
    <Frame sectionRef={section} headRef={head} title="Failing now" testId="failing" count={<span className="text-small text-ink-3 tnum" data-testid="failing-count">{plural(all.length, 'product')}</span>}>
      {all.length === 0 ? (
        <p className="px-6 pb-6 text-body text-ink-3">Nothing is failing: every latest deployment succeeded.</p>
      ) : (
        <>
          <ul ref={list} className="m-0 min-h-0 flex-1 list-none overflow-hidden p-0" aria-label="Products failing now">
            {items.map((p, i) => {
              const st = platformStage(s, p);
              return (
                <Item key={p.urn} urn={p.urn} hidden={i >= fit} icon={<AlertIcon width={16} height={16} style={{ color: SIGNALS.red.color }} aria-hidden="true" />}>
                  <a href={href.product(p.urn)} className="block truncate text-body font-semibold text-ink no-underline hover:underline" data-testid={i < fit ? 'failing-item' : undefined} tabIndex={i < fit ? undefined : -1}>
                    {p.name}
                  </a>
                  <p className="mt-0.5 text-small text-pretty text-ink-2">{failingReasons(s, p).join(' · ')}</p>
                  <p className="mt-0.5 inline-flex items-center gap-1.5 text-small text-ink-3">
                    <PlatformMark stage={st} size={14} />
                    <span>
                      {st.step > 0 ? `Got as far as ${st.label}` : st.label} · {domainName(s, p.domain)}
                    </span>
                  </p>
                </Item>
              );
            })}
          </ul>
          {rest.length > 0 && (
            <a
              href={href.products({ failing: '1', domain })}
              className="flex shrink-0 items-center justify-between gap-3 border-t border-line px-6 py-3.5 text-small text-ink-2 no-underline transition-colors hover:bg-panel-2 hover:text-ink"
              data-testid="failing-more"
              data-count={rest.length}
            >
              <span className="line-clamp-2 text-pretty">
                <span className="font-semibold text-ink">{rest.length} more:</span> {rest.map((p) => p.name).join(', ')}
              </span>
              <ArrowRightIcon width={14} height={14} className="shrink-0" />
            </a>
          )}
        </>
      )}
    </Frame>
  );
}
