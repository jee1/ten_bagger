import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import type { Market } from './performanceLoad.ts';

/** Baselines the published pick is paired against, by date (scripts/edge_baseline.py). */
export const EDGE_ARMS = ['random', 'size_matched', 'top2_5'] as const;
export type EdgeArm = (typeof EDGE_ARMS)[number];

export interface EdgeComparison {
  arm: EdgeArm;
  n: number;
  meanExcess: number;
  medianExcess: number;
  beatRate: number;
  tStat: number | null;
}

export interface EdgeSummary {
  asOfDate: string;
  comparisons: EdgeComparison[];
}

export function loadLatestEdgeSummary(
  market: Market,
  options: { rootDir?: string } = {},
): EdgeSummary | null {
  const dir = join(options.rootDir ?? process.cwd(), 'content', 'edge-baseline');
  if (!existsSync(dir)) return null;
  const latest = readdirSync(dir)
    .filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f))
    .sort()
    .at(-1);
  if (!latest) return null;
  try {
    const doc = JSON.parse(readFileSync(join(dir, latest), 'utf8'));
    const pickMinus = doc?.summary?.[market]?.pickMinus ?? {};
    const comparisons = EDGE_ARMS.flatMap((arm) => {
      const s = pickMinus[arm];
      if (!s || !(s.n > 0)) return [];
      return [
        {
          arm,
          n: s.n,
          meanExcess: s.meanExcess,
          medianExcess: s.medianExcess,
          beatRate: s.beatRate,
          tStat: s.tStat ?? null,
        },
      ];
    });
    if (comparisons.length === 0) return null;
    return { asOfDate: doc.asOfDate, comparisons };
  } catch {
    return null;
  }
}
