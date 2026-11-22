import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld} from '../apps/rist-world/wwwroot/first-player/core.mjs';
import {applyAuthorizedIntent} from '../apps/rist-world/wwwroot/first-player/authority-gate.mjs';

const trusted = world => ({
  principalId:'test:authenticated-user',playerId:world.player.id,
  nextSequence:1,canAct:true
});
test('untrusted payload cannot self-grant identity or capabilities',()=>{
  const world=createWorld(),before=structuredClone(world);
  for(const request of [
    {sequence:1,verb:'move',arg:'east',canAct:true},
    {sequence:1,verb:'move',arg:'east',principalId:'owner'},
    {sequence:1,verb:'teleport',arg:'east'},
    {sequence:1,verb:'move',arg:'east'}
  ]){
    const result=applyAuthorizedIntent(world,request,null);
    assert.equal(result.accepted,false);
    assert.deepEqual(world,before);
  }
});
test('deny mismatched identity, missing capability and replay',()=>{
  const world=createWorld(),authority=trusted(world);
  for(const changed of [{playerId:'other'}, {canAct:false}, {principalId:''}]){
    const result=applyAuthorizedIntent(world,{sequence:1,verb:'move',arg:'east'},{...authority,...changed});
    assert.equal(result.accepted,false);
  }
  for(const sequence of [0,2,-1,1.5,NaN,Infinity]){
    const result=applyAuthorizedIntent(world,{sequence,verb:'move',arg:'east'},authority);
    assert.equal(result.accepted,false);
  }
});
test('accepted move commits only new snapshot and increments sequence',()=>{
  const world=createWorld(),original=JSON.stringify(world);
  const first=applyAuthorizedIntent(world,{sequence:1,verb:'move',arg:'east'},trusted(world));
  assert.equal(first.accepted,true);
  assert.equal(first.world.player.x,world.player.x+1);
  assert.equal(first.nextSequence,2);
  assert.equal(JSON.stringify(world),original);
  const replay=applyAuthorizedIntent(first.world,{sequence:1,verb:'move',arg:'east'},
    {...trusted(first.world),nextSequence:2});
  assert.equal(replay.accepted,false);
  assert.strictEqual(replay.world,first.world);
  const second=applyAuthorizedIntent(first.world,{sequence:2,verb:'move',arg:'west'},
    {...trusted(first.world),nextSequence:2});
  assert.equal(second.accepted,true);
  assert.equal(second.world.player.x,world.player.x);
});
test('invalid actions cannot mutate, consume sequence or leak world',()=>{
  const world=createWorld(),authority=trusted(world),before=JSON.stringify(world);
  for(const request of [
    {sequence:1,verb:'move',arg:'up'},
    {sequence:1,verb:'plant',arg:'unexpected'},
    {sequence:1,verb:'talk',arg:'x'.repeat(100)},
    {sequence:1,verb:'admin'},
    {sequence:1,verb:'move',arg:'east',owner:true},
    {sequence:1,verb:'talk',arg:'not-present'},
  ]){
    const result=applyAuthorizedIntent(world,request,authority);
    assert.equal(result.accepted,false,JSON.stringify(request));
    assert.equal(result.nextSequence,1);
    assert.strictEqual(result.world,world);
    assert.equal(JSON.stringify(world),before);
  }
});
