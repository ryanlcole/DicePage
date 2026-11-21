import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../tools/cloudflare-setup/preflight-worker.mjs';

const run = (method, path) => worker.fetch(new Request(`https://localhost${path}`, {method}));

test('health responds 200 with explicitly non-game status', async () => {
  const response = await run('GET', '/health');
  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-type'), /application\/json/);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.deepEqual(await response.json(), {
    service: 'shaelvien-endemar-preflight',
    classification: 'NONCANONICAL_PREFLIGHT',
    state: 'HOSTING_PROBE_ONLY',
    gameServer: false,
    persistentWorld: false,
    authenticatedPlayers: false,
  });
});

test('root, game endpoints and unknown routes fail closed', async () => {
  for (const path of ['/', '/api/endemar/health', '/api/endemar/session', '/api/endemar/intent', '/unknown']) {
    const response = await run('GET', path);
    assert.equal(response.status, 404, path);
    assert.deepEqual(await response.json(), {error: 'NOT_FOUND'});
  }
});

test('non-GET request to health also fails closed', async () => {
  for (const method of ['POST', 'PUT', 'DELETE']) {
    const response = await run(method, '/health');
    assert.equal(response.status, 404);
  }
});
