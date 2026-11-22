import test from 'node:test';
import assert from 'node:assert/strict';
import edge from '../apps/rist-world/experimental-authority/worker.mjs';
import {EndemarRoom} from '../apps/rist-world/experimental-authority/room.mjs';
import {SnapshotObserver,acceptSnapshot,parseServerSnapshot} from '../apps/rist-world/experimental-authority/snapshot-observer.mjs';

class MemoryStorage {
  constructor(){this.items=new Map();this.nextAlarm=null;}
  async get(k){return structuredClone(this.items.get(k));}
  async put(k,v){this.items.set(k,structuredClone(v));}
  async setAlarm(when){this.nextAlarm=when;}
  async transaction(callback){
    const shadow=new Map([...this.items].map(([k,v])=>[k,structuredClone(v)]));
    const txn={get:async k=>structuredClone(shadow.get(k)),put:async(k,v)=>shadow.set(k,structuredClone(v))};
    const result=await callback(txn);
    this.items=shadow;
    return result;
  }
}
function fixture(){
  const store=new MemoryStorage(),ctx={storage:store};
  const room=new EndemarRoom(ctx,{});
  const binding={idFromName:n=>n,get:id=>({fetch:request=>room.fetch(request)})};
  const env={ENDEMAR_ROOM:binding,ENDEMAR_BOOTSTRAP_KEY:'random-private-key-'.padEnd(48,'x')};
  return {room,store,ctx,env};
}
const request=(path,method='GET',body,token)=>new Request(`https://test.example${path}`,{
  method,headers:{...(token?{authorization:`Bearer ${token}`}:{})},...(body!==undefined?{body:JSON.stringify(body),headers:{...(token?{authorization:`Bearer ${token}`}:{}),'content-type':'application/json'}}:{})
});
const asJson=async r=>({code:r.status,...await r.json()});
async function session(env){const result=await asJson(await edge.fetch(request('/api/endemar/session','POST',undefined,env.ENDEMAR_BOOTSTRAP_KEY),env));assert.equal(result.code,200);return result.capability;}
const move=id=>({version:'endemar-intent/1',requestId:id,verb:'move',arg:'north'});

// Keep all behavior verified through the edge facade that would run in Cloudflare.
test('bootstrap stays disabled without a deployment secret',async()=>{
  const {env}=fixture();delete env.ENDEMAR_BOOTSTRAP_KEY;
  const result=await asJson(await edge.fetch(request('/api/endemar/session','POST',undefined,'made-up-key'.padEnd(48,'a')),env));
  assert.equal(result.code,503);assert.equal(result.error,'BOOTSTRAP_DISABLED');
});
test('bootstrap must match secret and never exposes it in responses',async()=>{
  const {env}=fixture();let result=await asJson(await edge.fetch(request('/api/endemar/session','POST',undefined,'wrong-key'.padEnd(48,'a')),env));
  assert.equal(result.code,403);const cap=await session(env);assert.match(cap,/^[a-f0-9]{64}$/);
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,cap),env));
  assert.equal(snap.code,200);assert.equal(snap.view.player.id,'shaelvien:player:first');assert.equal(snap.revision,0);
  assert.ok(!JSON.stringify(snap).includes(cap));assert.ok(!JSON.stringify(snap).includes(env.ENDEMAR_BOOTSTRAP_KEY));
});
test('untrusted intents cannot mutate and unknown action is rejected',async()=>{
  const {env}=fixture(),token=await session(env);
  for(const field of ['playerId','owner','role','gm','worldId','revision','tick','authority']){
    const r=await asJson(await edge.fetch(request('/api/endemar/intent','POST',{...move(`bad-${field}`),[field]:'owner'},token),env));
    assert.equal(r.code,400);assert.equal(r.error,'UNTRUSTED_FIELDS');
  }
  const bad=await asJson(await edge.fetch(request('/api/endemar/intent','POST',{version:'endemar-intent/1',requestId:'no',verb:'teleport'},token),env));
  assert.equal(bad.code,400);
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));assert.equal(snap.revision,0);
});
test('accepted moves update only trusted world state and monotonic revision',async()=>{
  const {env}=fixture(),token=await session(env);
  const first=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('move-1'),token),env));
  assert.equal(first.code,200);assert.equal(first.action.ok,true);assert.equal(first.revision,1);
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(snap.view.player.y,13);assert.equal(snap.view.player.id,'shaelvien:player:first');
});
test('exact request-id replay returns cached outcome without second mutation',async()=>{
  const {env}=fixture(),token=await session(env);
  const first=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('same-id'),token),env));
  const second=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('same-id'),token),env));
  assert.equal(second.code,200);assert.equal(second.replayed,true);
  assert.equal(second.revision,first.revision);assert.deepEqual(second.action,first.action);
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(snap.view.player.y,13);
});

