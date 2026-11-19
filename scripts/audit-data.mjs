#!/usr/bin/env node
/**
 * WMM GOV RADAR: read-only source-data quality gate.
 * Run: node scripts/audit-data.mjs
 * No network calls, secret access, or production file modifications.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const load = (name) => JSON.parse(readFileSync(resolve(root, 'data', name), 'utf8'));
const countries = load('countries.json');
const regions = load('regions.json');
const opportunitiesFile = load('opps.json');
const opportunities = opportunitiesFile.items || [];
let errors = 0;
const warn = (msg) => console.warn('WARN:', msg);
const fail = (msg) => { errors++; console.error('ERROR:', msg); };
const uniq = (items, key, category) => {
  const seen = new Set();
  for (const row of items) {
    const value = row?.[key];
    if (!value) { fail(`${category}: missing ${key}`); continue; }
    if (seen.has(value)) fail(`${category}: duplicate ${key}=${value}`);
    seen.add(value);
  }
};
if (!Array.isArray(countries) || !Array.isArray(regions) || !Array.isArray(opportunities)) {
  fail('Source structures must contain countries[], regions[] and opps.items[]');
  process.exit(1);
}
uniq(countries, 'iso', 'country');
uniq(regions, 'code', 'special region');
const countrySet = new Set(countries.map(x => x.iso));
const badParents = regions.filter(x => !countrySet.has(x.parent));
if (badParents.length) fail(`Special regions have missing parent countries: ${badParents.map(x => x.code).join(', ')}`);
const badOppCountries = opportunities.filter(x => !countrySet.has(x.iso));
if (badOppCountries.length) fail(`Opportunities with unknown country: ${badOppCountries.length}`);
const missingSource = opportunities.filter(x => !x.source_url && !x.sourceUrl && !x.url && !x.source);
const noDeadline = opportunities.filter(x => !x.deadline);
const dated = opportunities.filter(x => x.deadline);
const invalidDeadline = dated.filter(x => !/^\d{4}-\d{2}-\d{2}/.test(x.deadline));
const duplicateKeys = new Map();
for (const item of opportunities) {
  const key = [item.iso, item.kind, (item.ko || item.en || '').trim().toLowerCase(), item.deadline || ''].join('|');
  duplicateKeys.set(key, (duplicateKeys.get(key) || 0) + 1);
}
const duplicateCandidates = [...duplicateKeys.values()].filter(n => n > 1).length;
const report = {
  checked_at_utc: new Date().toISOString(),
  countries_registered: countries.length,
  countries_done_flag_true: countries.filter(x => x.done === true).length,
  countries_done_flag_false: countries.filter(x => x.done !== true).length,
  special_regions_registered: regions.length,
  special_regions_done_flag_true: regions.filter(x => x.done === true).length,
  opportunities_total: opportunities.length,
  opportunities_missing_source: missingSource.length,
  opportunities_no_deadline: noDeadline.length,
  opportunities_invalid_deadline_format: invalidDeadline.length,
  opportunities_duplicate_key_groups: duplicateCandidates,
  opportunity_snapshot_updated: opportunitiesFile.updated || null,
  structural_errors: errors
};
console.log(JSON.stringify(report, null, 2));
if (missingSource.length) warn('Business opportunities without traceable source must not be labeled as verified tenders.');
if (duplicateCandidates) warn('Potential duplicate opportunities need human review before removal.');
if (invalidDeadline.length) warn('Invalid deadline strings must be corrected against source documents.');
if (errors) process.exitCode = 1;
