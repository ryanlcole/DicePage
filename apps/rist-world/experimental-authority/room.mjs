/**
 * NONCANONICAL Endemar first-player server pilot, not the Shaelvien MMO authority.
 * State mutation is confined to this Durable Object. No role or identity is read
 * from client JSON. Does not expose a GM/owner capability or external AI execution.
 */
import {createWorld, advance, intent, view, status} from '../wwwroot/first-player/core.mjs';
import {parseIntentEnvelope} from '../wwwroot/first-player/authority-contract.mjs';

const KEY = 'endemar:experimental-room-v1';
const SCHEMA = 'endemar:experimental-room-v1';
const SESSION_MS = 2 * 60 * 60 * 1000;
const ALARM_MS = 2 * 60 * 1000;
const MAX_REQUESTS = 512;
const MAX_TICKS = 300000;
const CAPABILITY_RE = /^[a-f0-9]{64}$/;
const freezeHeaders = {'Cache-Control':'no-store', 'Content-Type':'application/json; charset=utf-8', 'X-Content-Type-Options':'nosniff'};
function reply(body,statusCode=200){return new Response(JSON.stringify(body),{status:statusCode,headers:freezeHeaders});}
function fresh(now) {return {schema:SCHEMA, world:createWorld(), revision:0, session:null, processed:Object.create(null), operations:0, createdAt:now};}
function capability() {return [...crypto.getRandomValues(new Uint8Array(32))].map(n=>n.toString(16).padStart(2,'0')).join('');}
async function sha256(value){const data = new TextEncoder().encode(value); const bytes = new Uint8Array(await crypto.subtle.digest('SHA-256',data)); return [...bytes].map(x=>x.toString(16).padStart(2,'0')).join('');}
function bearer(request){const match=/^Bearer ([a-f0-9]{64})$/.exec(request.headers.get('authorization')||'');return match?.[1]||null;}
function validSession(state, hash, now){return state?.schema===SCHEMA && state.session?.hash===hash && now < state.session.expiresAt;}
function publicState(state){return {classification:'VERIFIED_SIMULATION_RESULT',scope:'NONCANONICAL_END_EMAR_PILOT',worldId:'end:pilot:one',revision:state.revision,view:view(state.world,'LOCAL'),status:status(state.world)};}

/** This is not publicly routable: only the edge Worker has a Durable Object binding. */
export class EndemarRoom {
  constructor(ctx, env){this.ctx=ctx;this.env=env;}
  async fetch(request){
    const path=new URL(request.url).pathname;
    const now=Date.now();
    if(path==='/internal/issue' && request.method==='POST'){
      // Caller must be the edge Worker after its private bootstrap-key check.
      const token=capability();
      const hash=await sha256(token);
      const state=await this.ctx.storage.transaction(async txn=>{
        const state=await txn.get(KEY)??fresh(now);
        if(state.schema!==SCHEMA)throw Error('Unsupported world schema');
        state.session={hash,expiresAt:now+SESSION_MS,playerId:state.world.player.id};
        state.processed=Object.create(null);
        state.operations=0; // New capability invalidates older capabilities and replays.
        await txn.put(KEY,state);
        return state;
      });
      await this.ctx.storage.setAlarm(now+ALARM_MS);
      return reply({classification:'NONCANONICAL_PILOT_SESSION',capability:token,expiresAt:state.session.expiresAt,worldId:'end:pilot:one'});
    }
    const token=bearer(request);
    if(!token)return reply({error:'SESSION_REQUIRED'},401);
    const hash=await sha256(token);
    if(path==='/internal/snapshot' && request.method==='GET'){
      const state=await this.ctx.storage.get(KEY);
      if(!validSession(state,hash,now))return reply({error:'SESSION_UNAVAILABLE'},401);
      return reply(publicState(state));
    }
    if(path==='/internal/intent' && request.method==='POST'){
      const raw=await request.text();
      if(raw.length>1024)return reply({error:'INTENT_TOO_LARGE'},413);
      let decoded;
      try {decoded=JSON.parse(raw);}catch{return reply({error:'INVALID_JSON'},400);}
      const parsed=parseIntentEnvelope(decoded);
      if(!parsed.ok)return reply({error:parsed.error},400);
      const result=await this.ctx.storage.transaction(async txn=>{
        const state=await txn.get(KEY);
        if(!validSession(state,hash,now))return {code:401,data:{error:'SESSION_UNAVAILABLE'}};
        // A request ID is scoped to the current server-issued capability, not claimed identity.
        // Exact retries are idempotent; a changed action may NEVER inherit an old success.
        // Canonical parsed fields exclude untrusted data, tokens, clocks, and representation.
        const fingerprint=JSON.stringify([parsed.intent.verb, Object.hasOwn(parsed.intent,'arg')?parsed.intent.arg:null]);
        const previous=Object.hasOwn(state.processed,parsed.intent.requestId) ? state.processed[parsed.intent.requestId] : null;
        if(previous){
          // Fail closed on records from an unknown or older schema: no false replay claims.
          if(typeof previous.fingerprint!=='string'||!previous.response)
            return {code:409,data:{error:'REQUEST_ID_UNVERIFIABLE'}};
          if(previous.fingerprint!==fingerprint)
            return {code:409,data:{error:'REQUEST_ID_CONFLICT'}};
          return {code:200,data:{...previous.response,replayed:true}};
        }
        if(state.operations>=MAX_REQUESTS)return {code:429,data:{error:'SESSION_REQUEST_LIMIT'}};
        const action=intent(state.world,parsed.intent.verb,parsed.intent.arg);
        if(action.ok)state.revision++;
        const response={classification:'VERIFIED_SIMULATION_RESULT',action,revision:state.revision,tick:state.world.tick,playerId:state.world.player.id};
        state.processed[parsed.intent.requestId]={fingerprint,response};
        state.operations++;
        await txn.put(KEY,state);
        return {code:200,data:response};
      });
      return reply(result.data,result.code);
    }
    return reply({error:'NOT_FOUND'},404);
  }
  async alarm(){
    const now=Date.now();
    const updated=await this.ctx.storage.transaction(async txn=>{
      const state=await txn.get(KEY);
      if(!state || state.schema!==SCHEMA || state.world.tick>=MAX_TICKS)return false;
      advance(state.world,1);
      state.revision++;
      await txn.put(KEY,state);
      return true;
    });
    if(updated)await this.ctx.storage.setAlarm(now+ALARM_MS);
  }
}
