#!/usr/bin/env node
/** Generate TypeScript types from JSON Schema (single source of truth). */

import { compileFromFile } from 'json-schema-to-typescript';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const schemaDir = join(root, 'scripts', 'schema');
const outPath = join(root, 'src', 'lib', 'content-types.generated.ts');

const BANNER = `/* eslint-disable */
/**
 * Generated from scripts/schema/*.schema.json — do not edit manually.
 * Regenerate: npm run gen:types
 */
`;

const SCHEMAS = [
  'daily-entry.schema.json',
  'manifest.schema.json',
  'ledger.schema.json',
  'performance-bundle.schema.json',
  'walk-forward-report.schema.json',
];

async function buildTypes() {
  const chunks = [];
  for (const name of SCHEMAS) {
    const compiled = await compileFromFile(join(schemaDir, name), {
      bannerComment: '',
      additionalProperties: false,
      enableConstEnums: true,
    });
    chunks.push(compiled.replace(/^\/\*[\s\S]*?\*\/\s*/u, '').trim());
  }

  return `${BANNER}${chunks.join('\n\n')}\n`;
}

async function main() {
  const check = process.argv.includes('--check');
  const next = await buildTypes();

  if (check) {
    const current = readFileSync(outPath, 'utf8');
    if (current !== next) {
      console.error('content-types.generated.ts is out of date. Run: npm run gen:types');
      process.exit(1);
    }
    console.log('Generated types are up to date');
    return;
  }

  writeFileSync(outPath, next, 'utf8');
  console.log(`Wrote ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
