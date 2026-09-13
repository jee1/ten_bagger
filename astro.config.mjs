// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const site = process.env.SITE_URL ?? 'https://tenbagger.finnaut.com';
const base = process.env.BASE_PATH ?? '/';

// https://astro.build/config
export default defineConfig({
  site,
  base,
  output: 'static',
  i18n: {
    locales: ['ko', 'en'],
    defaultLocale: 'ko',
    fallback: { en: 'ko' },
    routing: { prefixDefaultLocale: false, fallbackType: 'rewrite' },
  },
  integrations: [
    sitemap({
      // ponytail: @astrojs/sitemap skips fallback copies of dynamic routes, so
      // /en/daily/* gets no <loc> and /daily/* gets no alternates. Head hreflang in
      // Layout.astro covers those; upgrade path is customPages fed from
      // content/manifest.json if sitemap coverage is ever required.
      i18n: { defaultLocale: 'ko', locales: { ko: 'ko', en: 'en' } },
    }),
  ],
});
