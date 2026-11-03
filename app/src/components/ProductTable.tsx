/* Product table. Optionally grouped by domain: each domain is a summary row with a disclosure
   triangle, its figures staying in view while the table scrolls sideways. Sortable columns, the
   product name frozen on the left, search matches highlighted in names. Stages, not gate codes. */

import { useId, useMemo, useState, type ReactNode } from 'react';
import StatusPips from '@/components/StatusPips';
import FlagBadge from '@/components/FlagBadge';
import SourceLabel from '@/components/SourceLabel';
import ScrollTable from '@/components/ScrollTable';
import { ChevronDownIcon, ChevronUpIcon, SortIcon, TriangleIcon } from '@/components/Icons';
import { useSnapshot } from '@/lib/context';
import { fmtShort } from '@/lib/format';
import { href } from '@/lib/router';
import { STATUS_ORDER, domainName } from '@/lib/select';
import { nextSort, sortRows, type Column, type Sort } from '@/lib/table';
import { STAGE_ORDER, gateLabel } from '@/lib/theme';
import type { Range } from '@/lib/search';
import type { ProductRow, Snapshot } from '@/types/snapshot';

const FAILING = new Set(['Failed', 'Unreachable']);

export function Highlighted({ text, ranges }: { text: string; ranges?: Range[] }) {
  if (!ranges?.length) return <>{text}</>;
  const out: ReactNode[] = [];
  let at = 0;
  ranges.forEach(([a, b], i) => {
    if (a > at) out.push(text.slice(at, a));
    out.push(
      <mark key={i} className="rounded-[3px] bg-clear/20 px-px text-ink">
        {text.slice(a, b)}
      </mark>,
    );
    at = b;
  });
  if (at < text.length) out.push(text.slice(at));
  return <>{out}</>;
}

interface ColumnOptions {
  showDomain: boolean;
  compact: boolean;
  highlight?: Map<string, Range[]>;
}

export function productColumns(s: Snapshot, { showDomain, compact, highlight }: ColumnOptions): Column<ProductRow>[] {
  const year = Number(s.asOfDate.slice(0, 4));
  const short = (iso?: string) => fmtShort(iso, year);
  const allSelfReported = s.products.every((p) => !p.activeUsers30d || p.activeUsers30d.source === 'self-reported');
  const cols: Column<ProductRow>[] = [
    {
      id: 'name',
      header: 'Product',
      sortValue: (p) => p.name.toLowerCase(),
      freezeAt: compact ? undefined : 0,
      freezeEdge: !compact,
      minWidth: 230,
      cell: (p) => (
        <a href={href.product(p.urn)} className="font-semibold whitespace-nowrap text-ink no-underline hover:text-clear hover:underline" data-testid="product-row-link">
          <Highlighted text={p.name} ranges={highlight?.get(p.urn)} />
        </a>
      ),
    },
  ];
  if (showDomain && !compact)
    cols.push({
      id: 'domain',
      header: 'Domain',
      sortValue: (p) => domainName(s, p.domain),
      cell: (p) => <span className="block whitespace-nowrap text-ink-2">{domainName(s, p.domain)}</span>,
    });
  cols.push({ id: 'status', header: 'Stage', sortValue: (p) => STAGE_ORDER.indexOf(p.lifecycle) * 10 + STATUS_ORDER.indexOf(p.status), cell: (p) => <StatusPips product={p} /> });
  if (!compact)
    cols.push(
      {
        id: 'lastGate',
        header: 'Stage since',
        sortValue: (p) => p.lastGate?.date ?? '',
        cell: (p) =>
          p.lastGate ? (
            <span className="whitespace-nowrap">
              <span className="text-ink-2">{short(p.lastGate.date)}</span>
            </span>
          ) : (
            <span className="text-ink-3">–</span>
          ),
      },
      { id: 'days', header: 'Days in stage', align: 'right', sortValue: (p) => p.daysInStage, cell: (p) => <span className="font-semibold text-ink">{p.daysInStage}</span> },
    );
  cols.push({
    id: 'nextGate',
    header: 'Next gate',
    sortValue: (p) => p.nextGate?.plannedDate ?? '9999',
    cell: (p) =>
      p.nextGate ? (
        <span className="whitespace-nowrap">
          <span className="font-semibold text-ink">{gateLabel(p.nextGate.gate)}</span> <span className="text-ink-3">{short(p.nextGate.plannedDate)}</span>
          {p.nextGate.overdueDays > 0 && <span className="block text-small font-semibold whitespace-nowrap text-ink">{p.nextGate.overdueDays} days late</span>}
        </span>
      ) : (
        <span className="text-ink-3">–</span>
      ),
  });
  if (!compact)
    cols.push({
      id: 'users',
      header: (
        <span>
          Users, 30 d{allSelfReported && <span className="block text-left text-small font-normal text-ink-3">self-reported</span>}
        </span>
      ),
      align: 'right',
      descFirst: true,
      sortValue: (p) => p.activeUsers30d?.value ?? -1,
      cell: (p) =>
        p.activeUsers30d ? (
          <span className="inline-flex items-center gap-1.5">
            {!(allSelfReported && p.activeUsers30d.source === 'self-reported') && <SourceLabel source={p.activeUsers30d.source} />}
            <span className="font-semibold text-ink">{p.activeUsers30d.value}</span>
          </span>
        ) : (
          <span className="text-ink-3">–</span>
        ),
    });
  if (!compact && s.products.some((p) => p.nextdata || p.validation))
    cols.push({
      id: 'platform',
      header: (
        <span title="Runtime in NextData and finish-spec score from the validation tool">
          Platform<span className="block text-left text-small font-normal text-ink-3">runtime · spec</span>
        </span>
      ),
      descFirst: true,
      minWidth: 130,
      sortValue: (p) => p.validation?.score ?? -1,
      cell: (p) => (
        <span className="block whitespace-nowrap" data-testid="platform-cell">
          <span className={p.nextdata && FAILING.has(p.nextdata.runtime) ? 'font-semibold text-ink' : 'text-ink-2'}>{p.nextdata ? p.nextdata.runtime : 'Not in NextData'}</span>
          {p.nextdata?.env && p.nextdata.runtime === 'Started' && <span className="text-ink-3"> · {p.nextdata.env}</span>}
          <span className="block text-small text-ink-3">{p.validation?.score != null ? `spec ${Math.round(p.validation.score * 100)}%` : 'no spec score'}</span>
        </span>
      ),
    });
  cols.push(
    {
      id: 'dpo',
      header: 'Data product owner',
      sortValue: (p) => p.dpo ?? '~',
      cell: (p) => (p.dpo ? <span className="whitespace-nowrap text-ink-2">{p.dpo}</span> : <span className="whitespace-nowrap text-ink-3">Not assigned</span>),
    },
    {
      id: 'flags',
      header: 'Flags',
      descFirst: true,
      sortValue: (p) => p.flags.length,
      cell: (p) => (
        <span className="flex flex-wrap gap-1">
          {p.flags.map((f) => (
            <FlagBadge key={f.code} code={f.code} reason={f.reason} />
          ))}
        </span>
      ),
    },
  );
  return cols;
}

