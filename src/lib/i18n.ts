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
  priceBasisPageTitle: {
    ko: '002780.KS 가격 기준 검증',
    en: '002780.KS price-basis validation',
  } satisfies LocalizedText,
  priceBasisPageDescription: {
    ko:
      '주식병합(1:10)으로 일시적으로 +898%처럼 보였던 002780.KS 픽의 가격 기준을 어떻게 검증·수정했는지 설명합니다. 투자 권유가 아닙니다.',
    en:
      'How we validated and corrected price basis for pick 002780.KS after a temporary +898% display around a 1-for-10 reverse split. Not investment advice.',
  } satisfies LocalizedText,
  about: { ko: '소개', en: 'About' } satisfies LocalizedText,
  noPickTitle: {
    ko: '오늘은 텐베거 후보가 없습니다',
    en: 'No ten-bagger candidate today',
  } satisfies LocalizedText,
  noPickBody: {
    ko: '임계 점수를 넘는 종목이 없습니다. 기준을 만족할 때만 공개합니다.',
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
    ko: '누적 성과(모델)',
    en: 'Cumulative (modeled)',
  } satisfies LocalizedText,
  performanceAsOf: { ko: '기준일', en: 'As of' } satisfies LocalizedText,
  performanceHypothetical: {
    ko: '실제 펀드·복수 보유 포트폴리오가 아닙니다. 완료된 일별 픽 수익률을 순서대로 복리한 가상 수치입니다(보유 기간이 겹칠 수 있음).',
    en: 'Not a live fund or multi-position portfolio. Hypothetical compounding of completed per-pick returns in sequence (holding windows may overlap).',
  } satisfies LocalizedText,
  performanceEqualWeight: {
    ko: '픽별 통계: 완료된 선정일만 동일 가중으로 평균·복리합니다(없음 날 제외). 동시 보유 배분 모델이 아닙니다.',
    en: 'Per-pick stats: equal-weight mean/compound of completed pick days only (no_pick excluded). Not a simultaneous allocation model.',
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
  performanceHorizonSamples: { ko: '완료 표본', en: 'Completed samples' } satisfies LocalizedText,
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
  performancePortfolio: { ko: '모델 누적', en: 'Modeled cumulative' } satisfies LocalizedText,
  performanceBenchmark: { ko: '벤치마크', en: 'Benchmark' } satisfies LocalizedText,
  performanceAvgPick: { ko: '평균 픽(픽별)', en: 'Avg pick (per-pick)' } satisfies LocalizedText,
  performanceAvgBench: { ko: '평균 벤치', en: 'Avg bench' } satisfies LocalizedText,
  performanceTableDate: { ko: '날짜', en: 'Date' } satisfies LocalizedText,
  performanceTableSymbol: { ko: '종목', en: 'Symbol' } satisfies LocalizedText,
  performanceTablePortfolio: { ko: '모델 누적', en: 'Modeled cum.' } satisfies LocalizedText,
  performanceTableBench: { ko: '벤치', en: 'Bench' } satisfies LocalizedText,
  performancePriceAdjustment: {
    ko: '가격 기준',
    en: 'Price basis',
  } satisfies LocalizedText,
  performancePriceBasisIncomplete: {
    ko: '가격 조정·단위 검증이 아직 완료되지 않았습니다. 큰 수익률(예: 002780.KS)은 검증 전까지 참고용입니다.',
    en: 'Price-adjustment / unit validation is incomplete. Large returns (e.g. 002780.KS) are provisional until validation completes.',
  } satisfies LocalizedText,
  performancePriceBasisIncompleteTitle: {
    ko: '가격 조정·단위 검증 미완료',
    en: 'Price-basis validation incomplete',
  } satisfies LocalizedText,
  performancePriceBasisCompleteTitle: {
    ko: '가격 기준 검증 완료',
    en: 'Price basis validated',
  } satisfies LocalizedText,
  performancePriceBasisComplete: {
    ko: '가격은 yfinance vendor 조정(분할·배당, auto_adjust) 기준입니다.',
    en: 'Prices use yfinance vendor adjustment (splits and dividends, auto_adjust).',
  } satisfies LocalizedText,
  performancePriceBasisCompleteKR: {
    ko:
      '002780.KS(2026-07-31 픽)의 +898% 이상 수치는 2026-09-07 시행 1:10 주식병합의 일시적 미반영이었고, 현재는 집계에 유지·표시합니다. 해당 픽의 H20/1M 청산가는 거래정지 구간의 forward-fill(Volume 0)입니다.',
    en:
      'The former +898% on 002780.KS (2026-07-31 pick) was a transient pre-consolidation mismatch around the 1-for-10 reverse split effective 2026-09-07; the pick stays in aggregates. Its H20/1M exit price is a suspension forward-fill (Volume 0).',
  } satisfies LocalizedText,
  performancePriceAdjustmentAdjustedAuto: {
    ko: 'vendor 조정 (auto_adjust)',
    en: 'vendor adjusted (auto_adjust)',
  } satisfies LocalizedText,
  performancePriceBasisNoteLink: {
    ko: '검증 노트',
    en: 'validation note',
  } satisfies LocalizedText,
  performanceZeroVolumeCaveat: {
    ko: '일부 측정값의 진입·청산가가 거래정지 구간 vendor forward-fill(Volume 0, OHLC 동일)입니다. 실제 체결가와 다를 수 있습니다.',
    en: 'Some measurements use entry/exit prices from vendor forward-fills during trading suspensions (Volume 0, flat OHLC). They may differ from tradable prints.',
  } satisfies LocalizedText,
  performanceExcess: { ko: '초과 성과', en: 'Excess' } satisfies LocalizedText,
  performanceExcessPending: {
    ko: '표본·벤치마크·공개 지평(1M–1Y) 게이트 충족 시 산출',
    en: 'Computed once sample, benchmark coverage, and a presentation horizon (1M–1Y) pass the gate',
  } satisfies LocalizedText,
  performanceSamplesPending: {
    ko: '표본이 쌓이면 자동으로 채워집니다',
    en: 'Fills in automatically as samples accumulate',
  } satisfies LocalizedText,
  threshold: { ko: '임계', en: 'Threshold' } satisfies LocalizedText,
  screened: { ko: '스크리닝', en: 'Screened' } satisfies LocalizedText,
  scoreAxesLegend: {
    ko: '막대 순서: 규모 · 성장 · 밸류 · 진입 · 모멘텀 · 품질',
    en: 'Bars: size · growth · valuation · entry · momentum · quality',
  } satisfies LocalizedText,
  moatLabel: { ko: '해자', en: 'Moat' } satisfies LocalizedText,
  megatrendLabel: { ko: '메가트렌드', en: 'Megatrend' } satisfies LocalizedText,
  contents: { ko: '목차', en: 'Contents' } satisfies LocalizedText,
  calendarScoreLegend: { ko: '복합 점수', en: 'Composite score' } satisfies LocalizedText,
  calendarUnpublished: { ko: '미공개', en: 'Unpublished' } satisfies LocalizedText,
  calendarRotationNote: {
    ko: '홀수일 한국, 짝수일 미국 · 최근 30일 중복 종목은 제외됩니다.',
    en: 'Odd days Korea, even days US · symbols picked in the last 30 days are excluded.',
  } satisfies LocalizedText,
  pickFreshToday: { ko: '오늘의 픽', en: "Today's pick" } satisfies LocalizedText,
  pickFreshLatest: { ko: '최신 픽', en: 'Latest pick' } satisfies LocalizedText,
  pickFreshHint: {
    ko: '오늘 리포트는 아직 준비되지 않았습니다. 새 픽은 매일 오전 6시(KST)에 공개됩니다.',
    en: "Today's report isn't ready yet. New picks publish daily at 06:00 KST.",
  } satisfies LocalizedText,
  homeReportGenerated: {
    ko: '리포트 생성',
    en: 'Report generated',
  } satisfies LocalizedText,
  homeTitle: {
    ko: '규칙 기반 일일 종목 스크리닝',
    en: 'Daily rule-based stock screening',
  } satisfies LocalizedText,
  homeDescription: {
    ko:
      '한국·미국 시장에서 규칙과 데이터로 하루 하나의 텐베거 후보를 기록합니다. 선정 이유·리스크·일정을 공개하며 수익을 보장하지 않습니다.',
    en:
      'One rule-based ten-bagger candidate per day across Korea and US markets — with reasons, risks, and schedule published. No return promises.',
  } satisfies LocalizedText,
  homeHeroHead: {
    ko: '규칙과 데이터로, 하루 하나의 KR/US 종목 후보를 공개합니다.',
    en: 'One Korea or US candidate per day — by rules and data.',
  } satisfies LocalizedText,
  homeHeroSub: {
    ko:
      '회원가입 없이 Score v2 가중치·임계·선정 이유를 그대로 볼 수 있습니다. 투자 권유가 아니며 수익을 약속하지 않습니다.',
    en:
      'No signup. See Score v2 weights, threshold, and selection reasons as published. Not investment advice; no return promises.',
  } satisfies LocalizedText,
  homeHeroCtaMethodology: {
    ko: '선정 방법 보기',
    en: 'See methodology',
  } satisfies LocalizedText,
  homeHeroCtaPerformance: {
    ko: '누적 기록(가상) 보기',
    en: 'View modeled record',
  } satisfies LocalizedText,
  aboutTitle: {
    ko: '소개·FAQ',
    en: 'About & FAQ',
  } satisfies LocalizedText,
  aboutDescription: {
    ko:
      '텐베거 데일리(Finnaut)가 무엇인지, 투자 권유가 아닌 이유, Score v2·일일 1후보·브랜드 구분을 설명합니다.',
    en:
      'What Finnaut Ten Bagger Daily is: not investment advice, Score v2, one daily candidate, and brand distinction.',
  } satisfies LocalizedText,
  aboutLead: {
    ko:
      '텐베거 데일리는 Finnaut가 운영하는 규칙 기반 일일 스크리닝 기록 사이트입니다. 연구·참고용이며 투자 권유·수익 보장이 아닙니다.',
    en:
      'Ten Bagger Daily is Finnaut’s rule-based daily screening record. For research only — not investment advice or return promises.',
  } satisfies LocalizedText,
  aboutBrandHeading: {
    ko: '다른 “텐배거” 사이트와의 차이',
    en: 'How this differs from other “tenbagger” sites',
  } satisfies LocalizedText,
  aboutBrandBody: {
    ko:
      '유료 차트팩·리딩방·블로그형 장기 리서치와 목적이 다릅니다. 텐베거 데일리는 일일 공개 스크리닝 기록에 초점을 두며, 공식 URL은 tenbagger.finnaut.com 입니다.',
    en:
      'Unlike paid chart packs, signal rooms, or long-form blog research, Ten Bagger Daily focuses on a daily public screening record. Official URL: tenbagger.finnaut.com.',
  } satisfies LocalizedText,
  aboutFaqHeading: {
    ko: '자주 묻는 질문',
    en: 'Frequently asked questions',
  } satisfies LocalizedText,
  aboutLinksHeading: {
    ko: '관련 페이지',
    en: 'Related pages',
  } satisfies LocalizedText,
  newcomerTitle: {
    ko: '이 사이트는 무엇을 하나요?',
    en: 'What is this site?',
  } satisfies LocalizedText,
  newcomerBody: {
    ko:
      '한국·미국 시장을 번갈아 스크리닝해 규칙 기반으로 하루 하나의 후보 종목을 기록합니다. 선정 이유와 리스크를 함께 공개하고, 매일 오전 6시(KST)에 새 리포트가 올라갑니다. 연구·참고용이며 투자 수익을 약속하지 않습니다.',
    en:
      'We screen Korea and US markets on a schedule and record one rule-based candidate per day. Each report includes selection reasons and risks; new reports publish daily at 06:00 KST. For research only — no return promises.',
  } satisfies LocalizedText,
  newcomerLinks: {
    ko: '선정 방법과 누적 성과를 확인하세요.',
    en: 'See how picks are made and historical results.',
  } satisfies LocalizedText,
  rssCta: { ko: '일일 기록 피드', en: 'Daily report feed' } satisfies LocalizedText,
  rssHint: {
    ko: '피드 리더에 주소를 추가해 새 기록을 받아보세요.',
    en: 'Add this feed in your reader to follow new reports.',
  } satisfies LocalizedText,
  shareCta: { ko: '일일 링크 공유', en: 'Share daily link' } satisfies LocalizedText,
  shareShared: { ko: '공유 메뉴를 열었습니다', en: 'Share menu opened' } satisfies LocalizedText,
  shareCopied: { ko: '링크를 복사했습니다', en: 'Link copied' } satisfies LocalizedText,
  shareCancelled: { ko: '공유가 취소되었습니다', en: 'Share cancelled' } satisfies LocalizedText,
  shareManualHint: {
    ko: '아래 주소를 선택해 복사해 주세요.',
    en: 'Select and copy the URL below.',
  } satisfies LocalizedText,
  shareManualUrlLabel: {
    ko: '공유 링크',
    en: 'Share link',
  } satisfies LocalizedText,
  shareFailed: {
    ko: '공유할 수 없습니다. 아래 주소를 직접 복사해 주세요.',
    en: 'Could not share. Please copy the URL below.',
  } satisfies LocalizedText,
} as const;

export function localeToLang(locale: string | undefined): Lang {
  return locale === 'en' ? 'en' : 'ko';
}

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
