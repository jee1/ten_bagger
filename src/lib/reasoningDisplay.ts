import type { Lang } from './i18n';
import type { DailyReasoning, LocalizedText } from './types';

const MISSING_LABEL: Record<Lang, string> = { ko: '데이터 없음', en: 'No data' };

/** Legacy committed reports used these defaults when price history was missing. */
const COMPOSITE_THRESHOLD = 70.0;
const LEGACY_ENTRY_DEFAULT_SCORE = 59.0;
const LEGACY_MOMENTUM_DEFAULT_SCORE = 100.0;

const MISSING_NUMERIC_TOKEN = /\b(nan|NaN|Infinity|None)(?=%|\b)/i;
const HAS_PRICE_FACTOR_NOTE =
  /가격 이력 부족|insufficient price history|일부 가격 입력 없음|some price inputs missing/i;

type PriceFactor = 'entry' | 'momentum';

function isMissingMetricValue(value: string): boolean {
  const trimmed = value.trim();
  return MISSING_NUMERIC_TOKEN.test(trimmed) || trimmed === MISSING_LABEL.ko || trimmed === MISSING_LABEL.en;
}

function extractScore(text: string, lang: Lang, factor: PriceFactor): number | null {
  const patterns =
    factor === 'entry'
      ? lang === 'ko'
        ? [/진입 점수 ([\d.]+)/]
        : [/entry score ([\d.]+)/i]
      : lang === 'ko'
        ? [/보조 모멘텀 점수 ([\d.]+)/, /모멘텀 점수 ([\d.]+)/]
        : [/auxiliary momentum score ([\d.]+)/i, /momentum score ([\d.]+)/i];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return Number.parseFloat(match[1]);
  }
  return null;
}

function entryMetricsMissing(raw: string, lang: Lang): { any: boolean; all: boolean } {
  const pattern =
    lang === 'ko'
      ? /12개월 가격대 (.+?), 52주 고점 대비 (.+?) —/
      : /12M price range (.+?), (.+?) from 52W high —/i;
  const match = raw.match(pattern);
  if (!match) return { any: false, all: false };
  const missing = [match[1], match[2]].map(isMissingMetricValue);
  return { any: missing.some(Boolean), all: missing.every(Boolean) };
}

function momentumMetricMissing(raw: string, lang: Lang): { any: boolean; all: boolean } {
  const pattern = lang === 'ko' ? /6개월 수익률 (.+?) —/ : /6M return (.+?) —/i;
  const match = raw.match(pattern);
  if (!match) return { any: false, all: false };
  const missing = isMissingMetricValue(match[1]);
  return { any: missing, all: missing };
}

function fmtScore(value: number): string {
  return value.toFixed(1);
}

function legacyPriceFactorNote(
  lang: Lang,
  factor: PriceFactor,
  score: number,
  allMissing: boolean,
): string {
  const factorKo = factor === 'entry' ? '진입' : '모멘텀';
  const factorEn = factor;
  const scoreText = fmtScore(score);
  const thresholdText = fmtScore(COMPOSITE_THRESHOLD);
  const defaultScore =
    factor === 'entry' ? LEGACY_ENTRY_DEFAULT_SCORE : LEGACY_MOMENTUM_DEFAULT_SCORE;
  const usesDefault = allMissing && score === defaultScore;

  if (usesDefault) {
    if (lang === 'ko') {
      return (
        ` (가격 이력 부족: 기본 ${factorKo} 점수 ${scoreText} 적용; ` +
        `해당 점수는 복합에 포함되며 선정은 복합 임계 ${thresholdText} 기준)`
      );
    }
    return (
      ` (insufficient price history: default ${factorEn} score ${scoreText}; ` +
      `score still enters composite; selection uses composite threshold ${thresholdText})`
    );
  }

  if (lang === 'ko') {
    return (
      ` (일부 가격 입력 없음; ${factorKo} 점수 ${scoreText}는 가용 데이터로 계산; ` +
      `복합에 포함, 선정은 복합 임계 ${thresholdText} 기준)`
    );
  }
  return (
    ` (some price inputs missing; ${factorEn} score ${scoreText} from available data; ` +
    `still enters composite; selection uses composite threshold ${thresholdText})`
  );
}

/** Legacy committed daily JSON may still contain None/nan before regeneration. */
function sanitizeReasoningLine(text: string, lang: Lang): string {
  const missing = MISSING_LABEL[lang];
  return text
    .replace(/\bnan%/gi, missing)
    .replace(/\bNaN%/g, missing)
    .replace(/\bInfinity%/g, missing)
    .replace(/\bNone%/g, missing)
    .replace(/\bNone\b/g, missing)
    .replace(/\bInfinity\b/g, missing)
    .replace(/\bNaN\b/g, missing)
    .replace(/\bnan\b/gi, missing);
}

function sanitizePriceFactorLine(
  raw: string,
  lang: Lang,
  factor: PriceFactor,
): string {
  const sanitized = sanitizeReasoningLine(raw, lang);
  if (!MISSING_NUMERIC_TOKEN.test(raw) || HAS_PRICE_FACTOR_NOTE.test(raw)) {
    return sanitized;
  }

  const missing =
    factor === 'entry' ? entryMetricsMissing(raw, lang) : momentumMetricMissing(raw, lang);
  if (!missing.any) return sanitized;

  const score = extractScore(sanitized, lang, factor);
  if (score == null) return sanitized;

  const trimmed = sanitized.replace(/\s+$/, '');
  const base = trimmed.endsWith('.') ? trimmed.slice(0, -1) : trimmed;
  return `${base}.${legacyPriceFactorNote(lang, factor, score, missing.all)}`;
}

function sanitizeLocalized(text: LocalizedText): LocalizedText {
  return {
    ko: sanitizeReasoningLine(text.ko, 'ko'),
    en: sanitizeReasoningLine(text.en, 'en'),
  };
}

function sanitizePriceFactorLocalized(text: LocalizedText, factor: PriceFactor): LocalizedText {
  return {
    ko: sanitizePriceFactorLine(text.ko, 'ko', factor),
    en: sanitizePriceFactorLine(text.en, 'en', factor),
  };
}

export function sanitizeReasoningForDisplay(reasoning: DailyReasoning): DailyReasoning {
  return {
    summary: sanitizeLocalized(reasoning.summary),
    growth: sanitizeLocalized(reasoning.growth),
    valuation: sanitizeLocalized(reasoning.valuation),
    momentum: sanitizePriceFactorLocalized(reasoning.momentum, 'momentum'),
    quality: reasoning.quality ? sanitizeLocalized(reasoning.quality) : reasoning.quality,
    size: reasoning.size ? sanitizeLocalized(reasoning.size) : reasoning.size,
    entry: reasoning.entry ? sanitizePriceFactorLocalized(reasoning.entry, 'entry') : reasoning.entry,
    risks: reasoning.risks.map((risk) => sanitizeLocalized(risk)),
  };
}
