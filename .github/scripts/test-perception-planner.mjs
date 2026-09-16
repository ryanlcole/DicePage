import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('apps/rist-world/wwwroot/shaelvien-perception-planner.js', 'utf8');

function loadPlanner(profile) {
  const shaelvien = {
    runtimeVersion: 'test-runtime',
    ClientPerception: {
      modes: ['semantic', 'local-render', 'pixel-delta', 'encoded-media'],
      profile: () => profile
    }
  };
  const sandbox = { window: { Shaelvien: shaelvien } };
  vm.runInNewContext(source, sandbox, { filename: 'shaelvien-perception-planner.js' });
  return sandbox.window.Shaelvien.PerceptionPlanner;
}

const reducedMotionProfile = Object.freeze({
  supportedModes: Object.freeze({
    semantic: true,
    'local-render': true,
    'pixel-delta': true,
    'encoded-media': true
  }),
  accessibility: Object.freeze({
    reducedMotion: true,
    forcedColors: false,
    increasedContrast: false
  })
});

const planner = loadPlanner(reducedMotionProfile);
assert.ok(planner, 'planner should register');
assert.equal(planner.canonical, false);

assert.throws(
  () => planner.plan({ offerId: 'unauthorized', candidates: [{ representationId: 'a', mode: 'semantic' }] }),
  /authorized and presentation-equivalent/,
  'planner must reject offers without trusted authorized-equivalent declaration'
);

const plan = planner.plan({
  offerId: 'accessibility-filter',
  authorizedEquivalent: true,
  candidates: [
    {
      representationId: 'motion-heavy-local',
      mode: 'local-render',
      priority: 0,
      accessibility: { reducedMotionSafe: false, forcedColorsSafe: true, increasedContrastSafe: true }
    },
    {
      representationId: 'reduced-motion-pixels',
      mode: 'pixel-delta',
      priority: 1,
      accessibility: { reducedMotionSafe: true, forcedColorsSafe: true, increasedContrastSafe: true }
    },
    {
      representationId: 'reduced-motion-semantic',
      mode: 'semantic',
      priority: 2,
      accessibility: { reducedMotionSafe: true, forcedColorsSafe: true, increasedContrastSafe: true }
    }
  ]
});

assert.equal(plan.ok, true);
assert.equal(plan.selected.representationId, 'reduced-motion-pixels');
assert.equal(plan.selected.mode, 'pixel-delta');
assert.deepEqual(
  Array.from(plan.fallbacks, item => item.representationId),
  ['reduced-motion-semantic'],
  'incompatible motion-heavy candidate must not appear in fallback chain'
);
assert.equal(plan.authority, 'none');
assert.equal(plan.executes, false);
assert.equal(plan.localOnly, true);

const forcedColorsPlanner = loadPlanner(Object.freeze({
  supportedModes: Object.freeze({ semantic: true, 'local-render': true, 'pixel-delta': false, 'encoded-media': false }),
  accessibility: Object.freeze({ reducedMotion: false, forcedColors: true, increasedContrast: false })
}));
const none = forcedColorsPlanner.plan({
  offerId: 'no-compatible-accessible-mode',
  authorizedEquivalent: true,
  candidates: [
    {
      representationId: 'not-forced-colors-safe',
      mode: 'semantic',
      priority: 0,
      accessibility: { reducedMotionSafe: true, forcedColorsSafe: false, increasedContrastSafe: true }
    }
  ]
});
assert.equal(none.ok, false);
assert.equal(none.reason, 'no-compatible-authorized-representation');
assert.equal(none.selected, null);
assert.equal(none.executes, false);

console.log('Perception planner behavior verified: trusted offers required, accessibility filters applied, fallbacks bounded, planner remains non-authoritative and non-executing.');
