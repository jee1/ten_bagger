import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { before, describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';

import { sanitizeReasoningForDisplay } from './reasoningDisplay.ts';
import type { DailyReasoning } from './types.ts';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '../..');

/** Reasoning text must not expose raw missing-metric tokens (not i18n badge en:"None"). */
const FORBIDDEN_RENDER_TOKENS = /\b(nan|NaN|Infinity)\b|None(?:%|(?=[\s,—.\-]|$))/;

const LEGACY_MISSING_METRICS_DATE = '2026-09-11';
const LEGACY_REPORT_DATE = '2026-09-22';

const LEGACY_ENTRY_KO =
  '12개월 가격대 nan%, 52주 고점 대비 nan% — 진입 점수 59.0.';
const LEGACY_ENTRY_EN = '12M price range nan%, nan% from 52W high — entry score 59.0.';
const LEGACY_MOMENTUM_KO = '6개월 수익률 nan% — 보조 모멘텀 점수 100.0.';
const LEGACY_MOMENTUM_EN = '6M return nan% — auxiliary momentum score 100.0.';

const GENERATED_ENTRY_KO =
  '12개월 가격대 데이터 없음, 52주 고점 대비 데이터 없음 — 진입 점수 59.0.' +
  ' (가격 이력 부족: 기본 진입 점수 59.0 적용; 해당 점수는 복합에 포함되며 선정은 복합 임계 70.0 기준)';
const GENERATED_ENTRY_EN =
  '12M price range No data, No data from 52W high — entry score 59.0.' +
  ' (insufficient price history: default entry score 59.0; score still enters composite; selection uses composite threshold 70.0)';

function legacyReasoning(): DailyReasoning {
  return {
    summary: { ko: '요약', en: 'Summary' },
    growth: { ko: '성장', en: 'Growth' },
    valuation: { ko: 'PER None, PEG None — 밸류 점수 70.0.', en: 'P/E None, PEG None — valuation score 70.0.' },
    momentum: { ko: LEGACY_MOMENTUM_KO, en: LEGACY_MOMENTUM_EN },
    entry: { ko: LEGACY_ENTRY_KO, en: LEGACY_ENTRY_EN },
    risks: [{ ko: '리스크', en: 'Risk' }],
  };
}

function assertSafeLocalized(text: string): void {
  assert.doesNotMatch(text, FORBIDDEN_RENDER_TOKENS);
  assert.doesNotMatch(text, /데이터 없음%/);
  assert.doesNotMatch(text, /No data%/);
}

function dailyDetailHtml(date: string): string {
  return readFileSync(join(repoRoot, 'dist/daily', date, 'index.html'), 'utf8');
}

describe(`legacy ${LEGACY_REPORT_DATE} entry/momentum reasoning display`, () => {
  it('renders Korean without forbidden tokens and with default-score rule', () => {
    const { entry, momentum, valuation } = sanitizeReasoningForDisplay(legacyReasoning());

    assert.ok(entry);
    assertSafeLocalized(entry.ko);
    assert.match(entry.ko, /12개월 가격대 데이터 없음, 52주 고점 대비 데이터 없음/);
    assert.match(entry.ko, /기본 진입 점수 59\.0 적용/);
    assert.match(entry.ko, /복합 임계 70\.0 기준/);
    assert.doesNotMatch(valuation.ko, /기본 진입 점수/);

    assertSafeLocalized(momentum.ko);
    assert.match(momentum.ko, /6개월 수익률 데이터 없음 — 보조 모멘텀 점수 100\.0\./);
    assert.match(momentum.ko, /기본 모멘텀 점수 100\.0 적용/);
    assert.match(momentum.ko, /복합 임계 70\.0 기준/);
  });

  it('renders English without forbidden tokens and with default-score rule', () => {
    const { entry, momentum, valuation } = sanitizeReasoningForDisplay(legacyReasoning());

    assert.ok(entry);
    assertSafeLocalized(entry.en);
    assert.match(entry.en, /12M price range No data, No data from 52W high/);
    assert.match(entry.en, /default entry score 59\.0/);
    assert.match(entry.en, /composite threshold 70\.0/);
    assert.doesNotMatch(valuation.en, /default entry score/);

    assertSafeLocalized(momentum.en);
    assert.match(momentum.en, /6M return No data — auxiliary momentum score 100\.0\./);
    assert.match(momentum.en, /default momentum score 100\.0/);
    assert.match(momentum.en, /composite threshold 70\.0/);
  });

  it('does not duplicate notes on newly generated reasoning', () => {
    const reasoning = legacyReasoning();
    reasoning.entry = { ko: GENERATED_ENTRY_KO, en: GENERATED_ENTRY_EN };

    const { entry } = sanitizeReasoningForDisplay(reasoning);
    assert.ok(entry);
    assert.equal((entry.ko.match(/가격 이력 부족/g) ?? []).length, 1);
    assert.equal((entry.en.match(/insufficient price history/gi) ?? []).length, 1);
  });
});

describe('Daily detail HTML (legacy missing metrics)', { timeout: 180_000 }, () => {
  before(() => {
    execSync('npm run build', { cwd: repoRoot, encoding: 'utf8', stdio: 'pipe' });
  });

  it('renders Korean missing-data labels without forbidden tokens', () => {
    const html = dailyDetailHtml(LEGACY_MISSING_METRICS_DATE);

    assert.doesNotMatch(html, FORBIDDEN_RENDER_TOKENS);
    assert.match(html, /PER 데이터 없음, PEG 데이터 없음/);
    assert.doesNotMatch(html, /PER None/);
    assert.doesNotMatch(html, /데이터 없음%/);
  });

  it('embeds English missing-data copy in bilingual reasoning markup', () => {
    const html = dailyDetailHtml(LEGACY_MISSING_METRICS_DATE);

    assert.match(html, /P\/E No data, PEG No data/);
    assert.doesNotMatch(html, /P\/E None/);
    assert.doesNotMatch(html, /No data%/);
  });
});