test('same request id with changed movement is rejected, not reported as successful replay',async()=>{
  const {env,store}=fixture(),token=await session(env);
  const original=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('conflict'),token),env));
  assert.equal(original.action.ok,true);
  const stateBefore=JSON.stringify(await store.get('endemar:experimental-room-v1'));
  const changed=await asJson(await edge.fetch(request('/api/endemar/intent','POST',{...move('conflict'),arg:'south'},token),env));
  assert.deepEqual(changed,{code:409,error:'REQUEST_ID_CONFLICT'});
  assert.equal(JSON.stringify(await store.get('endemar:experimental-room-v1')),stateBefore);
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(snap.view.player.y,13);assert.equal(snap.revision,original.revision);
});

test('same request id with changed verb never inherits an earlier success',async()=>{
  const {env}=fixture(),token=await session(env);
  const original=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('switch-verb'),token),env));
  const changed=await asJson(await edge.fetch(request('/api/endemar/intent','POST',{version:'endemar-intent/1',requestId:'switch-verb',verb:'rest'},token),env));
  assert.deepEqual(changed,{code:409,error:'REQUEST_ID_CONFLICT'});
  const same=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('switch-verb'),token),env));
  assert.equal(same.code,200);assert.equal(same.replayed,true);assert.equal(same.revision,original.revision);
});

test('unverifiable legacy request-id records fail closed without mutation',async()=>{
  const {env,store}=fixture(),token=await session(env);
  const key='endemar:experimental-room-v1',state=await store.get(key);
  state.processed.legacy={classification:'VERIFIED_SIMULATION_RESULT',action:{ok:true},revision:999};
  await store.put(key,state);
  const before=JSON.stringify(await store.get(key));
  const result=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('legacy'),token),env));
  assert.deepEqual(result,{code:409,error:'REQUEST_ID_UNVERIFIABLE'});
  assert.equal(JSON.stringify(await store.get(key)),before);
});

