// @ts-check
import { defineConfig } from 'astro/config';

const site = process.env.SITE_URL ?? 'https://tenbagger.finnaut.com';
const base = process.env.BASE_PATH ?? '/';

// https://astro.build/config
export default defineConfig({
  site,
  base,
  output: 'static',
});
