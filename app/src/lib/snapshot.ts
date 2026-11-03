/* Loads the embedded snapshot. In `npm run dev` the placeholder is empty, so the showcase week is used. */

import type { Snapshot } from '@/types/snapshot';

export async function loadSnapshot(): Promise<Snapshot> {
  const el = document.getElementById('snapshot');
  const text = el?.textContent?.trim() ?? '';
  if (text && text !== '{}') {
    return JSON.parse(text) as Snapshot;
  }
  if (import.meta.env.DEV) {
    const mod = await import('../../../tests/fixtures/showcase/2026-W47.json'); // the showcase week: scripts/make_showcase.py
    return mod.default as unknown as Snapshot;
  }
  throw new Error('No snapshot embedded. Run `dp build` to produce index.html.');
}
