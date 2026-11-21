/**
 * Read-only public ReLiC-Continuity ecology observer.
 *
 * This is a DIFFERENT, NONCANONICAL synthetic ecology from the local Endemar game.
 * It is not a game synchronization protocol, login, authority, or persistence layer.
 * It consumes public GitHub data without credentials or write capability.
 */
export const ECOLOGY_STATE_URL = 'https://raw.githubusercontent.com/ryanlcole/ReLiC-Continuity/experiment-autonomous-ecology-state/experiments/continuity_ecology/state.json';
export const ECOLOGY_SOURCE_URL = 'https://github.com/ryanlcole/ReLiC-Continuity/tree/experiment-autonomous-ecology-state/experiments/continuity_ecology';
const MAX_BYTES = 3_000_000;
const idPattern = /^[A-Za-z0-9:_-]{1,80}$/;

export function summarizeEcology(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      data.schema !== 'relic-ecology/1' || data.policy !== 'observation_only' ||
      !Number.isSafeInteger(data.tick) || data.tick < 0 || data.tick > 20000 ||
      !Array.isArray(data.agents) || data.agents.length > 100 ||
      !Array.isArray(data.history) || data.history.length > 20000) {
    throw new Error('UNSUPPORTED_PUBLIC_CHECKPOINT');
  }
  const identities = new Set();
  const agents = data.agents.map(agent => {
    if (!agent || typeof agent !== 'object' || typeof agent.id !== 'string' ||
        !idPattern.test(agent.id) || identities.has(agent.id) ||
        !['alive', 'dead', 'deleted'].includes(agent.status) ||
        !Number.isSafeInteger(agent.seen) || agent.seen < 0) {
      throw new Error('INVALID_PUBLIC_AGENT');
    }
    identities.add(agent.id);
    return Object.freeze({
      id: agent.id,
      status: agent.status,
      observations: agent.seen,
      parents: Array.isArray(agent.parents)
        ? agent.parents.filter(x => typeof x === 'string' && idPattern.test(x)).slice(0, 8)
        : [],
    });
  });
  const last = data.history.at(-1);
  if (last && (!Number.isSafeInteger(last.seq) || last.seq < 0 ||
      !Number.isSafeInteger(last.tick) || last.tick > data.tick ||
      typeof last.hash !== 'string' || !/^[a-f0-9]{64}$/.test(last.hash))) {
    throw new Error('INVALID_PUBLIC_EVENT');
  }
  return Object.freeze({
    classification: 'OBSERVATION_OF_PUBLIC_SYNTHETIC_STATE',
    canonical: false,
    project: 'ReLiC-Continuity ecology experiment',
    distinctFromShaelvien: true,
    tick: data.tick,
    agents,
    alive: agents.filter(a => a.status === 'alive').length,
    reportedEvents: data.history.length,
    lastEventSequence: last?.seq ?? null,
    hashChainVerified: false, // A hash-shaped field alone does NOT verify event lineage.
    source: ECOLOGY_SOURCE_URL,
  });
}

export async function readEcologyCheckpoint(fetcher = fetch) {
  const response = await fetcher(ECOLOGY_STATE_URL, {
    method: 'GET', credentials: 'omit', cache: 'no-store',
  });
  if (!response?.ok) throw new Error('PUBLIC_CHECKPOINT_UNAVAILABLE');
  const header = response.headers?.get?.('content-length');
  if (header && Number(header) > MAX_BYTES) throw new Error('PUBLIC_CHECKPOINT_TOO_LARGE');
  const raw = await response.text();
  if (raw.length > MAX_BYTES) throw new Error('PUBLIC_CHECKPOINT_TOO_LARGE');
  let parsed;
  try { parsed = JSON.parse(raw); }
  catch { throw new Error('PUBLIC_CHECKPOINT_NOT_JSON'); }
  return summarizeEcology(parsed);
}
