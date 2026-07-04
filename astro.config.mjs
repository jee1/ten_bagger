// @ts-check
import { defineConfig } from 'astro/config';

const site = process.env.SITE_URL ?? 'https://example.github.io/ten_bagger';
const base = process.env.BASE_PATH ?? '/ten_bagger';

// https://astro.build/config
export default defineConfig({
  site,
  base,
  output: 'static',
});
