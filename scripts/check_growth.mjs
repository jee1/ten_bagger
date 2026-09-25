#!/usr/bin/env node
/** Growth loop regression: newcomer intro, RSS/share CTAs, daily meta, subpath share URLs. */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const dist = join(process.cwd(), 'dist');
const base = process.env.BASE_PATH ?? '/';
const site = process.env.SITE_URL ?? 'https://tenbagger.finnaut.com';
const baseNorm = base.endsWith('/') ? base : `${base}/`;

const { buildDailyShareUrl } = await import('../src/lib/share.ts');
const { joinSitePath } = await import('../src/lib/rss.ts');

function normalizeSite(url) {
  return url.replace(/\/$/, '');
}

function readHtml(rel) {
  const path = join(dist, rel);
  if (!existsSync(path)) {
    console.error(`check_growth: missing ${rel}`);
    process.exit(1);
  }
  return readFileSync(path, 'utf8');
}

const manifest = JSON.parse(readFileSync(join(process.cwd(), 'content/manifest.json'), 'utf8'));
const newestDate = [...manifest.dates].sort().at(-1);
if (!newestDate) {
  console.error('check_growth: manifest has no dates');
  process.exit(1);
}

const expectedShareUrl = buildDailyShareUrl(site, baseNorm, 'ko', newestDate);
const expectedRssUrl = joinSitePath(normalizeSite(site), 'rss.xml');

const indexHtml = readHtml('index.html');
if (!indexHtml.includes('class="newcomer-intro"')) {
  console.error('check_growth: home missing newcomer intro');
  process.exit(1);
}
if (!indexHtml.includes('data-growth-rss')) {
  console.error('check_growth: home missing RSS CTA');
  process.exit(1);
}
if (!indexHtml.includes('data-growth-follow')) {
  console.error('check_growth: home missing follow page link');
  process.exit(1);
}
if (!indexHtml.includes('data-growth-share')) {
  console.error('check_growth: home missing share CTA');
  process.exit(1);
}
if (!indexHtml.includes(`href="${expectedRssUrl}"`)) {
  console.error(`check_growth: RSS link must use absolute URL (${expectedRssUrl})`);
  process.exit(1);
}
if (!indexHtml.includes(`>${expectedRssUrl}<`)) {
  console.error('check_growth: RSS displayed text must be absolute URL');
  process.exit(1);
}
if (!indexHtml.includes('data-i18n-attr="content:homeDescription"')) {
  console.error('check_growth: home meta must use service description key');
  process.exit(1);
}
const newcomerPos = indexHtml.indexOf('class="newcomer-intro"');
const retentionPos = indexHtml.indexOf('data-retention-actions');
const dailyCardPos = indexHtml.indexOf('daily-card');
if (retentionPos === -1 || dailyCardPos === -1 || retentionPos < dailyCardPos) {
  console.error('check_growth: retention actions must appear after the daily report on home');
  process.exit(1);
}
if (newcomerPos === -1 || newcomerPos > dailyCardPos) {
  console.error('check_growth: newcomer intro must stay before the daily report');
  process.exit(1);
}
if (indexHtml.includes('구독 여부는 확인되지 않습니다') || indexHtml.includes('Subscription is not confirmed')) {
  console.error('check_growth: RSS copy must not expose subscription confirmation wording');
  process.exit(1);
}

const dailyKo = readHtml(`daily/${newestDate}/index.html`);
if (!dailyKo.includes('data-growth-rss') || !dailyKo.includes('data-growth-share')) {
  console.error('check_growth: daily detail missing retention CTAs');
  process.exit(1);
}
if (!dailyKo.includes('property="og:description"')) {
  console.error('check_growth: daily detail missing og:description');
  process.exit(1);
}
if (dailyKo.includes('data-i18n-attr="content:tagline"')) {
  console.error('check_growth: daily detail must not use tagline meta overwrite');
  process.exit(1);
}
if (!dailyKo.includes('data-description-ko=') || !dailyKo.includes('data-description-en=')) {
  console.error('check_growth: daily detail must expose bilingual description metadata');
  process.exit(1);
}
if (!dailyKo.includes('data-title-ko=') || !dailyKo.includes('data-title-en=')) {
  console.error('check_growth: daily detail must expose bilingual title metadata');
  process.exit(1);
}

