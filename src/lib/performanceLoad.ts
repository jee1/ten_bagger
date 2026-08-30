import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import type { PerformanceBundle } from './content-types.generated.ts';

export type Market = 'KR' | 'US';

/** Prefer cwd (astro build/dev) over import.meta.url — bundling relocates modules. */
function defaultRoot(): string {
  return process.cwd();
}

export interface LoadOptions {
  /** Defaults to repository root. Tests pass a fixture root with content/performance/. */
  rootDir?: string;
}

export function loadPerformanceBundle(
  market: Market,
  options: LoadOptions = {},
): PerformanceBundle | null {
  const root = options.rootDir ?? defaultRoot();
  const path = join(root, 'content', 'performance', `${market}.json`);
  if (!existsSync(path)) return null;
  try {
    const raw = readFileSync(path, 'utf8');
    const data = JSON.parse(raw) as PerformanceBundle;
    if (data.market !== market) return null;
    if (!Array.isArray(data.measurements)) return null;
    return data;
  } catch {
    return null;
  }
}
