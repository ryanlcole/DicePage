/** Proposed server boundary for the experimental Endemar world.
 * This module validates syntax only. Authentication, ownership, replay protection,
 * persistence, and sequencing MUST be enforced by a trusted server.
 * Never use browser-provided identity, role or expected tick as authorization.
 */
export const AUTHORITY_CONTRACT = 'endemar-intent/1';
export const ALLOWED_VERBS = Object.freeze(['move','gather','drink','eat','plant','rest','talk']);
const directions = new Set(['north','south','east','west']);
const safeId = /^[a-z0-9][a-z0-9:_-]{0,79}$/i;
const own = (o,k) => Object.prototype.hasOwnProperty.call(o,k);

export function parseIntentEnvelope(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value))
    return {ok:false,error:'INVALID_ENVELOPE'};
  const keys = Object.keys(value);
  if (keys.some(k => !['version','requestId','verb','arg'].includes(k)))
    return {ok:false,error:'UNTRUSTED_FIELDS'};
  if (value.version !== AUTHORITY_CONTRACT || typeof value.requestId !== 'string'
      || !safeId.test(value.requestId) || typeof value.verb !== 'string'
      || !ALLOWED_VERBS.includes(value.verb))
    return {ok:false,error:'INVALID_INTENT'};
  if (value.verb === 'move' && !directions.has(value.arg))
    return {ok:false,error:'INVALID_DIRECTION'};
  if (value.verb === 'talk' && (typeof value.arg !== 'string' || !safeId.test(value.arg)))
    return {ok:false,error:'INVALID_TARGET'};
  if (!['move','talk'].includes(value.verb) && own(value,'arg'))
    return {ok:false,error:'UNEXPECTED_ARGUMENT'};
  return {ok:true,intent:{version:AUTHORITY_CONTRACT,requestId:value.requestId,
    verb:value.verb,...(own(value,'arg')?{arg:value.arg}:{})}};
}

export function serverRequirements() {
  return Object.freeze({
    classification:'PROPOSED_CONTRACT_NOT_DEPLOYED',
    authentication:'Trusted server authenticates session independently of request body',
    authorization:'Server binds session to player and world, never accepts client owner/GM flags',
    ordering:'Server atomically checks requestId replay and authoritative world revision',
    mutation:'Only server validates and applies permitted intent to persistent world',
    observation:'ReLiC and RIOT receive read-only snapshots, never mutation capability'
  });
}