interface Props {
  products: ProductRow[];
  showDomain?: boolean;
  compact?: boolean;
  caption?: string;
  title?: string;
  action?: ReactNode;
  /** Group rows under a domain summary row with a disclosure triangle; groups start open. */
  groupByDomain?: boolean;
  /** Open every group that has rows (e.g. while searching). */
  forceOpen?: boolean;
  highlight?: Map<string, Range[]>;
  empty?: ReactNode;
}

export default function ProductTable({ products, showDomain = true, compact = false, caption, title, action, groupByDomain = false, forceOpen = false, highlight, empty }: Props) {
  const s = useSnapshot();
  const scroll = !compact; // full tables scroll in their own viewport (pinned header, drag to pan); compact ones sit inline
  const uid = useId();
  const [sort, setSort] = useState<Sort>(null);
  const cols = useMemo(() => productColumns(s, { showDomain: showDomain && !groupByDomain, compact, highlight }), [s, showDomain, compact, highlight, groupByDomain]);
  const sorted = useMemo(() => sortRows(products, cols, sort), [products, cols, sort]);
  const groups = useMemo(() => (groupByDomain ? s.domains.map((d) => ({ id: d.id, rows: sorted.filter((p) => p.domain === d.id) })).filter((g) => g.rows.length) : [{ id: '', rows: sorted }]), [groupByDomain, s.domains, sorted]);
  const [open, setOpen] = useState<Set<string>>(() => new Set(s.domains.map((d) => d.id)));
  const isOpen = (id: string) => forceOpen || open.has(id);
  const toggle = (id: string) => setOpen((o) => (o.has(id) ? new Set([...o].filter((x) => x !== id)) : new Set([...o, id])));
  const allOpen = groups.every((g) => isOpen(g.id));

  const cellCls = (c: Column<ProductRow>, head = false) => {
    const base = compact ? 'px-3 py-2.5' : 'px-3 py-3';
    const align = c.align === 'right' ? 'text-right' : 'text-left';
    const frozen = c.freezeAt !== undefined ? `sticky ${head ? 'z-30' : 'z-10'}` : '';
    const edge = c.freezeEdge ? 'group-data-[scrolled=true]/scroll:shadow-[10px_0_12px_-10px_rgba(0,0,0,0.65)]' : '';
    const bg = head ? 'bg-panel-2' : c.freezeAt !== undefined ? 'bg-panel group-hover/row:bg-panel-2' : '';
    return `${base} ${align} ${frozen} ${edge} ${bg} first:pl-5 last:pr-5 align-middle`;
  };
  const freezeStyle = (c: Column<ProductRow>) => (c.freezeAt !== undefined ? { left: c.freezeAt, minWidth: c.minWidth, width: undefined } : c.minWidth ? { minWidth: c.minWidth } : undefined);

  const table = (
    <table className="w-full border-separate border-spacing-0 text-body" data-testid="product-table" data-count={products.length}>
      {caption && <caption className="sr-only">{caption}</caption>}
      <thead className={scroll ? 'sticky top-0 z-20' : ''}>
        <tr>
          {cols.map((c) => {
            const on = sort?.id === c.id;
            const Icon = on ? (sort!.desc ? ChevronDownIcon : ChevronUpIcon) : SortIcon;
            return (
              <th key={c.id} scope="col" aria-sort={on ? (sort!.desc ? 'descending' : 'ascending') : 'none'} className={`${cellCls(c, true)} border-b border-line whitespace-nowrap`} style={freezeStyle(c)}>
                <button type="button" onClick={() => setSort(nextSort(sort, c as Column<unknown>))} className={`group inline-flex cursor-pointer items-start gap-1 rounded-md text-small font-medium ${on ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}>
                  {c.header}
                  <Icon width={12} height={12} className={`mt-0.5 ${on ? 'text-clear' : 'opacity-0 transition-opacity group-hover:opacity-100'}`} />
                </button>
              </th>
            );
          })}
        </tr>
      </thead>
      {groups.map((g) => (
        <tbody key={g.id || 'all'} id={groupByDomain ? `${uid}-${g.id}` : undefined}>
          {groupByDomain && <GroupRow id={g.id} controls={`${uid}-${g.id}`} shown={g.rows.length} span={cols.length} open={isOpen(g.id)} onToggle={() => toggle(g.id)} />}
          {(!groupByDomain || isOpen(g.id)) &&
            g.rows.map((p) => (
              <tr key={p.urn} className="group/row transition-colors duration-150 hover:bg-panel-2" data-urn={p.urn}>
                {cols.map((c) => (
                  <td key={c.id} className={`${cellCls(c)} border-b border-line`} style={freezeStyle(c)}>
                    {c.cell(p)}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      ))}
      {products.length === 0 && (
        <tbody>
          <tr>
            <td colSpan={cols.length} className="px-6 py-12 text-center text-body text-ink-3">
              {empty ?? (
                <>
                  No products match these filters. <a href={href.products()}>Show all products</a>.
                </>
              )}
            </td>
          </tr>
        </tbody>
      )}
    </table>
  );

  const head = (title || action || groupByDomain) && (
    <div className="flex flex-wrap items-center justify-between gap-3 px-6 pt-6 pb-4">
      {title ? <h2 className="text-heading font-semibold text-ink">{title}</h2> : <span />}
      <div className="flex items-center gap-4">
        {groupByDomain && !forceOpen && (
          <button type="button" onClick={() => setOpen(allOpen ? new Set() : new Set(groups.map((g) => g.id)))} className="cursor-pointer text-small text-link hover:text-ink" data-testid="toggle-all-domains">
            {allOpen ? 'Collapse all' : 'Expand all'}
          </button>
        )}
        {action}
      </div>
    </div>
  );

  if (!scroll) return table;
  return (
    <div>
      {head && <div className="mb-0">{head}</div>}
      <ScrollTable label={caption ?? title ?? 'Products'}>
        {table}
      </ScrollTable>
    </div>
  );
}

/** A domain's row: triangle, name and how many products it holds, pinned left while scrolling. */
function GroupRow({ id, controls, shown, span, open, onToggle }: { id: string; controls: string; shown: number; span: number; open: boolean; onToggle: () => void }) {
  const s = useSnapshot();
  const d = s.domains.find((x) => x.id === id)!;
  const total = s.products.filter((p) => p.domain === id).length;
  return (
    <tr className="bg-panel-2">
      <td colSpan={span} className="border-b border-line p-0">
        <div className="sticky left-0 flex w-max items-center gap-3 py-2.5 pr-6 pl-3">
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={open}
            aria-controls={controls}
            aria-label={`${open ? 'Collapse' : 'Expand'} ${d.name}`}
            className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-control text-ink-2 hover:bg-panel-3 hover:text-ink"
            data-testid={`domain-toggle-${id}`}
          >
            <TriangleIcon className={`transition-transform duration-200 ${open ? 'rotate-90' : ''}`} />
          </button>
          <a href={href.domain(id)} className="text-lead font-semibold text-ink no-underline hover:text-clear hover:underline">
            {d.name}
          </a>
          {/* The count shows while the domain is closed; open, its rows speak for themselves. */}
          {!open && (
            <span className="text-small whitespace-nowrap text-ink-3 tnum" data-testid={`domain-total-${id}`}>
              {shown < total ? (
                <span data-testid={`domain-shown-${id}`}>
                  {shown} of {total} products
                </span>
              ) : (
                `${total} ${total === 1 ? 'product' : 'products'}`
              )}
            </span>
          )}
        </div>
      </td>
    </tr>
  );
}
