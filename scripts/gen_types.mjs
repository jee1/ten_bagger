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

async function buildTypes() {
  const daily = await compileFromFile(join(schemaDir, 'daily-entry.schema.json'), {
    bannerComment: '',
    additionalProperties: false,
    enableConstEnums: true,
  });

  const manifest = await compileFromFile(join(schemaDir, 'manifest.schema.json'), {
    bannerComment: '',
    additionalProperties: false,
    enableConstEnums: true,
  });

  const body = [daily, manifest]
    .map((chunk) => chunk.replace(/^\/\*[\s\S]*?\*\/\s*/u, '').trim())
    .join('\n\n');

  return `${BANNER}${body}\n`;
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
