/**
 * Visitor-facing channel URLs. Set `PUBLIC_TELEGRAM_CHANNEL_URL` at build time
 * (e.g. `https://t.me/your_public_channel`) to show a join button on /follow/.
 */
export const TELEGRAM_CHANNEL_URL = (
  import.meta.env.PUBLIC_TELEGRAM_CHANNEL_URL ?? ''
).trim();
