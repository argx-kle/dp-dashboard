import { createContext, useContext } from 'react';
import type { Snapshot } from '@/types/snapshot';

export const SnapshotContext = createContext<Snapshot | null>(null);

export function useSnapshot(): Snapshot {
  const s = useContext(SnapshotContext);
  if (!s) throw new Error('SnapshotContext missing');
  return s;
}
