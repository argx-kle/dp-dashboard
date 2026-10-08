/* A small typed table model: columns, sort state and a stable sort. Replaces TanStack Table. */

import type { ReactNode } from 'react';

export interface Column<T> {
  id: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  sortValue?: (row: T) => string | number;
  /** First sort direction when the header is clicked. */
  descFirst?: boolean;
  align?: 'right';
  /** Frozen on the left during horizontal scroll, at this offset in px. */
  freezeAt?: number;
  /** Last frozen column: draws the edge shadow once the table is scrolled. */
  freezeEdge?: boolean;
  minWidth?: number;
}

export type Sort = { id: string; desc: boolean } | null;

export function nextSort(current: Sort, col: Column<unknown>): Sort {
  const firstDesc = !!col.descFirst;
  if (!current || current.id !== col.id) return { id: col.id, desc: firstDesc };
  if (current.desc === firstDesc) return { id: col.id, desc: !firstDesc };
  return null;
}

export function sortRows<T>(rows: T[], cols: Column<T>[], sort: Sort): T[] {
  if (!sort) return rows;
  const col = cols.find((c) => c.id === sort.id);
  if (!col?.sortValue) return rows;
  const v = col.sortValue;
  const dir = sort.desc ? -1 : 1;
  return rows
    .map((r, i) => ({ r, i, k: v(r) }))
    .sort((a, b) => {
      if (a.k < b.k) return -dir;
      if (a.k > b.k) return dir;
      return a.i - b.i;
    })
    .map((x) => x.r);
}
