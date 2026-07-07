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
