// DOM integration tests, not a substitute for authenticated browser testing.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {JSDOM}=require('jsdom');
const root=path.join(__dirname,'../wwwroot/prototype');

function fixture(access='edit'){
  const dom=new JSDOM(fs.readFileSync(path.join(root,'index.html'),'utf8'),{url:`https://viewer.test/Game/prototype/index.html?seed=empty&worldId=isolated-input-test&access=${access}`,runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window,d=w.document,stage=d.getElementById('stage'),world=d.getElementById('world');
  let size={width:1920,height:1080},observer;
  stage.getBoundingClientRect=()=>({...size,left:0,top:0,right:size.width,bottom:size.height});
  w.HTMLElement.prototype.getClientRects=function(){return this.closest('[hidden]')?[]:[{}]};
  w.matchMedia=()=>({matches:false});
  w.ResizeObserver=class{constructor(fn){observer=fn}observe(){}disconnect(){}};
  const captured=new Set();
  stage.setPointerCapture=id=>captured.add(id);stage.hasPointerCapture=id=>captured.has(id);stage.releasePointerCapture=id=>captured.delete(id);
  for(const name of ['viewer-input.js','prototype.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),dom.getInternalVMContext(),{filename:name});
  const event=(target,type,fields={})=>{const e=new w.Event(type,{bubbles:true,cancelable:true});for(const [key,value]of Object.entries(fields))Object.defineProperty(e,key,{value});target.dispatchEvent(e);return e};
  const pointer=(type,fields={})=>event(stage,type,{pointerId:1,pointerType:'mouse',button:0,clientX:200,clientY:200,...fields});
  const key=(target,key,extra={})=>{const e=new w.KeyboardEvent('keydown',{key,bubbles:true,cancelable:true,...extra});target.dispatchEvent(e);return e};
  const camera=()=>{const m=world.style.transform.match(/translate3d\(([-.\d]+)px,\s*([-.\d]+)px,0\) scale\(([-.\d]+)\)/);assert.ok(m,world.style.transform);return{x:+m[1],y:+m[2],scale:+m[3]}};
  return{w,d,stage,world,captured,event,pointer,key,camera,resize(next){size=next;observer()},close:()=>w.close()};
}
test('canonical runtime mouse capture releases on outside-up, lost capture and window blur',()=>{
  const f=fixture();try{
    f.pointer('pointerdown');assert.equal(f.d.activeElement,f.stage);assert.equal(f.captured.size,1);
    const before=f.camera();f.pointer('pointermove',{clientX:400,clientY:300});assert.equal(f.camera().x,before.x+200);
    f.pointer('pointerup',{clientX:2200});assert.equal(f.captured.size,0);assert.equal(f.stage.classList.contains('dragging'),false);
    let current=f.camera();f.pointer('pointermove',{clientX:10});assert.deepEqual(f.camera(),current);
    f.pointer('pointerdown');f.pointer('lostpointercapture');assert.equal(f.stage.classList.contains('dragging'),false);
    f.pointer('pointerdown');f.w.dispatchEvent(new f.w.Event('blur'));assert.equal(f.captured.size,0);
  }finally{f.close()}
});
test('toolbar and right-click do not pan; wheel zoom anchors to the pointer',()=>{
  const f=fixture();try{
    const button=f.d.getElementById('zoomIn');button.focus();
    f.event(button,'pointerdown',{pointerId:1,pointerType:'mouse',button:0});assert.equal(f.captured.size,0);assert.equal(f.d.activeElement,button);
    f.pointer('pointerdown',{button:2});assert.equal(f.captured.size,0);
    const before=f.camera(),px=600,py=300;
    assert.equal(f.event(f.stage,'wheel',{clientX:px,clientY:py,deltaY:-120}).defaultPrevented,true);
    const after=f.camera();assert.ok(after.scale>before.scale);
    assert.ok(Math.abs((px-before.x)/before.scale-(px-after.x)/after.scale)<1e-6);
    assert.ok(Math.abs((py-before.y)/before.scale-(py-after.y)/after.scale)<1e-6);
    assert.equal(f.event(button,'wheel',{deltaY:120}).defaultPrevented,false);
    assert.deepEqual(f.camera(),after);
  }finally{f.close()}
});
test('physical keys and controls share camera behavior; text fields cannot move it',()=>{
  const f=fixture();try{
    f.stage.focus();const before=f.camera();f.key(f.stage,'ArrowRight');assert.equal(f.camera().x,before.x-32);
    const start=f.camera().scale;f.key(f.stage,'+');assert.ok(Math.abs(f.camera().scale/start-1.22)<1e-9);
    f.d.getElementById('zoomOut').click();assert.ok(Math.abs(f.camera().scale-start)<1e-9);
    f.stage.focus();f.key(f.stage,'u');const panel=f.d.getElementById('imageUploadPanel');assert.equal(panel.hidden,false);
    const input=f.d.getElementById('imageX');input.focus();const camera=f.camera();f.key(input,'ArrowRight');f.key(input,'+');assert.deepEqual(f.camera(),camera);
    f.key(input,'Escape');assert.equal(panel.hidden,true);assert.equal(f.d.activeElement.id,'imageUploadToggle');
    f.stage.focus();f.key(f.stage,'f');assert.equal(f.camera().scale,before.scale);
  }finally{f.close()}
});
test('view-only mode keeps navigation but blocks the upload shortcut and save',()=>{
  const f=fixture('view');try{
    assert.equal(f.d.getElementById('persistentSave').disabled,true);f.stage.focus();f.key(f.stage,'u');assert.equal(f.d.getElementById('imageUploadPanel').hidden,true);
    const before=f.camera();f.key(f.stage,'ArrowDown');assert.notEqual(f.camera().y,before.y);
    f.key(f.stage,'t');assert.equal(f.d.getElementById('tierMenu').hidden,false);
    f.key(f.d.activeElement,'Escape');assert.equal(f.d.getElementById('tierMenu').hidden,true);
  }finally{f.close()}
});
test('touch pan and pinch still use the same camera and release cleanly',()=>{
  const f=fixture();try{
    f.pointer('pointerdown',{pointerType:'touch'});const before=f.camera();f.pointer('pointermove',{pointerType:'touch',clientX:220});assert.equal(f.camera().x,before.x+20);
    f.pointer('pointerdown',{pointerType:'touch',pointerId:2,clientX:320});const scale=f.camera().scale;
    f.pointer('pointermove',{pointerType:'touch',pointerId:2,clientX:420});assert.ok(f.camera().scale>scale);
    f.pointer('pointercancel',{pointerType:'touch',pointerId:2});f.pointer('pointerup',{pointerType:'touch'});assert.equal(f.stage.classList.contains('dragging'),false);
  }finally{f.close()}
});
test('actual resize integration retains camera center and scale without fitting again',()=>{
  const f=fixture();try{
    f.stage.focus();f.key(f.stage,'+');f.key(f.stage,'ArrowRight');const before=f.camera();
    f.resize({width:1366,height:768});const after=f.camera();assert.equal(after.scale,before.scale);assert.equal(after.x,before.x+(1366-1920)/2);
    f.resize({width:0,height:0});assert.deepEqual(f.camera(),after);
    f.resize({width:900,height:700});assert.equal(f.camera().scale,before.scale);
  }finally{f.close()}
});
test('tool-tab rerenders retain focus; closing keyboard restores focus to toggle',()=>{
  const f=fixture();try{
    f.d.getElementById('keyboardToggle').click();const tab=Array.from(f.d.querySelectorAll('#keyboardTabs button')).find(b=>b.textContent==='Image');tab.focus();tab.click();
    assert.equal(f.d.activeElement.textContent,'Image');assert.ok(f.d.activeElement.isConnected);
    f.key(f.d.activeElement,'Escape');assert.equal(f.d.getElementById('viewerKeyboard').hidden,true);assert.equal(f.d.activeElement.id,'keyboardToggle');
  }finally{f.close()}
});
