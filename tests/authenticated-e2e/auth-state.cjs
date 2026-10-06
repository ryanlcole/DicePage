'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const runtime = path.join(root, '.e2e-runtime');

function requireTestEnvironment(env = process.env) {
  if (env.SHAELVIEN_TEST_AUTH !== '1' || env.SHAELVIEN_ENVIRONMENT !== 'test' ||
      env.NODE_ENV !== 'test' || env.DOTNET_ENVIRONMENT !== 'Development') {
    throw new Error('Authenticated E2E refused outside explicit local test environment');
  }
}

async function authenticatedContext(browser, persona, options = {}) {
  requireTestEnvironment();
  if (!['user', 'gm'].includes(persona)) throw new Error('Unknown fixture persona');
  const state = JSON.parse(fs.readFileSync(path.join(runtime, '.auth', `${persona}.json`), 'utf8'));
  const origin = new URL(state.origin);
  if (origin.protocol !== 'http:' || origin.hostname !== '127.0.0.1' ||
      origin.origin !== state.origin || !state.token || state.expiresAt * 1000 <= Date.now()) {
    throw new Error('Invalid, nonlocal or expired test session');
  }
  const context = await browser.newContext(options);
  context.setDefaultTimeout(10000);
  // Prevent a local fixture from ever contacting production or a third party.
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    return url.origin === state.origin ? route.continue() : route.abort('blockedbyclient');
  });
  await context.addInitScript(({origin, token, provider, expiresAt}) => {
    if (location.origin !== origin || sessionStorage.getItem('rist.session')) return;
    sessionStorage.setItem('rist.session', token);
    sessionStorage.setItem('rist.session.provider', provider);
    sessionStorage.setItem('rist.session.expiresAt', String(expiresAt));
  }, state);
  // Verify the legitimate backend session before opening a private UI. Never mock /me.
  const response = await context.request.get(`${state.origin}/api/auth/me`, {
    headers: {Authorization: `Bearer ${state.token}`}
  });
  if (response.status() !== 200 || (await response.json()).userId !== state.userId) {
    await context.close();
    throw new Error('Backend rejected fixture session');
  }
  return {context, origin: state.origin, userId: state.userId};
}
module.exports = {authenticatedContext, requireTestEnvironment, runtime};
