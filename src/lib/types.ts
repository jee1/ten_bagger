/**
 * App-facing content types. Base shapes come from JSON Schema codegen;
 * pick/no_pick branches use stricter optional fields for Astro templates.
 *
 * NOTE: `SchemaDailyEntry`'s generated type carries a top-level index
 * signature (`[k: string]: unknown`), which makes TS collapse indexed access
 * into its nested optional object properties (e.g. `SchemaDailyEntry['stock']`)
 * down to `{}`. That rules out deriving DailyStock/DailyScores/DailyMeta via
 * indexing — they stay hand-written, kept honest by the active
 * `_DailyEntrySchemaCheck` assertion below (a generic-constraint check, not a
 * plain conditional type, so it fails to *compile* — not just silently
 * evaluate to `never` — the moment DailyEntry drifts from the schema).
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
  size?: LocalizedText;
  growth: LocalizedText;
  valuation: LocalizedText;
  entry?: LocalizedText;
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
  size?: number;
  growth: number;
  valuation: number;
  entry?: number;
  momentum: number;
  quality: number;
  threshold: number;
  version?: number;
}

export interface DailyMeta {
  generatedAt: string;
  candidatesScreened: number;
  excludedRecent: number;
  skippedMarketCap?: number;
  skippedRedFlags?: number;
  noData?: number;
  errors?: number;
}

export type DailyEntry = {
  date: string;
  market: 'KR' | 'US';
  status: 'pick' | 'no_pick';
  stock?: DailyStock;
  scores?: DailyScores;
  reasoning?: DailyReasoning;
  meta?: DailyMeta;
};

/**
 * Fails to compile (not just silently evaluate to `never`) if DailyEntry
 * stops structurally matching the generated schema type.
 */
type AssertExtends<T extends U, U> = T;
export type _DailyEntrySchemaCheck = AssertExtends<DailyEntry, SchemaDailyEntry>;
