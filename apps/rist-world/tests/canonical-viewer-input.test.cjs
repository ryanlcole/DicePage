const {test}=require('node:test');
const assert=require('node:assert/strict');
const {install,resizeCamera}=require('../wwwroot/prototype/viewer-input.js');

function fixture(){
  const handlers=new Map(),calls=[];
  const doc={activeElement:null,addEventListener:(type,fn)=>handlers.set(type,fn),removeEventListener:type=>handlers.delete(type)};
  const stage={};doc.activeElement=stage;
  let panel=null;
  const dispose=install({stage,document:doc,modal:()=>panel,
    ...Object.fromEntries(['pan','zoom','fit','tiers','settings','upload','keyboard'].map(name=>[name,(...args)=>calls.push([name,...args])]))});
  function key(key,extra={}){const event={key,target:doc.activeElement,preventDefault(){this.defaultPrevented=true},...extra};handlers.get('keydown')?.(event);return event}
  return{doc,stage,calls,key,dispose,setModal(value){panel=value}};
}
test('focused camera supports pan, accelerated pan, zoom and documented commands',()=>{
  const f=fixture();
  for(const key of ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','f','T','s','u','k'])assert.equal(f.key(key).defaultPrevented,true);
  f.key('ArrowLeft',{shiftKey:true});
  assert.deepEqual(f.calls,[['pan',32,0],['pan',-32,0],['pan',0,32],['pan',0,-32],['zoom',1.22],['zoom',1.22],['zoom',1/1.22],['fit'],['tiers'],['settings'],['upload'],['keyboard'],['pan',128,0]]);
});
test('typing, native control keys and shortcuts outside viewer focus never move map',()=>{
  const f=fixture();
  for(const tagName of ['INPUT','TEXTAREA','SELECT','BUTTON','DIV']){
    f.doc.activeElement={tagName,isContentEditable:tagName==='DIV'};
    for(const key of ['ArrowLeft','+','-','f','s',' ','Enter'])assert.equal(f.key(key).defaultPrevented,undefined);
  }
  f.doc.activeElement=f.stage;
  for(const extra of [{ctrlKey:true},{metaKey:true},{altKey:true},{isComposing:true},{defaultPrevented:true}])f.key('ArrowRight',extra);
  assert.deepEqual(f.calls,[]);
});
test('Tab and browser keys remain native when no dialog is open',()=>{
  const f=fixture();
  for(const key of ['Tab','Escape','F5','Enter',' '])assert.equal(f.key(key).defaultPrevented,undefined);
  assert.deepEqual(f.calls,[]);
});
test('modal Tab boundaries wrap within visible enabled controls',()=>{
  const f=fixture();
  const control=(overrides={})=>({tabIndex:0,getClientRects:()=>[{}],focus(){f.doc.activeElement=this},...overrides});
  const first=control(),last=control(),hidden=control({getClientRects:()=>[]}),disabled=control({disabled:true});
  f.setModal({querySelectorAll:()=>[first,hidden,disabled,last]});
  f.doc.activeElement=first;assert.equal(f.key('Tab',{shiftKey:true}).defaultPrevented,true);assert.equal(f.doc.activeElement,last);
  assert.equal(f.key('Tab').defaultPrevented,true);assert.equal(f.doc.activeElement,first);
  assert.equal(f.key('Tab').defaultPrevented,undefined);
  f.doc.activeElement=f.stage;f.key('ArrowLeft');assert.deepEqual(f.calls,[]);
  f.key('Tab');assert.equal(f.doc.activeElement,first);
  f.setModal(null);f.doc.activeElement=f.stage;f.key('ArrowLeft');assert.deepEqual(f.calls,[['pan',32,0]]);
});
test('removing input controller removes its listener',()=>{
  const f=fixture();f.dispose();f.key('f');assert.deepEqual(f.calls,[]);
});
test('viewport resize preserves zoom and world point at center across desktop and narrow dimensions',()=>{
  let previous={width:1920,height:1080},camera={x:-381,y:49,fitX:50,fitY:60,scale:2.3};
  const point={x:(previous.width/2-camera.x)/camera.scale,y:(previous.height/2-camera.y)/camera.scale};
  for(const next of [{width:1366,height:768},{width:900,height:700},{width:390,height:844},{width:1920,height:1080}]){
    camera=resizeCamera(camera,previous,next);
    assert.equal(camera.scale,2.3);
    assert.ok(Math.abs((next.width/2-camera.x)/camera.scale-point.x)<1e-9);
    assert.ok(Math.abs((next.height/2-camera.y)/camera.scale-point.y)<1e-9);
    previous=next;
  }
});
test('zero size and first layout defer camera fitting instead of creating zero scale',()=>{
  const camera={x:0,y:0,fitX:0,fitY:0,scale:1};
  assert.equal(resizeCamera(camera,null,{width:800,height:600}),null);
  assert.equal(resizeCamera(camera,{width:800,height:600},{width:0,height:0}),null);
  assert.equal(camera.scale,1);
});
