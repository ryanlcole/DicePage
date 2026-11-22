/**
 * Read-only Endemar pilot snapshot verifier for two or more viewer clients.
 * Accepts only already-authorized server snapshot responses. It does not
 * authenticate any account, grant owner/GM powers, or send mutation requests.
 * This is NONCANONICAL; never use a client-provided view as world authority.
 */
import {SIZE} from '../wwwroot/first-player/core.mjs';

export const SNAPSHOT_SCOPE = 'NONCANONICAL_END_EMAR_PILOT';
const WORLD = 'end:pilot:one';
const own = (x,k)=>Object.prototype.hasOwnProperty.call(x,k);
const isObject = x=>x!==null && typeof x==='object' && !Array.isArray(x);
const safeId = /^[a-z0-9][a-z0-9:_-]{0,79}$/i;
const xyz = n=>Number.isSafeInteger(n)&&n>=0&&n<SIZE;
const safeTick = n=>Number.isSafeInteger(n)&&n>=0&&n<=300000;
const safeRevision = n=>Number.isSafeInteger(n)&&n>=0;
const freezeActor = x=>Object.freeze({id:x.id,x:x.x,y:x.y});

function reject(error){return {ok:false,error};}

/** Parse and sanitize ONLY a read-only server view, never a raw world model. */
export function parseServerSnapshot(snapshot) {
  if(!isObject(snapshot) || Object.keys(snapshot).sort().join(',')!==
      'classification,revision,scope,status,view,worldId')
    return reject('UNEXPECTED_SNAPSHOT_FIELDS');
  if(snapshot.classification!=='VERIFIED_SIMULATION_RESULT'||
     snapshot.scope!==SNAPSHOT_SCOPE||snapshot.worldId!==WORLD||
     !safeRevision(snapshot.revision))return reject('UNTRUSTED_SNAPSHOT_ENVELOPE');
  const v=snapshot.view,s=snapshot.status;
  if(!isObject(v)||!isObject(s)||v.tier!=='LOCAL'||
     !safeTick(v.tick)||s.tick!==v.tick||v.playerId!=='shaelvien:player:first'||
     !isObject(v.player)||v.player.id!==v.playerId||
     !xyz(v.player.x)||!xyz(v.player.y)||
     !Array.isArray(v.actors)||v.actors.length>64||
     !isObject(v.weather)||typeof v.weather.phase!=='string'||
     !['clear','rain','wind','frost'].includes(v.weather.phase))
    return reject('INVALID_SNAPSHOT_PROJECTION');
  const actors=[],ids=new Set([v.playerId]);
  for(const a of v.actors){
    if(!isObject(a)||typeof a.id!=='string'||!safeId.test(a.id)||
       ids.has(a.id)||!xyz(a.x)||!xyz(a.y))
      return reject('DUPLICATE_OR_INVALID_ACTOR');
    ids.add(a.id);actors.push(freezeActor(a));
  }
  const result=Object.freeze({
    classification:'OBSERVED_NONCANONICAL_SERVER_PROJECTION',
    verifiedServerIdentity:false, // Client JSON cannot authenticate the remote host.
    worldId:WORLD,revision:snapshot.revision,tick:v.tick,
    player:freezeActor(v.player),actors:Object.freeze(actors),
    weatherPhase:v.weather.phase,
    immutableWorldAuthority:false, // This read-only client never owns truth.
  });
  return {ok:true,state:result};
}

/**
 * Check revision continuity; an unchanged revision MUST have identical
 * projection, and a changed world/player identity or rollback is rejected.
 */
export function acceptSnapshot(snapshot,previous=null) {
  const parsed=parseServerSnapshot(snapshot);
  if(!parsed.ok)return parsed;
  const now=parsed.state;
  if(previous!==null){
    if(!isObject(previous)||previous.classification!=='OBSERVED_NONCANONICAL_SERVER_PROJECTION')
      return reject('INVALID_PREVIOUS_PROJECTION');
    if(previous.worldId!==now.worldId||previous.player.id!==now.player.id)
      return reject('IDENTITY_CHANGED');
    if(now.revision<previous.revision)return reject('STALE_REVISION');
    if(now.tick<previous.tick)return reject('TIME_REWIND');
    if(now.revision===previous.revision){
      return JSON.stringify(previous)===JSON.stringify(now)
        ? {ok:true,status:'UNCHANGED',state:previous}
        : reject('REVISION_CONTENT_CONFLICT');
    }
  }
  return {ok:true,status:'NEW_REVISION',state:now};
}

/** Safe read-only local cache, not a server or a client-side simulation. */
export class SnapshotObserver {
  #last=null;
  accept(snapshot){
    const result=acceptSnapshot(snapshot,this.#last);
    if(result.ok)this.#last=result.state;
    return {ok:result.ok,status:result.status??null,error:result.error??null};
  }
  read(){return this.#last ? structuredClone(this.#last) : null;}
}
