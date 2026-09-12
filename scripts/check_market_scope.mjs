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
console.log('check_market_scope: OK');
