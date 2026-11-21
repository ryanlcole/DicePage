/**
 * Shaelvien / Endemar isolated Cloudflare Workers Free hosting preflight.
 * NONCANONICAL; health-only. No credentials, sessions, private state, gameplay,
 * Durable Objects, telemetry, or permissions are granted by this Worker.
 */
const HEADER = Object.freeze({
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'no-store',
  'X-Content-Type-Options': 'nosniff',
});

export default {
  async fetch(request) {
    const path = new URL(request.url).pathname;
    if (request.method !== 'GET' || path !== '/health') {
      return new Response(JSON.stringify({error: 'NOT_FOUND'}), {
        status: 404,
        headers: HEADER,
      });
    }
    return new Response(JSON.stringify({
      service: 'shaelvien-endemar-preflight',
      classification: 'NONCANONICAL_PREFLIGHT',
      state: 'HOSTING_PROBE_ONLY',
      gameServer: false,
      persistentWorld: false,
      authenticatedPlayers: false,
    }), {status: 200, headers: HEADER});
  },
};
