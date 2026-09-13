#!/usr/bin/env node
/** Assert og:image, hreflang, and /en locale pages in built HTML. */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const dist = join(process.cwd(), 'dist');
const site = 'https://tenbagger.finnaut.com';
const enTagline = 'One ten-bagger candidate per day, selected by rules and data.';
const koTagline = '매일 하나의 텐베거 후보, 규칙과 데이터로 선정합니다.';

function readHtml(rel) {
  const path = join(dist, rel);
  if (!existsSync(path)) {
    console.error(`check_seo_head: missing ${rel}`);
    process.exit(1);
  }
  return readFileSync(path, 'utf8');
}

function pngSize(path) {
  const buf = readFileSync(path);
  if (buf[0] !== 0x89 || buf[1] !== 0x50) {
    console.error(`check_seo_head: ${path} is not a PNG`);
    process.exit(1);
  }
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  return { w, h };
}

const ogPath = join(dist, 'og-default.png');
if (!existsSync(ogPath)) {
  console.error('check_seo_head: dist/og-default.png missing');
  process.exit(1);
}
const { w, h } = pngSize(ogPath);
if (w !== 1200 || h !== 630) {
  console.error(`check_seo_head: og-default.png must be 1200x630, got ${w}x${h}`);
  process.exit(1);
}

const indexHtml = readHtml('index.html');
const ogImageUrl = `${site}/og-default.png`;
if (!indexHtml.includes(`property="og:image" content="${ogImageUrl}"`)) {
  console.error(`check_seo_head: index.html missing og:image ${ogImageUrl}`);
  process.exit(1);
}
if (!indexHtml.includes('property="og:image:width" content="1200"')) {
  console.error('check_seo_head: index.html missing og:image:width');
  process.exit(1);
}
if (!indexHtml.includes('property="og:image:height" content="630"')) {
  console.error('check_seo_head: index.html missing og:image:height');
  process.exit(1);
}
if (!indexHtml.includes('name="twitter:card" content="summary_large_image"')) {
  console.error('check_seo_head: index.html missing twitter:card summary_large_image');
  process.exit(1);
}
if (!indexHtml.includes(`name="twitter:image" content="${ogImageUrl}"`)) {
  console.error('check_seo_head: index.html missing twitter:image');
  process.exit(1);
}
for (const alt of ['hreflang="ko"', 'hreflang="en"', 'hreflang="x-default"']) {
  if (!indexHtml.includes(alt)) {
    console.error(`check_seo_head: index.html missing ${alt}`);
    process.exit(1);
  }
}
if (!indexHtml.includes(`rel="canonical" href="${site}/"`)) {
  console.error(`check_seo_head: index.html canonical must be ${site}/`);
  process.exit(1);
}

const enIndex = readHtml('en/index.html');
if (!enIndex.includes('<html lang="en">')) {
  console.error('check_seo_head: dist/en/index.html must have <html lang="en">');
  process.exit(1);
}
if (!enIndex.includes(`rel="canonical" href="${site}/en/"`)) {
  console.error(
    'check_seo_head: dist/en/index.html canonical must end with /en/ — rewrite/canonical bug if it points at /',
  );
  process.exit(1);
}
const enBody = enIndex.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
if (!enBody.includes(enTagline)) {
  console.error('check_seo_head: dist/en/index.html must contain English tagline in rendered body');
  process.exit(1);
}
if (enBody.includes(koTagline)) {
  console.error('check_seo_head: dist/en/index.html must not contain Korean tagline in rendered body');
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(join(process.cwd(), 'content/manifest.json'), 'utf8'));
const newestDate = [...manifest.dates].sort().at(-1);
if (!newestDate) {
  console.error('check_seo_head: manifest has no dates');
  process.exit(1);
}
readHtml(`en/daily/${newestDate}/index.html`);

const sitemapPath = join(dist, 'sitemap-0.xml');
if (!existsSync(sitemapPath)) {
  console.error('check_seo_head: dist/sitemap-0.xml missing');
  process.exit(1);
}
const sitemap = readFileSync(sitemapPath, 'utf8');
if (!sitemap.includes('/en/')) {
  console.error('check_seo_head: sitemap must contain at least one /en/ URL');
  process.exit(1);
}

const enArchive = readHtml('en/archive/index.html');
const navBlock = enArchive.match(/<div class="calendar-nav">([\s\S]*?)<\/div>/);
if (!navBlock) {
  console.error('check_seo_head: dist/en/archive/index.html missing calendar-nav');
  process.exit(1);
}
const monthNavHrefs = [...navBlock[1].matchAll(/href="([^"]+)"/g)].map((m) => m[1]);
if (monthNavHrefs.length < 2) {
  console.error('check_seo_head: dist/en/archive/index.html must contain prev/next month links');
  process.exit(1);
}
for (const href of monthNavHrefs) {
  if (!href.startsWith('/en/archive/?')) {
    console.error(
      `check_seo_head: en archive month link must start with /en/archive/?, got ${href}`,
    );
    process.exit(1);
  }
}

function walkHtml(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) {
      walkHtml(path, out);
    } else if (name.endsWith('.html')) {
      out.push(path);
    }
  }
  return out;
}

const legacyLangQuery = /href="[^"]*(?:[?&]lang=en(?:&|$|"))/g;
for (const htmlPath of walkHtml(dist)) {
  const html = readFileSync(htmlPath, 'utf8');
  const hit = html.match(legacyLangQuery);
  if (hit) {
    console.error(
      `check_seo_head: ${relative(process.cwd(), htmlPath)} contains legacy lang=en link: ${hit[0]}`,
    );
    process.exit(1);
  }
}

console.log('check_seo_head: OK');
