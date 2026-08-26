(()=>{
 const hosts=new WeakMap();
 const maps={
  'random-world':{name:'Random World',cols:800,rows:600,seed:()=>Math.floor(Math.random()*2147483646)+1,kind:'world'},
  'verdant-reach':{name:'Verdant Reach',cols:320,rows:240,seed:170041,kind:'region'},
  'ember-basin':{name:'Ember Basin',cols:320,rows:240,seed:824911,kind:'region'},
  'frost-march':{name:'Frost March',cols:320,rows:240,seed:510337,kind:'region'}
 };
 let current={id:'random-world',seed:maps['random-world'].seed()};
 const raf=()=>new Promise(r=>requestAnimationFrame(r));
 const hash=(x,y,s)=>{let n=(x*374761393+y*668265263+s*1442695041)|0;n=(n^(n>>>13))*1274126177;n^=n>>>16;return (n>>>0)/4294967295};
 const fade=t=>t*t*(3-2*t);
 function valueNoise(x,y,scale,seed){
  const gx=x/scale,gy=y/scale,x0=Math.floor(gx),y0=Math.floor(gy),tx=fade(gx-x0),ty=fade(gy-y0);
  const a=hash(x0,y0,seed),b=hash(x0+1,y0,seed),c=hash(x0,y0+1,seed),d=hash(x0+1,y0+1,seed);
  const u=a+(b-a)*tx,v=c+(d-c)*tx;return u+(v-u)*ty;
 }
 function terrain(x,y,w,h,seed,kind){
  const nx=x/w-.5,ny=y/h-.5,edge=Math.max(Math.abs(nx)*1.82,Math.abs(ny)*1.82);
  const broad=valueNoise(x,y,96,seed),mid=valueNoise(x,y,38,seed+17),fine=valueNoise(x,y,13,seed+43);
  const height=broad*.56+mid*.31+fine*.13-(kind==='world'?Math.max(0,edge-.58)*1.25:0);
  const wet=valueNoise(x,y,61,seed+101)*.7+valueNoise(x,y,21,seed+211)*.3;
  const heat=valueNoise(x,y,77,seed+307)*.65+(1-Math.abs(ny*1.5))*.35;
  return {height,wet,heat};
 }
 const lerp=(a,b,t)=>Math.round(a+(b-a)*t);
 const mix=(a,b,t)=>[lerp(a[0],b[0],t),lerp(a[1],b[1],t),lerp(a[2],b[2],t)];
 function colorOf(t,kind){
  const ocean=[17,77,92],deep=[8,46,68],sand=[151,123,70],grass=[67,104,55],forest=[38,76,49],dry=[133,104,53],rock=[92,88,72],snow=[190,205,202],ember=[122,67,39],frost=[94,139,151];
  if(t.height<.39)return mix(deep,ocean,Math.max(0,Math.min(1,(t.height-.18)/.21)));
  if(t.height<.43)return mix(ocean,sand,(t.height-.39)/.04);
  let base=t.wet>.63?forest:t.wet<.34?dry:grass;
  if(kind==='region'&&t.heat>.72)base=mix(base,ember,(t.heat-.72)/.28);
  if(kind==='region'&&t.heat<.29)base=mix(base,frost,(.29-t.heat)/.29);
  if(t.height>.72)base=mix(base,rock,(t.height-.72)/.18);
  if(t.height>.89)base=mix(base,snow,(t.height-.89)/.11);
  return base;
 }
 async function render(host,id,seedOverride){
  const def=maps[id]||maps['random-world'];
  const seed=seedOverride??(typeof def.seed==='function'?def.seed():def.seed);
  current={id,seed};
  const token={cancel:false};
  const old=hosts.get(host);if(old)old.cancel=true;hosts.set(host,token);
  host.className='base map-tile-map procedural-map loading';
  host.dataset.mapId=id;host.dataset.mapColumns=def.cols;host.dataset.mapRows=def.rows;host.dataset.mapSeed=seed;
  const canvas=document.createElement('canvas');
  canvas.className='procedural-map-canvas';canvas.width=def.cols;canvas.height=def.rows;canvas.setAttribute('aria-label',`${def.name}, ${def.cols} by ${def.rows} tiles`);
  host.replaceChildren(canvas);
  const ctx=canvas.getContext('2d',{alpha:false});
  const image=ctx.createImageData(def.cols,def.rows),data=image.data;
  let p=0;
  for(let y=0;y<def.rows;y++){
   if(token.cancel)return;
   for(let x=0;x<def.cols;x++){
    const c=colorOf(terrain(x,y,def.cols,def.rows,seed,def.kind),def.kind);data[p++]=c[0];data[p++]=c[1];data[p++]=c[2];data[p++]=255;
   }
   if(y%24===23){ctx.putImageData(image,0,0,0,0,def.cols,y+1);await raf();}
  }
  ctx.putImageData(image,0,0);
  host.classList.remove('loading');host.classList.add('ready');
  const status=document.querySelector('.map>.status');if(status)status.textContent=`${def.name} • ${def.kind.toUpperCase()} • ${def.cols}×${def.rows} tiles • drag • pinch`;
 }
 function scan(){
  document.querySelectorAll('.map-tile-map').forEach(host=>{if(!hosts.has(host))render(host,current.id,current.seed)});
  installCards();
 }
 function mapCard(id,label,type){
  const b=document.createElement('button');b.type='button';b.className='library-playing-card rist-map-card';b.dataset.mapId=id;b.setAttribute('aria-label',label);
  b.innerHTML=`<span class="library-card-face"><small>${type}</small><strong>${label}</strong></span>`;
  b.addEventListener('click',()=>{document.querySelectorAll('.map-tile-map').forEach(h=>render(h,id));});
  return b;
 }
 function installCards(){
  const lib=document.querySelector('#card-library');if(!lib)return;
  const select=lib.querySelector('.card-library-source-row select');if(!select||select.value!=='Universal')return;
  const results=lib.querySelector('.card-library-results');if(!results||results.querySelector('.rist-map-card'))return;
  results.append(mapCard('random-world','Random World Map','World map'));
  results.append(mapCard('verdant-reach','Verdant Reach','Region map'));
  results.append(mapCard('ember-basin','Ember Basin','Region map'));
  results.append(mapCard('frost-march','Frost March','Region map'));
 }
 const observer=new MutationObserver(scan);
 function start(){observer.observe(document.documentElement,{subtree:true,childList:true});scan()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.ristProceduralMap={load:(id)=>document.querySelectorAll('.map-tile-map').forEach(h=>render(h,id)),regenerate:()=>document.querySelectorAll('.map-tile-map').forEach(h=>render(h,'random-world'))};
})();
