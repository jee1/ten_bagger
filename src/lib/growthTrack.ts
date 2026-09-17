export const GROWTH_EVENTS = {
  rssClick: 'growth/rss-click',
  shareSuccess: 'growth/share-success',
} as const;

export type GrowthEventPath = (typeof GROWTH_EVENTS)[keyof typeof GROWTH_EVENTS];

export interface GoatCounterLike {
  count: (args: { path: string; event: true; title?: string }) => void;
}

/** Disable analytics on dev/preview hosts so tests do not pollute production. */
export function isGrowthTrackingEnabled(hostname: string, dev = false): boolean {
  if (dev) return false;
  const host = hostname.toLowerCase();
  if (host === 'localhost' || host === '127.0.0.1' || host.endsWith('.local')) return false;
  return true;
}

/** Count a GoatCounter event; never throws. */
export function trackGrowthEvent(
  goatcounter: GoatCounterLike | undefined,
  path: GrowthEventPath,
  enabled: boolean,
): void {
  if (!enabled || !goatcounter?.count) return;
  try {
    goatcounter.count({ path, event: true, title: path });
  } catch {
    // blocked or unloaded — ignore
  }
}