test('request IDs become reusable only after session rotation, not for the stale capability',async()=>{
  const {env}=fixture(),old=await session(env);
  const first=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('session-scoped'),old),env));
  assert.equal(first.action.ok,true);
  const next=await session(env);
  const stale=await asJson(await edge.fetch(request('/api/endemar/intent','POST',{...move('session-scoped'),arg:'south'},old),env));
  assert.equal(stale.code,401);
  const fresh=await asJson(await edge.fetch(request('/api/endemar/intent','POST',{...move('session-scoped'),arg:'south'},next),env));
  assert.equal(fresh.code,200);assert.equal(fresh.action.ok,true);
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,next),env));
  assert.equal(snap.view.player.y,14);
});
test('prototype-like request ids do not receive special privileges',async()=>{
  const {env}=fixture(),token=await session(env);
  const r=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('constructor'),token),env));
  assert.equal(r.code,200);assert.equal(r.action.ok,true);
  const again=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('constructor'),token),env));
  assert.equal(again.replayed,true);
});
test('revoking and rotating capability prevents stale token reuse',async()=>{
  const {env}=fixture(),old=await session(env),fresh=await session(env);
  assert.notEqual(old,fresh);
  assert.equal((await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,old),env))).code,401);
  assert.equal((await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,fresh),env))).code,200);
});
test('session expires and does not accept an action after expiry',async()=>{
  const {env,store}=fixture(),token=await session(env);
  const key='endemar:experimental-room-v1';const state=await store.get(key);state.session.expiresAt=1;await store.put(key,state);
  const r=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('exp'),token),env));
  assert.equal(r.code,401);
});
test('survives object recreation with identity and replay history intact',async()=>{
  const {ctx,env}=fixture(),token=await session(env);
  const prior=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('persist-1'),token),env));
  const restarted=new EndemarRoom(ctx,{});
  env.ENDEMAR_ROOM.get=()=>({fetch:req=>restarted.fetch(req)});
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(snap.revision,prior.revision);assert.equal(snap.view.player.y,13);
  const replay=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('persist-1'),token),env));
  assert.equal(replay.replayed,true);assert.equal(replay.revision,prior.revision);
});
test('alarm advances existing world with original weather and NPC engine',async()=>{
  const {env,room,store}=fixture(),token=await session(env);
  const before=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  await room.alarm();
  const after=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(after.status.tick,before.status.tick+1);assert.equal(after.revision,before.revision+1);
  assert.equal(after.view.actors.length,before.view.actors.length);
  assert.equal(typeof after.status.weather.temperature,'number');assert.ok(store.nextAlarm>Date.now());
});
test('read-only inspection does not advance world or leak capability/hash',async()=>{
  const {env,store}=fixture(),token=await session(env),key='endemar:experimental-room-v1';
  const before=JSON.stringify(await store.get(key));
  const a=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  const b=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(JSON.stringify(await store.get(key)),before);
  assert.equal(a.revision,b.revision);assert.ok(!JSON.stringify(a).includes('hash'));
});
test('internal routes not exposed by edge worker',async()=>{
  const {env}=fixture();
  const r=await asJson(await edge.fetch(request('/internal/issue','POST'),env));assert.equal(r.code,404);
});
test('boundary enforces request size',async()=>{
  const {env}=fixture(),token=await session(env);
  const oversize={...move('size'),padding:'x'.repeat(1300)};
  const r=await asJson(await edge.fetch(request('/api/endemar/intent','POST',oversize,token),env));assert.equal(r.code,413);
});
test('session request quota is bounded and cannot apply action on overflow',async()=>{
  const {env,store}=fixture(),token=await session(env);
  const key='endemar:experimental-room-v1';const state=await store.get(key);state.operations=512;await store.put(key,state);
  const r=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('too-many'),token),env));
  assert.equal(r.code,429);const after=await store.get(key);assert.equal(after.revision,0);
});
test('world is not reinitialized on rotated capability',async()=>{
  const {env}=fixture(),first=await session(env);
  const r=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('before-rotate'),first),env));
  assert.equal(r.revision,1);
  const second=await session(env);
  const snap=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,second),env));
  assert.equal(snap.view.player.y,13);assert.equal(snap.revision,1);
});
test('operator-only booth does not treat RIOT or ReLiC labels as authorization',async()=>{
  const {env}=fixture();
  for(const label of ['RIOT','ReLiC','owner','GM']){
    const r=await asJson(await edge.fetch(new Request('https://test.example/api/endemar/session',{method:'POST',headers:{authorization:`Bearer ${label}`}}),env));
    assert.equal(r.code,403);
  }
});


test('two independent read-only clients converge on the same server revision', async()=>{
  const {env}=fixture(),token=await session(env);
  const a=new SnapshotObserver(),b=new SnapshotObserver();
  const initial=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(a.accept(initial).status,'NEW_REVISION');
  assert.equal(b.accept(initial).status,'NEW_REVISION');
  assert.deepEqual(a.read(),b.read());
  assert.equal(a.read().verifiedServerIdentity,false);
  assert.equal(a.read().classification,'OBSERVED_NONCANONICAL_SERVER_PROJECTION');
  assert.equal(a.read().player.id,'shaelvien:player:first');

  const moved=await asJson(await edge.fetch(request('/api/endemar/intent','POST',move('observer-move'),token),env));
  assert.equal(moved.action.ok,true);
  const next=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(a.accept(next).status,'NEW_REVISION');
  assert.equal(b.accept(next).status,'NEW_REVISION');
  assert.deepEqual(a.read(),b.read());
  assert.equal(a.read().player.y,13);
  assert.equal(a.read().revision,moved.revision);
});

