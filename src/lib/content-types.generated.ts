/* eslint-disable */
/**
 * Generated from scripts/schema/*.schema.json — do not edit manually.
 * Regenerate: npm run gen:types
 */
export type DailyEntry = {
  [k: string]: unknown;
} & {
  date: string;
  market: "KR" | "US";
  status: "pick" | "no_pick";
  stock?: {
    symbol: string;
    name: LocalizedText;
    exchange: string;
    currency: "KRW" | "USD";
  };
  scores?: {
    composite: number;
    growth: number;
    valuation: number;
    momentum: number;
    quality: number;
    threshold: number;
  };
  reasoning?: {
    summary?: LocalizedText;
    growth?: LocalizedText;
    valuation?: LocalizedText;
    momentum?: LocalizedText;
    quality?: LocalizedText;
    risks?: LocalizedText[];
  };
  meta?: {
    generatedAt: string;
    candidatesScreened: number;
    excludedRecent: number;
    skippedMarketCap?: number;
    noData?: number;
    errors?: number;
  };
};

export interface LocalizedText {
  ko: string;
  en: string;
}

export interface Manifest {
  dates: string[];
  lastUpdated: string;
}
