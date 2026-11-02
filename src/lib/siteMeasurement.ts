export function trimPublicEnv(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

export function resolveGoogleSiteVerification(envValue: unknown, fallback = ''): string {
  const fromEnv = trimPublicEnv(envValue);
  if (fromEnv) return fromEnv;
  return trimPublicEnv(fallback);
}

/** Cloudflare Web Analytics beacon payload, or null when token is unset. */
export function cfWebAnalyticsBeaconJson(token: unknown): string | null {
  const t = trimPublicEnv(token);
  if (!t) return null;
  return JSON.stringify({ token: t });
}
