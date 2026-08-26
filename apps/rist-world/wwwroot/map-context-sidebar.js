(()=>{
 const fmt=n=>{const a=Math.abs(n);const d=a>=100?0:a>=10?1:a>=1?2:a>=.1?3:4;return (Math.abs(n)<1e-9?0:n).toFixed(d).replace(/\.0+$|(?<=\.[0-9]*?)0+$/,'').replace(/\.$/,'')};
 const parseScale=map=>{const s=map.querySelector('.status')?.textContent||'';const m=s.match(/([0-9]+(?:\.[0-9]+)?)\s*(mi|km|m|yd|ft)\/(?:sq|hex)/i);return m?{distance:Number(m[1])||1,unit:m[2]}:{distance:1,unit:''}};
 function visibleCenter(map){
  const stage=map.querySelector('.world-stage');if(!stage)return {x:0,y:0,unit:''};
  const mr=map.getBoundingClientRect(),sr=stage.getBoundingClientRect();if(mr.width<2||sr.width<2)return {x:0,y:0,unit:''};
  const scale=parseScale(map),cols=20,rows=13,halfX=cols*scale.distance/2,halfY=rows*scale.distance/2;
  const cx=mr.left+mr.width/2,cy=mr.top+mr.height/2;
  const x=Math.max(-halfX,Math.min(halfX,(((cx-sr.left)/sr.width)-.5)*cols*scale.distance));
  const y=Math.max(-halfY,Math.min(halfY,(.5-((cy-sr.top)/sr.height))*rows*scale.distance));
  return {x,y,unit:scale.unit};
 }
 function item(label,value,key){const d=document.createElement('div');d.className='map-context-item';d.dataset.context=key;const s=document.createElement('strong');s.textContent=label;const v=key==='utc'?document.createElement('time'):document.createElement('span');v.textContent=value;d.append(s,v);return d}
 function ensure(){
  document.querySelectorAll('.map-shell').forEach(shell=>{
   const map=shell.querySelector(':scope > .map');if(!map)return;
   shell.classList.add('map-context-ready');
   let coord=map.querySelector(':scope > .map-current-coordinates');
   if(!coord){coord=document.createElement('div');coord.className='map-current-coordinates';coord.setAttribute('aria-label','Current map coordinates');map.appendChild(coord)}
   if(!shell.querySelector(':scope > .map-context-sidebar')){
    const rail=document.createElement('aside');rail.className='map-context-sidebar';rail.setAttribute('aria-label','World context');
    rail.append(item('Weather','Unset','weather'),item('Astronomy','Unset','astronomy'),item('Calendar','Unset','calendar'),item('Game Clock','Unset','game'),item('UTC Clock','--:--:--','utc'));
    shell.appendChild(rail);
   }
   const c=visibleCenter(map);coord.textContent=`${fmt(c.x)}, ${fmt(c.y)}${c.unit?` ${c.unit}`:''}`;
  });
 }
 function tick(){
  ensure();
  const now=new Date();const text=`${String(now.getUTCHours()).padStart(2,'0')}:${String(now.getUTCMinutes()).padStart(2,'0')}:${String(now.getUTCSeconds()).padStart(2,'0')}`;
  document.querySelectorAll('.map-context-item[data-context="utc"] time').forEach(x=>{x.textContent=text;x.dateTime=now.toISOString()});
 }
 let raf=0;const queue=()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;ensure()})};
 new MutationObserver(queue).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class','style','data-pan-x','data-pan-y','data-zoom']});
 addEventListener('resize',queue,{passive:true});addEventListener('pointermove',queue,{passive:true});addEventListener('wheel',queue,{passive:true});
 setInterval(tick,1000);document.addEventListener('DOMContentLoaded',tick);tick();
})();