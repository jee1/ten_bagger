/**
 * App-facing content types. Base shapes come from JSON Schema codegen;
 * pick/no_pick branches use stricter optional fields for Astro templates.
 */
import type {
  DailyEntry as SchemaDailyEntry,
  LocalizedText as SchemaLocalizedText,
  Manifest as SchemaManifest,
} from './content-types.generated';

export type LocalizedText = SchemaLocalizedText;
export type Manifest = SchemaManifest;

export interface DailyReasoning {
  summary: LocalizedText;
  growth: LocalizedText;
  valuation: LocalizedText;
  momentum: LocalizedText;
  quality?: LocalizedText;
  risks: LocalizedText[];
}

export interface DailyStock {
  symbol: string;
  name: LocalizedText;
  exchange: string;
  currency: 'KRW' | 'USD';
  profile?: DailyStockProfile;
}

export interface DailyStockProfile {
  overview: LocalizedText;
  sector?: LocalizedText;
  industry?: LocalizedText;
}

export interface DailyScores {
  composite: number;
  growth: number;
  valuation: number;
  momentum: number;
  quality: number;
  threshold: number;
}

export interface DailyMeta {
  generatedAt: string;
  candidatesScreened: number;
  excludedRecent: number;
  skippedMarketCap?: number;
  noData?: number;
  errors?: number;
}

export interface DailyEntry extends Omit<SchemaDailyEntry, 'stock' | 'scores' | 'reasoning' | 'meta'> {
  stock?: DailyStock;
  scores?: DailyScores;
  reasoning?: DailyReasoning;
  meta?: DailyMeta;
}

/** Ensures hand-written DailyEntry stays compatible with schema codegen. */
export type _DailyEntrySchemaCheck = DailyEntry extends SchemaDailyEntry ? true : never;