const dailyEn = readHtml(`en/daily/${newestDate}/index.html`);
const enBody = dailyEn.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
if (!enBody.includes('data-growth-share')) {
  console.error('check_growth: en daily missing share CTA');
  process.exit(1);
}
if (!dailyEn.includes('<html lang="en">')) {
  console.error('check_growth: en daily must set lang=en');
  process.exit(1);
}

const shareDateAttr = dailyKo.match(/data-share-date="([^"]+)"/);
if (!shareDateAttr || shareDateAttr[1] !== newestDate) {
  console.error('check_growth: share action must use dated daily slug, not a baked absolute URL');
  process.exit(1);
}
const siteAttr = dailyKo.match(/data-share-site="([^"]+)"/);
if (!siteAttr || normalizeSite(siteAttr[1]) !== normalizeSite(site)) {
  console.error(
    `check_growth: share action must carry configured SITE_URL (${site}), got ${siteAttr?.[1] ?? 'missing'}`,
  );
  process.exit(1);
}
if (baseNorm !== '/' && !dailyKo.includes(`data-share-base="${baseNorm}"`)) {
  console.error(`check_growth: share action must carry configured BASE_PATH (${baseNorm})`);
  process.exit(1);
}

const expectedEnShareUrl = buildDailyShareUrl(site, baseNorm, 'en', newestDate);
if (!expectedShareUrl.includes(`/daily/${newestDate}/`)) {
  console.error(`check_growth: expected ko share URL malformed: ${expectedShareUrl}`);
  process.exit(1);
}
if (baseNorm !== '/' && expectedShareUrl.includes(`${baseNorm.replace(/\/$/, '')}${baseNorm}`)) {
  console.error(`check_growth: share URL duplicates BASE_PATH: ${expectedShareUrl}`);
  process.exit(1);
}
if (!expectedShareUrl.includes('utm_source=share') || !expectedShareUrl.includes('utm_campaign=reader-share')) {
  console.error('check_growth: share URL must include fixed UTM params');
  process.exit(1);
}
if (expectedShareUrl.includes('lang=') || expectedShareUrl.includes('market=')) {
  console.error('check_growth: share URL must not carry private query params');
  process.exit(1);
}
if (!expectedEnShareUrl.includes('/en/daily/')) {
  console.error(`check_growth: expected en share URL malformed: ${expectedEnShareUrl}`);
  process.exit(1);
}

const titleMatch = dailyKo.match(/<title[^>]*>([^<]+)<\/title>/);
if (!titleMatch || !titleMatch[1].includes(newestDate)) {
  console.error('check_growth: daily title must include date');
  process.exit(1);
}

const methodologyHtml = readHtml('methodology/index.html');
if (!methodologyHtml.includes('data-i18n-attr="content:tagline"')) {
  console.error('check_growth: default pages must restore tagline description localization');
  process.exit(1);
}

const followKo = readHtml('follow/index.html');
if (!followKo.includes(expectedRssUrl) || !followKo.includes('follow-disclaimer')) {
  console.error('check_growth: follow page must show RSS URL and disclaimer');
  process.exit(1);
}
if (followKo.includes('github.com')) {
  console.error('check_growth: follow page must not link to GitHub');
  process.exit(1);
}
if (!followKo.includes('준비 중')) {
  console.error('check_growth: follow page must show Telegram preparing state when channel unset');
  process.exit(1);
}

const followEn = readHtml('en/follow/index.html');
if (!followEn.includes('Coming soon') || !followEn.includes(expectedRssUrl)) {
  console.error('check_growth: en follow page must show RSS URL and Telegram preparing state');
  process.exit(1);
}

const aboutKo = readHtml('about/index.html');
if (!aboutKo.includes('follow/')) {
  console.error('check_growth: about page must link to follow page');
  process.exit(1);
}

console.log(`check_growth: OK (${baseNorm}, rss=${expectedRssUrl}, share=${expectedShareUrl})`);
