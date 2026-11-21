import test from 'node:test';
import assert from 'node:assert/strict';
import {AUTHORITY_CONTRACT,parseIntentEnvelope,serverRequirements} from '../apps/rist-world/wwwroot/first-player/authority-contract.mjs';
const make=(verb='rest',arg)=>({version:AUTHORITY_CONTRACT,requestId:'req-001',verb,...(arg===undefined?{}:{arg})});
test('allowlisted intents retain stable request id',()=>{
  for(const verb of ['gather','drink','eat','plant','rest'])assert.equal(parseIntentEnvelope(make(verb)).ok,true);
  assert.equal(parseIntentEnvelope(make('move','north')).intent.arg,'north');
  assert.equal(parseIntentEnvelope(make('talk','end:a')).ok,true);
});
test('reject client claims of owner, GM, revision or player identity',()=>{
  for(const field of ['role','owner','gm','playerId','worldId','revision','tick','authority']){
    assert.deepEqual(parseIntentEnvelope({...make(),[field]:true}),{ok:false,error:'UNTRUSTED_FIELDS'});
  }
});
test('reject malformed and unexpected actions',()=>{
  for(const v of [null,[],42,{},make('teleport'),make('move','up'),make('talk','../secret'),
    make('rest','override'),{...make(),requestId:'bad id'}, {...make(),requestId:'x'.repeat(100)}])
    assert.equal(parseIntentEnvelope(v).ok,false);
});
test('do not mutate caller input and do not claim server authority',()=>{
  const source=make('move','west'),before=JSON.stringify(source);
  const parsed=parseIntentEnvelope(source);
  assert.equal(JSON.stringify(source),before);
  assert.notStrictEqual(parsed.intent,source);
  assert.equal(serverRequirements().classification,'PROPOSED_CONTRACT_NOT_DEPLOYED');
});
