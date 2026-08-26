(()=>{
 const order=['WORLD','REGION','LOCAL','SITE','ROOM','ENCOUNTER','OBJECT','CONTAINER','CONTENTS','WEATHER'];
 const rank=l=>Math.max(0,order.indexOf(normalize(l)));
 const normalize=v=>{
  const x=String(v||'WORLD').trim().toUpperCase();
  if(x==='ZONE'||x==='CONTINENT')return 'REGION';
  if(x==='AREA')return 'LOCAL';
  if(x==='TACTICAL'||x==='INSTANCE')return 'ENCOUNTER';
  if(x==='UNIVERSAL'||!order.includes(x))return 'WORLD';
  return x;
 };
 const pieceLayer=el=>el.classList.contains('rolling-stock')?'REGION':el.classList.contains('mini')?'ENCOUNTER':el.classList.contains('bit')?'OBJECT':'LOCAL';
 let catalog=[],scheduled=false;
 const stored=()=>{try{return JSON.parse(localStorage.getItem('rist.recursion.native.v1')||'{}')}catch{return {}}};
 const remembered=stored();
 const saveRemembered=()=>{try{localStorage.setItem('rist.recursion.native.v1',JSON.stringify(remembered))}catch{}};
 const current=()=>normalize(document.querySelector('.recursion-cockpit')?.dataset.recursionLayer||'WORLD');
 const fingerprint=el=>{
  const img=el.querySelector('img');
  const src=img?.getAttribute('src')||'';
  return [el.getAttribute('aria-label')||'',src,el.style.left||'',el.style.top||''].join('|');
 };
 const atlasLayer=el=>{
  const img=el.querySelector('img');
  const src=img?.getAttribute('src')||'';
  const name=el.getAttribute('aria-label')||'';
  const hit=catalog.find(x=>(x.image&&src&&String(x.image).split('?')[0]===src.split('?')[0])||(x.name&&name&&x.name===name));
  if(hit&&String(hit.layer||'').toUpperCase()!=='UNIVERSAL')return normalize(hit.layer);
  const key=fingerprint(el);
  if(remembered[key])return normalize(remembered[key]);
  const layer=current();remembered[key]=layer;saveRemembered();return layer;
 };
 const roofish=el=>/roof|ceiling|canopy|overhang/i.test(el.getAttribute('aria-label')||'');
 const overlaps=(a,b)=>{const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();const x=ar.left+ar.width/2,y=ar.top+ar.height/2;return x>=br.left&&x<=br.right&&y>=br.top&&y<=br.bottom};
 function classify(){
  scheduled=false;
  const view=current(),viewRank=rank(view);
  const tiles=[...document.querySelectorAll('.tile-cell')];
  const blockers=[];
  for(const el of tiles){const layer=atlasLayer(el);el.dataset.nativeLayer=layer;if(roofish(el)){el.dataset.weatherBlocker='true';blockers.push(el)}}
  for(const el of tiles){
   const layer=normalize(el.dataset.nativeLayer);let visible=layer==='WEATHER'?viewRank<=rank('ROOM'):rank(layer)<=viewRank;
   if(visible&&layer==='WEATHER'&&blockers.some(b=>b!==el&&overlaps(el,b)))visible=false;
   el.toggleAttribute('data-recursion-hidden',!visible);
  }
  for(const el of document.querySelectorAll('.piece')){
   const layer=pieceLayer(el);el.dataset.nativeLayer=layer;el.toggleAttribute('data-recursion-hidden',rank(layer)>viewRank);
  }
  for(const el of document.querySelectorAll('.tray-item')){
   let layer=el.classList.contains('tile')?atlasLayer(el):pieceLayer(el);el.dataset.nativeLayer=layer;el.title=`${el.title||'Place asset'} Native layer: ${layer}.`;
  }
  document.documentElement.dataset.ristViewportLayer=view;
 }
 const schedule=()=>{if(scheduled)return;scheduled=true;requestAnimationFrame(classify)};
 async function loadCatalog(){
  const urls=['data/atlas-public.json','assets/drive-tiles/catalog.json'];
  for(const url of urls){try{const r=await fetch(url,{cache:'no-store'});if(r.ok){const rows=await r.json();if(Array.isArray(rows))catalog.push(...rows)}}catch{}}
  schedule();
 }
 const observer=new MutationObserver(schedule);
 function start(){observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['data-recursion-layer','style']});loadCatalog();schedule()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 addEventListener('resize',schedule,{passive:true});addEventListener('orientationchange',schedule,{passive:true});
})();
