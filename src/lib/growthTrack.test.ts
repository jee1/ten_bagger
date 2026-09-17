import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { GROWTH_EVENTS, isGrowthTrackingEnabled, trackGrowthEvent } from './growthTrack.ts';

describe('isGrowthTrackingEnabled', () => {
  it('disables on localhost and dev', () => {
    assert.equal(isGrowthTrackingEnabled('localhost', false), false);
    assert.equal(isGrowthTrackingEnabled('tenbagger.finnaut.com', true), false);
  });

  it('enables on production host when not dev', () => {
    assert.equal(isGrowthTrackingEnabled('tenbagger.finnaut.com', false), true);
  });
});

describe('trackGrowthEvent', () => {
  it('counts events without throwing', () => {
    let path = '';
    trackGrowthEvent(
      {
        count: (args) => {
          path = args.path;
        },
      },
      GROWTH_EVENTS.rssClick,
      true,
    );
    assert.equal(path, GROWTH_EVENTS.rssClick);
  });

  it('no-ops when disabled or goatcounter missing', () => {
    trackGrowthEvent(undefined, GROWTH_EVENTS.shareSuccess, true);
    trackGrowthEvent({ count: () => {} }, GROWTH_EVENTS.shareSuccess, false);
  });

  it('swallows errors from blocked or unloaded analytics', () => {
    trackGrowthEvent(
      {
        count: () => {
          throw new Error('blocked');
        },
      },
      GROWTH_EVENTS.rssClick,
      true,
    );
  });
});
