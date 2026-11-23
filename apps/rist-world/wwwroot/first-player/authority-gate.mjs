/** Experimental trusted-side command gate for the Endemar synthetic world.
 * Not wired into the public client or a deployed server. Not a login system.
 * A server must supply the effective principal and capability decision from
 * trusted authentication + Recursive Authority, never from request JSON.
 */
import {intent, validate} from './core.mjs';

const ALLOWED = new Set(['move','gather','drink','eat','plant','rest','talk']);
const DIRECTIONS = new Set(['north','south','east','west']);
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const record = value => value !== null && typeof value === 'object' &&
  !Array.isArray(value) && (Object.getPrototypeOf(value) === Object.prototype ||
    Object.getPrototypeOf(value) === null);

/** Execute one command against an isolated candidate, committing only on success.
 * Caller owns persistence, session authentication, rate limits, and audit writes.
 * All of these are REQUIRED before any production integration.
 *
 * @param {object} world server-held synthetic world snapshot
 * @param {object} request untrusted wire data {sequence, verb, arg}
 * @param {object} authority trusted server-derived {principalId, playerId, nextSequence, canAct}
 * @returns {{accepted:boolean,reason:string,world:object,nextSequence:number}}
 */
export function applyAuthorizedIntent(world,request,authority) {
  const deny = reason => ({accepted:false,reason,world,nextSequence:authority?.nextSequence??null});
  // Untrusted persisted snapshots can be malformed; reject rather than throw.
  try { if (!record(world) || !validate(world)) return deny('INVALID_WORLD'); }
  catch { return deny('INVALID_WORLD'); }
  if (!authority || typeof authority !== 'object' ||
      typeof authority.principalId !== 'string' || !authority.principalId ||
      authority.playerId !== world.player.id ||
      authority.canAct !== true ||
      !Number.isSafeInteger(authority.nextSequence) || authority.nextSequence<1 ||
      authority.nextSequence===Number.MAX_SAFE_INTEGER)
    return deny('AUTHORITY_DENIED');
  // Only plain JSON-style records are eligible. Never invoke getters supplied
  // by the wire client while inspecting fields or allow authority keys through.
  let keys;
  try {
    if (!record(request)) return deny('INVALID_REQUEST');
    const descriptors=Object.getOwnPropertyDescriptors(request);
    keys=Object.keys(descriptors);
    if (keys.some(key=>!['sequence','verb','arg'].includes(key) ||
        !own(descriptors[key],'value'))) return deny('INVALID_REQUEST');
  } catch { return deny('INVALID_REQUEST'); }
  if (keys.some(key=>!['sequence','verb','arg'].includes(key)) ||
      !Number.isSafeInteger(request.sequence) ||
      request.sequence !== authority.nextSequence) return deny('INVALID_SEQUENCE');
  if (typeof request.verb !== 'string' || !ALLOWED.has(request.verb))
    return deny('INVALID_INTENT');
  if (request.verb === 'move' && !DIRECTIONS.has(request.arg))
    return deny('INVALID_DIRECTION');
  if (request.verb === 'talk' &&
      (typeof request.arg !== 'string' || request.arg.length>96))
    return deny('INVALID_TARGET');
  if (!['move','talk'].includes(request.verb) && own(request,'arg') && request.arg!==null)
    return deny('UNEXPECTED_ARGUMENT');
  let candidate, result;
  try { candidate=structuredClone(world); result=intent(candidate,request.verb,request.arg); }
  catch { return deny('EXECUTION_REJECTED'); }
  if (!result?.ok || !validate(candidate)) return deny('RULE_REJECTED');
  return {accepted:true,reason:'ACCEPTED',world:candidate,
    nextSequence:authority.nextSequence+1};
}
