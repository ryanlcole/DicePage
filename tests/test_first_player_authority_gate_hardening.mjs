import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld} from '../apps/rist-world/wwwroot/first-player/core.mjs';
import {applyAuthorizedIntent} from '../apps/rist-world/wwwroot/first-player/authority-gate.mjs';

const authority = world => ({
  principalId:'synthetic:authenticated',playerId:world.player.id,
  canAct:true,nextSequence:1
});
const request = () => ({sequence:1,verb:'move',arg:'east'});

test('invalid persisted world fails closed rather than throwing',()=>{
  const trusted=createWorld();
  for(const malformed of [
    null,{}, {...trusted,actors:[null]}, {...trusted,actors:[{id:'x'}]},
    {...trusted,player:null}
  ]){
    assert.doesNotThrow(()=>{
      const result=applyAuthorizedIntent(malformed,request(),authority(trusted));
      assert.equal(result.accepted,false);
      assert.equal(result.reason,'INVALID_WORLD');
    });
  }
});

test('wire accessors and non-JSON request objects cannot execute',()=>{
  const world=createWorld(),before=structuredClone(world);
  const accessor={sequence:1,verb:'move'};
  Object.defineProperty(accessor,'arg',{enumerable:true,get(){throw Error('wire getter executed')}});
  const inherited=Object.create({sequence:1});
  inherited.verb='move';inherited.arg='east';
  for(const payload of [accessor,inherited,[],new Date(),Object.assign(new String(''),request())]){
    assert.doesNotThrow(()=>{
      const result=applyAuthorizedIntent(world,payload,authority(world));
      assert.equal(result.accepted,false);
    });
    assert.deepEqual(world,before);
  }
});

test('maximum safe sequence cannot overflow to an unsafe next sequence',()=>{
  const world=createWorld(),before=structuredClone(world);
  const auth={...authority(world),nextSequence:Number.MAX_SAFE_INTEGER};
  const result=applyAuthorizedIntent(world,{...request(),sequence:Number.MAX_SAFE_INTEGER},auth);
  assert.equal(result.accepted,false);
  assert.equal(result.reason,'AUTHORITY_DENIED');
  assert.deepEqual(world,before);
});

test('valid ordinary JSON request remains supported without mutating input',()=>{
  const world=createWorld(),before=structuredClone(world);
  const wire=JSON.parse(JSON.stringify(request()));
  const result=applyAuthorizedIntent(world,wire,authority(world));
  assert.equal(result.accepted,true);
  assert.equal(result.nextSequence,2);
  assert.equal(result.world.player.x,before.player.x+1);
  assert.deepEqual(world,before);
  assert.deepEqual(wire,request());
});
