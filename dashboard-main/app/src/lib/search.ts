/* Product search: order-independent, forgiving, ranked. No dependency.

   The query is split into tokens; every token must match somewhere in a product's fields, in any
   order. Per token the best of four match kinds counts:
     1. substring           "insights"  in "Market Access Insights"
     2. fuzzy subsequence   "pj360"     in "Patient Journey 360" (letters in order, gaps allowed)
     3. one typo            "pharmacovigilence" for "pharmacovigilance" (tokens of 4+ letters)
   Scores reward contiguous runs and word starts, penalise gaps, and weight the product name above
   owner, domain, status, flags and URN. */

export type Range = [number, number];

export interface SearchField {
  key: string;
  text: string;
  weight: number;
}

export interface Hit<T> {
  item: T;
  score: number;
  /** Matched character ranges in the field named `highlightKey` (for highlighting). */
  ranges: Range[];
}

export function normalise(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

export function tokens(query: string): string[] {
  return normalise(query)
    .split(/[\s,;]+/)
    .map((t) => t.trim())
    .filter(Boolean);
}

const isWordChar = (c: string | undefined) => !!c && /[a-z0-9]/.test(c);
const isDigit = (c: string | undefined) => !!c && c >= '0' && c <= '9';

function isWordStart(t: string, i: number): boolean {
  if (i === 0) return true;
  const prev = t[i - 1];
  const cur = t[i];
  if (!isWordChar(prev)) return true;
  return isDigit(cur) !== isDigit(prev); // "journey360": the 3 starts a word
}

interface TokenMatch {
  score: number;
  ranges: Range[];
}

/** Substring match. */
function substring(token: string, t: string): TokenMatch | null {
  let best: TokenMatch | null = null;
  let from = 0;
  for (;;) {
    const i = t.indexOf(token, from);
    if (i < 0) break;
    const score = 10 + token.length * 2 + (isWordStart(t, i) ? 6 : 0) + (i === 0 ? 2 : 0);
    if (!best || score > best.score) best = { score, ranges: [[i, i + token.length]] };
    from = i + 1;
  }
  return best;
}

/** Fuzzy subsequence: every token letter in order, gaps allowed. Prefers word starts, then the
    tightest window (a forward pass finds the earliest end, a backward pass shrinks the start). */
function fuzzy(token: string, t: string): TokenMatch | null {
  // Forward: earliest positions that complete the subsequence.
  let ti = 0;
  let end = -1;
  for (let i = 0; i < t.length && ti < token.length; i++) {
    if (t[i] === token[ti]) {
      ti++;
      if (ti === token.length) end = i;
    }
  }
  if (end < 0) return null;
  // Backward from the end: the latest start, which gives the tightest window.
  let qi = token.length - 1;
  let start = end;
  for (let i = end; i >= 0 && qi >= 0; i--) {
    if (t[i] === token[qi]) {
      qi--;
      start = i;
    }
  }
  // Within the window, place each letter greedily, preferring a word start when one is near.
  const pos: number[] = [];
  let at = start;
  for (let k = 0; k < token.length; k++) {
    let chosen = -1;
    for (let i = at; i <= end; i++) {
      if (t[i] !== token[k]) continue;
      if (chosen < 0) chosen = i;
      if (isWordStart(t, i)) {
        // only jump ahead if the rest of the token still fits before `end`
        const rest = token.slice(k + 1);
        let r = 0;
        for (let j = i + 1; j <= end && r < rest.length; j++) if (t[j] === rest[r]) r++;
        if (r === rest.length) {
          chosen = i;
          break;
        }
      }
      if (i - chosen > 6) break;
    }
    if (chosen < 0) return null;
    pos.push(chosen);
    at = chosen + 1;
  }
  let score = 0;
  for (let k = 0; k < pos.length; k++) {
    score += 1;
    if (isWordStart(t, pos[k])) score += 3;
    if (k > 0 && pos[k] === pos[k - 1] + 1) score += 2;
    if (k > 0) score -= Math.min(2, (pos[k] - pos[k - 1] - 1) * 0.15);
  }
  // A short token that only matches as scattered letters is noise.
  if (token.length <= 2 && !isWordStart(t, pos[0])) return null;
  const ranges: Range[] = [];
  for (const p of pos) {
    const last = ranges[ranges.length - 1];
    if (last && last[1] === p) last[1] = p + 1;
    else ranges.push([p, p + 1]);
  }
  return { score: Math.max(1, score), ranges };
}

/** Damerau-Levenshtein distance capped at 2. */
function editDistance(a: string, b: string): number {
  if (Math.abs(a.length - b.length) > 1) return 2;
  const d: number[][] = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
    }
  }
  return d[a.length][b.length];
}

/** One typo against a word or a word prefix of the same length. */
function typo(token: string, t: string): TokenMatch | null {
  if (token.length < 4) return null;
  const re = /[a-z0-9]+/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(t))) {
    const w = m[0];
    const candidates = [w, w.slice(0, token.length), w.slice(0, token.length + 1)];
    if (candidates.some((c) => c.length >= token.length - 1 && editDistance(token, c) <= 1)) {
      return { score: 3 + token.length, ranges: [[m.index, m.index + Math.min(w.length, token.length + 1)]] };
    }
  }
  return null;
}

export function matchToken(token: string, text: string): TokenMatch | null {
  const t = normalise(text);
  return substring(token, t) ?? fuzzy(token, t) ?? typo(token, t);
}

/** Rank items for a query. Every token must match some field. Returns hits sorted by score. */
export function search<T>(items: T[], query: string, fields: (item: T) => SearchField[], highlightKey = 'name'): Hit<T>[] {
  const toks = tokens(query);
  if (toks.length === 0) return items.map((item) => ({ item, score: 0, ranges: [] }));
  const hits: Hit<T>[] = [];
  for (const item of items) {
    const fs = fields(item);
    let total = 0;
    const ranges: Range[] = [];
    let ok = true;
    for (const tok of toks) {
      let best: { score: number; key: string; ranges: Range[] } | null = null;
      for (const f of fs) {
        if (!f.text) continue;
        const m = matchToken(tok, f.text);
        if (m && (!best || m.score * f.weight > best.score)) best = { score: m.score * f.weight, key: f.key, ranges: m.ranges };
      }
      if (!best) {
        ok = false;
        break;
      }
      total += best.score;
      if (best.key === highlightKey) ranges.push(...best.ranges);
    }
    if (ok) hits.push({ item, score: total, ranges: mergeRanges(ranges) });
  }
  return hits.sort((a, b) => b.score - a.score);
}

function mergeRanges(rs: Range[]): Range[] {
  const sorted = [...rs].sort((a, b) => a[0] - b[0]);
  const out: Range[] = [];
  for (const r of sorted) {
    const last = out[out.length - 1];
    if (last && r[0] <= last[1]) last[1] = Math.max(last[1], r[1]);
    else out.push([r[0], r[1]]);
  }
  return out;
}
