(()=>{
 'use strict';
 let raf=0;
 const number=(value,fallback)=>{const n=Number(value);return Number.isFinite(n)?n:fallback};
 function mapElement(){return document.querySelector('.map-shell .map')||document.querySelector('.map')}
 function controls(){return document.getElementById('viewer-frame-controls')}
 function sync(){
  const map=mapElement();
  const panel=controls();
  if(!panel){return;}
  if(!map){panel.hidden=true;return;}
  panel.hidden=false;
  const cols=Math.max(1,number(panel.dataset.cols,30));
  const rows=Math.max(1,number(panel.dataset.rows,30));
  const aspect=cols/rows;
  map.style.setProperty('--rist-grid-columns',String(cols));
  map.style.setProperty('--rist-grid-rows',String(rows));
  map.style.setProperty('--rist-grid-aspect',String(aspect));
  map.dataset.viewerGrid=`${cols}x${rows}`;
  map.dataset.viewerZ=panel.dataset.zLabel||'1 km';
  const rect=map.getBoundingClientRect();
  panel.style.setProperty('--viewer-map-left',`${rect.left}px`);
  panel.style.setProperty('--viewer-map-top',`${rect.top}px`);
  panel.style.setProperty('--viewer-map-width',`${rect.width}px`);
  panel.style.setProperty('--viewer-map-height',`${rect.height}px`);
  panel.style.setProperty('--viewer-map-right',`${window.innerWidth-rect.right}px`);
  panel.style.setProperty('--viewer-map-bottom',`${window.innerHeight-rect.bottom}px`);
 }
 function schedule(){cancelAnimationFrame(raf);raf=requestAnimationFrame(sync)}
 function start(){
  schedule();
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('orientationchange',schedule,{passive:true});
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class','style','data-cols','data-rows','data-z-label']});
  document.addEventListener('input',event=>{if(event.target instanceof HTMLInputElement&&event.target.closest('#viewer-frame-controls'))schedule()},{passive:true});
 }
 window.ristViewerFrame={sync:schedule};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
