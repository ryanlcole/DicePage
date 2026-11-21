import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ECOLOGY_STATE_URL,
  readEcologyCheckpoint,
  summarizeEcology,
} from '../apps/rist-world/wwwroot/first-player/relic-online-observer.mjs';

const sample=()=>({
  schema:'relic-ecology/1',policy:'observation_only',tick:48,agents:[
    {id:'A',status:'alive',seen:48,parents:[]},
    {id:'B',status:'alive',seen:48,parents:[]},
    {id:'C',status:'alive',seen:26,parents:['A','B']},
  ],history:[{seq:0,tick:0,hash:'a'.repeat(64)}],
});
const response=(body,ok=true)=>({ok,headers:{get:()=>null},text:async()=>body});

test('public checkpoint is summarized without becoming Shaelvien world state',()=>{
  const raw=sample(),before=JSON.stringify(raw);
  const summary=summarizeEcology(raw);
  assert.equal(JSON.stringify(raw),before);
  assert.equal(summary.tick,48);assert.equal(summary.alive,3);
  assert.equal(summary.reportedEvents,1);assert.equal(summary.canonical,false);
  assert.equal(summary.distinctFromShaelvien,true);
  assert.equal(summary.hashChainVerified,false);
  assert.deepEqual(summary.agents.find(a=>a.id==='C').parents,['A','B']);
  assert.equal(summary.agents[0].observations,48);
  assert.equal('world' in summary,false);
});

test('public reader fetches only the pinned public GitHub URL without credentials',async()=>{
  let calls=0;
  const info=await readEcologyCheckpoint(async (url,opts)=>{
    calls++;
    assert.equal(url,ECOLOGY_STATE_URL);
    assert.equal(opts.credentials,'omit');
    assert.equal(opts.method,'GET');
    assert.equal(opts.cache,'no-store');
    return response(JSON.stringify(sample()));
  });
  assert.equal(calls,1);assert.equal(info.tick,48);
});

test('network failure does not manufacture observed state',async()=>{
  await assert.rejects(()=>readEcologyCheckpoint(async()=>response('error',false)),/PUBLIC_CHECKPOINT_UNAVAILABLE/);
});

test('unexpected schema and write-capable policy fail closed',()=>{
  assert.throws(()=>summarizeEcology({...sample(),schema:'unexpected'}),/UNSUPPORTED_PUBLIC_CHECKPOINT/);
  assert.throws(()=>summarizeEcology({...sample(),policy:'write_enabled'}),/UNSUPPORTED_PUBLIC_CHECKPOINT/);
  assert.throws(()=>summarizeEcology({...sample(),tick:-1}),/UNSUPPORTED_PUBLIC_CHECKPOINT/);
});

test('duplicate, missing, and malicious-looking identities are rejected',()=>{
  assert.throws(()=>summarizeEcology({...sample(),agents:[
    {...sample().agents[0]},{...sample().agents[0]},
  ]}),/INVALID_PUBLIC_AGENT/);
  assert.throws(()=>summarizeEcology({...sample(),agents:[{id:'<script>',status:'alive',seen:1}]}),/INVALID_PUBLIC_AGENT/);
  assert.throws(()=>summarizeEcology({...sample(),agents:[{id:'A',status:'owner',seen:1}]}),/INVALID_PUBLIC_AGENT/);
});

test('hash-shaped data never claims proof of valid event chain',()=>{
  const s=summarizeEcology(sample());assert.equal(s.hashChainVerified,false);
  assert.throws(()=>summarizeEcology({...sample(),history:[{seq:5,tick:50,hash:'a'.repeat(64)}]}),/INVALID_PUBLIC_EVENT/);
});

test('invalid JSON and oversized checkpoint are rejected',async()=>{
  await assert.rejects(()=>readEcologyCheckpoint(async()=>response('{not-json')),/PUBLIC_CHECKPOINT_NOT_JSON/);
  await assert.rejects(()=>readEcologyCheckpoint(async()=>response('x'.repeat(3_000_001))),/PUBLIC_CHECKPOINT_TOO_LARGE/);
  await assert.rejects(()=>readEcologyCheckpoint(async()=>({
    ok:true,headers:{get:k=>k==='content-length'?'5000000':null},text:async()=>{throw Error('must not read');}
  })),/PUBLIC_CHECKPOINT_TOO_LARGE/);
});
