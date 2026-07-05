export interface LocalizedText {
  ko: string;
  en: string;
}

export interface DailyStock {
  symbol: string;
  name: LocalizedText;
  exchange: string;
  currency: 'KRW' | 'USD';
}

export interface DailyScores {
  composite: number;
  growth: number;
  valuation: number;
  momentum: number;
  quality: number;
  threshold: number;
}

export interface DailyReasoning {
  summary: LocalizedText;
  growth: LocalizedText;
  valuation: LocalizedText;
  momentum: LocalizedText;
  quality?: LocalizedText;
  risks: LocalizedText[];
}

export interface DailyMeta {
  generatedAt: string;
  candidatesScreened: number;
  excludedRecent: number;
  skippedMarketCap?: number;
  noData?: number;
  errors?: number;
}

export interface DailyEntry {
  date: string;
  market: 'KR' | 'US';
  status: 'pick' | 'no_pick';
  stock?: DailyStock;
  scores?: DailyScores;
  reasoning?: DailyReasoning;
  meta?: DailyMeta;
}

export interface Manifest {
  dates: string[];
  lastUpdated: string;
}
