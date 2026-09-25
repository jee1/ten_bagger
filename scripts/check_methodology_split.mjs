#!/usr/bin/env node
/** Assert public methodology stays Score v2 summary; no visitor-facing GitHub repo links. */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const dist = join(process.cwd(), 'dist');
const pages = ['methodology/index.html', 'en/methodology/index.html'];
const forbiddenRepoUrl = 'https://github.com/jee1/ten_bagger';
/** Section-only markers; handoff link may say "Score v3" once per locale. */
const forbidden = [
  'id="v3"',
  'Measurement-gated · not live',
  '측정 게이트 · 미적용',
  'not a live Score v2 weight',
  'WEIGHT_GROWTH',
  'backtest_screen.py',
  'ADR 0004',
  'gated-box',
];
const requiredWeights = ['25%', '20%', '15%', '10%'];

function readHtml(rel) {
  const path = join(dist, rel);
  if (!existsSync(path)) {
    console.error(`check_methodology_split: missing ${rel}`);
    process.exit(1);
  }
  return readFileSync(path, 'utf8');
}

for (const rel of pages) {
  const html = readHtml(rel);

  for (const needle of forbidden) {
    if (html.includes(needle)) {
      console.error(`check_methodology_split: ${rel} must not contain "${needle}"`);
      process.exit(1);
    }
  }

  if (!html.includes('70.0')) {
    console.error(`check_methodology_split: ${rel} must contain 70.0 threshold`);
    process.exit(1);
  }
  for (const pct of requiredWeights) {
    if (!html.includes(pct)) {
      console.error(`check_methodology_split: ${rel} must contain weight ${pct}`);
      process.exit(1);
    }
  }

  const koCount = (html.match(/data-i18n-show="ko"/g) ?? []).length;
  const enCount = (html.match(/data-i18n-show="en"/g) ?? []).length;
  if (koCount !== enCount || koCount === 0) {
    console.error(
      `check_methodology_split: ${rel} KO/EN parity failed (ko=${koCount}, en=${enCount})`,
    );
    process.exit(1);
  }

  if (html.includes(forbiddenRepoUrl)) {
    console.error(`check_methodology_split: ${rel} must not link to ${forbiddenRepoUrl}`);
    process.exit(1);
  }

  if (!html.includes('/methodology/price-basis/')) {
    console.error(`check_methodology_split: ${rel} must link to on-site price-basis validation`);
    process.exit(1);
  }
}

console.log('check_methodology_split: OK');