test('stale and conflicting snapshots never roll a client back or invent updates',async()=>{
  const {env}=fixture(),token=await session(env),observer=new SnapshotObserver();
  const before=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(observer.accept(before).ok,true);
  await edge.fetch(request('/api/endemar/intent','POST',move('snapshot-advance'),token),env);
  const after=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(observer.accept(after).status,'NEW_REVISION');
  const valid=observer.read();
  assert.deepEqual(observer.accept(before),{ok:false,status:null,error:'STALE_REVISION'});
  assert.deepEqual(observer.read(),valid);
  const conflict=structuredClone(after);conflict.view.player.x++;
  assert.equal(observer.accept(conflict).error,'REVISION_CONTENT_CONFLICT');
  assert.deepEqual(observer.read(),valid);
  assert.equal(observer.accept(after).status,'UNCHANGED');
});

test('identity and injected authority claims fail closed',async()=>{
  const {env}=fixture(),token=await session(env);
  const packet=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  const injected={...packet,owner:true};
  assert.equal(parseServerSnapshot(injected).error,'UNEXPECTED_SNAPSHOT_FIELDS');
  const changed=structuredClone(packet);changed.view.playerId='admin';
  assert.equal(parseServerSnapshot(changed).error,'INVALID_SNAPSHOT_PROJECTION');
  const duplicate=structuredClone(packet);duplicate.view.actors.push({...duplicate.view.actors[0]});
  assert.equal(parseServerSnapshot(duplicate).error,'DUPLICATE_OR_INVALID_ACTOR');
  const invalid=structuredClone(packet);invalid.view.player.x=999;
  assert.equal(parseServerSnapshot(invalid).error,'INVALID_SNAPSHOT_PROJECTION');
});

test('server alarm advances same observed entity IDs without client mutation',async()=>{
  const {env,room,store}=fixture(),token=await session(env),observer=new SnapshotObserver();
  const initial=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  observer.accept(initial);
  const ids=observer.read().actors.map(x=>x.id);
  const serverBefore=JSON.stringify(await store.get('endemar:experimental-room-v1'));
  const edited=observer.read();edited.actors[0].x=999;edited.player.y=999;
  assert.deepEqual(observer.read().actors.map(x=>x.id),ids);
  assert.equal(JSON.stringify(await store.get('endemar:experimental-room-v1')),serverBefore);
  await room.alarm();
  const later=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  assert.equal(observer.accept(later).status,'NEW_REVISION');
  assert.equal(observer.read().tick,initial.view.tick+1);
  assert.deepEqual(observer.read().actors.map(x=>x.id),ids);
  assert.equal(observer.read().immutableWorldAuthority,false);
});

test('time rewind and server world mismatch are rejected',async()=>{
  const {env,room}=fixture(),token=await session(env),observer=new SnapshotObserver();
  const initial=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  observer.accept(initial);await room.alarm();
  const next=await asJson(await edge.fetch(request('/api/endemar/snapshot','GET',undefined,token),env));
  observer.accept(next);
  const rewind=structuredClone(next);rewind.revision++;rewind.view.tick--;rewind.status.tick--;
  assert.equal(observer.accept(rewind).error,'TIME_REWIND');
  const alien=structuredClone(next);alien.worldId='other:world';
  assert.equal(observer.accept(alien).error,'UNTRUSTED_SNAPSHOT_ENVELOPE');
  assert.equal(observer.read().worldId,'end:pilot:one');
});
