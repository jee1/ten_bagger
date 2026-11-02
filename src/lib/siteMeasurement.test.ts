import assert from 'node:assert/strict';
import test from 'node:test';
import {
  cfWebAnalyticsBeaconJson,
  resolveGoogleSiteVerification,
  trimPublicEnv,
} from './siteMeasurement.ts';

test('trimPublicEnv', () => {
  assert.equal(trimPublicEnv('  abc '), 'abc');
  assert.equal(trimPublicEnv(undefined), '');
});

test('resolveGoogleSiteVerification prefers env over fallback', () => {
  assert.equal(resolveGoogleSiteVerification('from-env', 'fallback'), 'from-env');
  assert.equal(resolveGoogleSiteVerification('  ', 'fallback'), 'fallback');
});

test('cfWebAnalyticsBeaconJson', () => {
  assert.equal(cfWebAnalyticsBeaconJson(''), null);
  assert.equal(cfWebAnalyticsBeaconJson('tok'), '{"token":"tok"}');
});
