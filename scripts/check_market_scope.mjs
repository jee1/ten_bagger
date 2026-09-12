#!/usr/bin/env node
/** Assert 002780.KS disclosure appears only in the KR performance panel. */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const htmlPath = join(process.cwd(), 'dist/performance/index.html');
const html = readFileSync(htmlPath, 'utf8');
const parts = html.split('data-market-panel="');
if (parts.length < 3) {
  console.error('check_market_scope: expected KR and US data-market-panel sections');
  process.exit(1);
}
const krChunk = parts.find((p) => p.startsWith('KR'));
const usChunk = parts.find((p) => p.startsWith('US'));
if (!krChunk || !usChunk) {
  console.error('check_market_scope: missing KR or US panel chunk');
  process.exit(1);
}

const krMarker = 'data-i18n="performancePriceBasisCompleteKR"';
if (!krChunk.includes(krMarker)) {
  console.error(`check_market_scope: KR panel must contain ${krMarker}`);
  process.exit(1);
}
if (usChunk.includes(krMarker)) {
  const idx = usChunk.indexOf(krMarker);
  console.error(`check_market_scope: US panel must not contain ${krMarker}:\n${usChunk.slice(Math.max(0, idx - 80), idx + 120)}`);
  process.exit(1);
}

/** Inner text of the first span with the given data-i18n key. */
function spanInnerText(chunk, i18nKey) {
  const marker = `data-i18n="${i18nKey}"`;
  const idx = chunk.indexOf(marker);
  if (idx < 0) return null;
  const afterOpen = chunk.indexOf('>', idx);
  if (afterOpen < 0) return null;
  const close = chunk.indexOf('</span>', afterOpen);
  if (close < 0) return null;
  return chunk.slice(afterOpen + 1, close);
}

const krDisclosure = spanInnerText(krChunk, 'performancePriceBasisCompleteKR');
if (!krDisclosure) {
  console.error('check_market_scope: KR panel missing rendered performancePriceBasisCompleteKR span');
  process.exit(1);
}
if (!krDisclosure.includes('002780')) {
  console.error(`check_market_scope: KR disclosure must render ticker 002780, got:\n${krDisclosure}`);
  process.exit(1);
}
if (!krDisclosure.includes('002780.KS')) {
  console.error(`check_market_scope: KR disclosure must render ticker 002780.KS, got:\n${krDisclosure}`);
  process.exit(1);
}

// Exclude doc-link hrefs (filename contains 002780) when scanning US panel body text.
const usBodyText = usChunk.replace(/href="[^"]*"/g, '');
if (usBodyText.includes('002780')) {
  const idx = usBodyText.indexOf('002780');
  console.error(`check_market_scope: US panel must not render ticker 002780:\n${usBodyText.slice(Math.max(0, idx - 80), idx + 120)}`);
  process.exit(1);
}
if (usChunk.includes('002780.KS')) {
  const idx = usChunk.indexOf('002780.KS');
  console.error(`check_market_scope: US panel must not render ticker 002780.KS:\n${usChunk.slice(Math.max(0, idx - 80), idx + 120)}`);
  process.exit(1);
}

console.log('check_market_scope: OK');
