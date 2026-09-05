import type { LocalizedText } from './types';

export type Lang = 'ko' | 'en';

export const labels = {
  siteName: { ko: '텐베거 데일리', en: 'Ten Bagger Daily' } satisfies LocalizedText,
  tagline: {
    ko: '매일 하나의 텐베거 후보, 규칙과 데이터로 선정합니다.',
    en: 'One ten-bagger candidate per day, selected by rules and data.',
  } satisfies LocalizedText,
  today: { ko: '오늘', en: 'Today' } satisfies LocalizedText,
  archive: { ko: '달력', en: 'Archive' } satisfies LocalizedText,
  methodology: { ko: '선정 방법', en: 'Methodology' } satisfies LocalizedText,
  noPickTitle: {
    ko: '오늘은 텐베거 후보가 없습니다',
    en: 'No ten-bagger candidate today',
  } satisfies LocalizedText,
  noPickBody: {
    ko: '임계 점수를 넘는 종목이 없습니다. 기준을 만족할 때만 추천합니다.',
    en: 'No stock passed the score threshold. We only publish when criteria are met.',
  } satisfies LocalizedText,
  marketKR: { ko: '한국', en: 'Korea' } satisfies LocalizedText,
  marketUS: { ko: '미국', en: 'United States' } satisfies LocalizedText,
  scores: { ko: '점수', en: 'Scores' } satisfies LocalizedText,
  composite: { ko: '복합', en: 'Composite' } satisfies LocalizedText,
  size: { ko: '규모', en: 'Size' } satisfies LocalizedText,
  growth: { ko: '성장', en: 'Growth' } satisfies LocalizedText,
  valuation: { ko: '밸류', en: 'Valuation' } satisfies LocalizedText,
  entry: { ko: '진입', en: 'Entry' } satisfies LocalizedText,
  momentum: { ko: '모멘텀', en: 'Momentum' } satisfies LocalizedText,
  quality: { ko: '품질', en: 'Quality' } satisfies LocalizedText,
  risks: { ko: '리스크', en: 'Risks' } satisfies LocalizedText,
  disclaimer: {
    ko: '본 사이트는 투자 권유가 아닙니다. 모든 투자 결정과 손실은 본인 책임입니다.',
    en: 'This site is not investment advice. All investment decisions and losses are your own responsibility.',
  } satisfies LocalizedText,
  viewDetail: { ko: '상세 보기', en: 'View details' } satisfies LocalizedText,
  prevMonth: { ko: '이전 달', en: 'Previous' } satisfies LocalizedText,
  nextMonth: { ko: '다음 달', en: 'Next' } satisfies LocalizedText,
  pick: { ko: '선정', en: 'Pick' } satisfies LocalizedText,
  none: { ko: '없음', en: 'None' } satisfies LocalizedText,
  companyProfile: { ko: '회사 소개', en: 'Company profile' } satisfies LocalizedText,
  sector: { ko: '섹터', en: 'Sector' } satisfies LocalizedText,
  industry: { ko: '산업', en: 'Industry' } satisfies LocalizedText,
  topCandidates: { ko: '당일 Top-5 후보', en: "Today's Top-5 candidates" } satisfies LocalizedText,
  topCandidatesHelp: {
    ko: '투명성을 위한 순위·축 점수입니다. 추가 추천이 아닙니다. 일 1픽 규칙은 그대로입니다.',
    en: 'Ranking and axis scores for transparency — not extra picks. One published pick per day still applies.',
  } satisfies LocalizedText,
  performance: { ko: '성과', en: 'Performance' } satisfies LocalizedText,
  performanceCumulative: {
    ko: '누적 성과',
    en: 'Cumulative performance',
  } satisfies LocalizedText,
  performanceAsOf: { ko: '기준일', en: 'As of' } satisfies LocalizedText,
  performanceHypothetical: {
    ko: '실제 펀드가 아닌 가상 포트폴리오입니다.',
    en: 'This is a hypothetical portfolio, not a fund.',
  } satisfies LocalizedText,
  performanceEqualWeight: {
    ko: '동일가중: 완료된 선정일마다 같은 비중으로 복리합니다(없음 날 제외).',
    en: 'Equal weight: compound completed pick days only (no_pick days excluded).',
  } satisfies LocalizedText,
  performanceIndexNote: {
    ko: '벤치마크는 지수 대리 지표이며 거래 가능한 상품이 아닙니다.',
    en: 'The benchmark is an index proxy and is not a tradable product.',
  } satisfies LocalizedText,
  performanceBenchmarkIdKR: { ko: '벤치마크: KOSPI (KR-KOSPI)', en: 'Benchmark: KOSPI (KR-KOSPI)' } satisfies LocalizedText,
  performanceBenchmarkIdUS: { ko: '벤치마크: S&P 500 (US-SPX)', en: 'Benchmark: S&P 500 (US-SPX)' } satisfies LocalizedText,
  performanceBenchmarkUnavailable: {
    ko: '벤치마크 데이터를 사용할 수 없습니다.',
    en: 'Benchmark data is unavailable.',
  } satisfies LocalizedText,
  performanceSurvivorshipCaveat: {
    ko: '일부 종목은 상장폐지되었거나 생존 상태가 불확실합니다.',
    en: 'Some names are delisted or have uncertain survivorship status.',
  } satisfies LocalizedText,
  performanceEmptyTitle: {
    ko: '표시할 성과 데이터가 없습니다',
    en: 'No performance data to show',
  } satisfies LocalizedText,
  performanceEmptyBody: {
    ko: '이 시장에 게시된 성과 측정값이 아직 없습니다.',
    en: 'No published performance measurements are available for this market yet.',
  } satisfies LocalizedText,
  performanceHorizonUnavailable: {
    ko: '아직 사용할 수 없음',
    en: 'Not yet available',
  } satisfies LocalizedText,
  performanceHorizons: { ko: '기간별 성과', en: 'Horizons' } satisfies LocalizedText,
  performanceSecondaryHorizons: {
    ko: '엔지니어링 기간 (H20 / H60)',
    en: 'Engineering horizons (H20 / H60)',
  } satisfies LocalizedText,
  performanceMarket: { ko: '시장', en: 'Market' } satisfies LocalizedText,
  horizon1M: { ko: '1개월', en: '1M' } satisfies LocalizedText,
  horizon3M: { ko: '3개월', en: '3M' } satisfies LocalizedText,
  horizon6M: { ko: '6개월', en: '6M' } satisfies LocalizedText,
  horizon1Y: { ko: '1년', en: '1Y' } satisfies LocalizedText,
  horizonH20: { ko: 'H20', en: 'H20' } satisfies LocalizedText,
  horizonH60: { ko: 'H60', en: 'H60' } satisfies LocalizedText,
  performancePortfolio: { ko: '포트폴리오', en: 'Portfolio' } satisfies LocalizedText,
  performanceBenchmark: { ko: '벤치마크', en: 'Benchmark' } satisfies LocalizedText,
  performanceAvgPick: { ko: '평균 픽', en: 'Avg pick' } satisfies LocalizedText,
  performanceAvgBench: { ko: '평균 벤치', en: 'Avg bench' } satisfies LocalizedText,
  performanceTableDate: { ko: '날짜', en: 'Date' } satisfies LocalizedText,
  performanceTableSymbol: { ko: '종목', en: 'Symbol' } satisfies LocalizedText,
  performanceTablePortfolio: { ko: '포트폴리오', en: 'Portfolio' } satisfies LocalizedText,
  performanceTableBench: { ko: '벤치', en: 'Bench' } satisfies LocalizedText,
} as const;

export function t(text: LocalizedText, lang: Lang): string {
  return text[lang];
}

export function label(key: keyof typeof labels, lang: Lang): string {
  return labels[key][lang];
}

export function shortText(text: string, maxChars = 150): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxChars) {
    return trimmed;
  }
  const clipped = trimmed.slice(0, maxChars);
  const lastSpace = clipped.lastIndexOf(' ');
  const cut = lastSpace > maxChars / 2 ? clipped.slice(0, lastSpace) : clipped;
  return `${cut.replace(/[.,;]+$/, '')}…`;
}
