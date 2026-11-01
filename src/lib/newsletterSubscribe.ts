function trimPublicEnv(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

export type NewsletterProvider = 'buttondown' | 'stibee';

export interface NewsletterHiddenField {
  name: string;
  value: string;
}

export interface NewsletterFormConfig {
  provider: NewsletterProvider;
  actionUrl: string;
  hiddenFields: NewsletterHiddenField[];
  sourceTag: string;
}

function normalizeProvider(value: unknown): NewsletterProvider | null {
  const p = trimPublicEnv(value).toLowerCase();
  if (p === 'buttondown' || p === 'stibee') return p;
  return null;
}

function isStibeeSubscribeUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === 'https:' && u.hostname.endsWith('stibee.com');
  } catch {
    return false;
  }
}

const BUTTONDOWN_USERNAME = /^[a-zA-Z0-9_-]+$/;

/** Returns null when provider or credentials are unset (production builds omit the form). */
export function resolveNewsletterFormConfig(
  env: Record<string, unknown>,
  defaultSourceSite: string,
): NewsletterFormConfig | null {
  const provider = normalizeProvider(env.PUBLIC_NEWSLETTER_PROVIDER);
  if (!provider) return null;

  const sourceTag =
    trimPublicEnv(env.PUBLIC_NEWSLETTER_SITE_TAG) || trimPublicEnv(defaultSourceSite) || 'unknown';

  if (provider === 'buttondown') {
    const username = trimPublicEnv(env.PUBLIC_BUTTONDOWN_USERNAME);
    if (!username || !BUTTONDOWN_USERNAME.test(username)) return null;
    return {
      provider,
      actionUrl: `https://buttondown.email/api/emails/embed-subscribe/${username}`,
      hiddenFields: [
        { name: 'embed', value: '1' },
        { name: 'tag', value: sourceTag },
      ],
      sourceTag,
    };
  }

  const actionUrl = trimPublicEnv(env.PUBLIC_STIBEE_SUBSCRIBE_URL);
  if (!actionUrl || !isStibeeSubscribeUrl(actionUrl)) return null;

  return {
    provider: 'stibee',
    actionUrl,
    hiddenFields: [],
    sourceTag,
  };
}
