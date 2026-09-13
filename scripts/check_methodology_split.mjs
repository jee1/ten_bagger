#!/usr/bin/env node
/** Assert public methodology stays Score v2 summary; engineer notes linked once. */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const dist = join(process.cwd(), 'dist');
const pages = ['methodology/index.html', 'en/methodology/index.html'];
const engineerNoteUrl =
  'https://github.com/jee1/ten_bagger/blob/main/docs/architecture/score-v3-candidates.md';
/** KO + EN spans each carry the handoff link — same pattern as price-basis URLs. */
const EXPECTED_ENGINEER_LINKS_PER_PAGE = 2;
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

const notePath = join(process.cwd(), 'docs/architecture/score-v3-candidates.md');
if (!existsSync(notePath)) {
  console.error('check_methodology_split: docs/architecture/score-v3-candidates.md missing');
  process.exit(1);
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

  const linkCount = html.split(engineerNoteUrl).length - 1;
  if (linkCount !== EXPECTED_ENGINEER_LINKS_PER_PAGE) {
    console.error(
      `check_methodology_split: ${rel} must contain engineer note URL exactly ${EXPECTED_ENGINEER_LINKS_PER_PAGE} times, got ${linkCount}`,
    );
    process.exit(1);
  }
}

console.log('check_methodology_split: OK');
