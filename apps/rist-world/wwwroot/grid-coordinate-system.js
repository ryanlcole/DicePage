(()=>{
 'use strict';
 const TICKS=5;
 const number=v=>{
  const a=Math.abs(v);
  const d=a>=100?0:a>=10?1:a>=1?2:a>=.1?3:a>=.01?4:5;
  const n=a<Math.pow(10,-d)/2?0:v;
  return n.toFixed(d).replace(/\.0+$|(?<=\.[0-9]*?)0+$/,'').replace(/\.$/,'');
 };
 function parseScale(map){
  const text=map.querySelector('.status')?.textContent||'';
  const match=text.match(/([0-9]+(?:\.[0-9]+)?)\s*(mi|km|m|yd|ft)\/(?:sq|hex)/i);
  return match?{distance:Number(match[1])||1,unit:match[2]}:{distance:1,unit:''};
 }
 function ensureFrame(host,kind){
  let frame=host.querySelector(':scope > .rist-coordinate-frame');
  if(frame)return frame;
  frame=document.createElement('div');
  frame.className=`rist-coordinate-frame ${kind}`;
  frame.setAttribute('aria-hidden','true');
  for(const side of ['top','right','bottom','left']){
   const axis=document.createElement('div');
   axis.className=`rist-coordinate-axis ${side}`;
   if(side!=='top'){
    const label=document.createElement('b');
    label.className='rist-coordinate-axis-label';
    label.textContent=side==='left'?'Y':side==='bottom'?'X':'Z';
    axis.appendChild(label);
   }
   for(let i=0;i<TICKS;i++){
    const tick=document.createElement('span');
    tick.className='rist-coordinate-tick';
    tick.style.setProperty('--p',`${i/(TICKS-1)*100}%`);
    axis.appendChild(tick);
   }
   frame.appendChild(axis);
  }
  host.appendChild(frame);
  return frame;
 }
 function setTick(tick,value,unit,inside,zeroTolerance){
  if(!inside){tick.textContent='';tick.classList.remove('zero');tick.classList.add('outside-world');return;}
  tick.classList.remove('outside-world');
  tick.textContent=`${number(value)}${unit?` ${unit}`:''}`;
  tick.classList.toggle('zero',Math.abs(value)<zeroTolerance);
 }
 function decorateMap(map){
  const stage=map.querySelector('.world-bounds')||map.querySelector('.world-stage');
  const shell=map.closest('.map-shell');
  if(!stage||!shell)return;
  /* Coordinates belong to the permanent shell frame, never inside the map. */
  const stale=map.querySelector(':scope > .rist-coordinate-frame');
  if(stale)stale.remove();
  const frame=ensureFrame(shell,'map-coordinates');
  const mapRect=map.getBoundingClientRect();
  const stageRect=stage.getBoundingClientRect();
  if(mapRect.width<2||mapRect.height<2||stageRect.width<2||stageRect.height<2)return;
  const scale=parseScale(map),cols=30,rows=30;
  const halfX=cols*scale.distance/2,halfY=rows*scale.distance/2;
  const xAt=x=>Math.max(-halfX,Math.min(halfX,(((x-stageRect.left)/stageRect.width)-.5)*cols*scale.distance));
  const yAt=y=>Math.max(-halfY,Math.min(halfY,(.5-((y-stageRect.top)/stageRect.height))*rows*scale.distance));
  const insideX=x=>x>=stageRect.left-.5&&x<=stageRect.right+.5;
  const insideY=y=>y>=stageRect.top-.5&&y<=stageRect.bottom+.5;
  const bottom=frame.querySelectorAll('.bottom .rist-coordinate-tick');
  const left=frame.querySelectorAll('.left .rist-coordinate-tick');
  const right=frame.querySelectorAll('.right .rist-coordinate-tick');
  bottom.forEach((tick,i)=>{const x=mapRect.left+mapRect.width*i/(TICKS-1);setTick(tick,xAt(x),scale.unit,insideX(x),scale.distance/1000);});
  left.forEach((tick,i)=>{const y=mapRect.top+mapRect.height*i/(TICKS-1);setTick(tick,yAt(y),scale.unit,insideY(y),scale.distance/1000);});
  const z=Number((map.querySelector('.status')?.textContent||'').match(/(?:^|\s)z=(-?\d+)/i)?.[1]||0);
  const center=Math.floor(TICKS/2);
  right.forEach((tick,i)=>{tick.textContent=i===center?number(z):'';tick.classList.toggle('zero',z===0&&i===center);});
  frame.querySelectorAll('.top .rist-coordinate-tick').forEach(tick=>tick.textContent='');
 }
 function decorateCanvas(main){
  const canvas=main.querySelector(':scope > canvas');if(!canvas)return;
  const frame=ensureFrame(main,'canvas-coordinates');const rect=canvas.getBoundingClientRect();if(rect.width<2||rect.height<2)return;
  const label=main.closest('.rist-art-studio')?.querySelector('.rist-art-zoom-value')?.textContent||'1×';const zoom=Math.max(1,Number.parseFloat(label)||1);
  const xAt=x=>((x-rect.left)-rect.width/2)/zoom;const yAt=y=>(rect.height/2-(y-rect.top))/zoom;
  frame.querySelectorAll('.bottom .rist-coordinate-tick').forEach((tick,i)=>{const value=xAt(rect.left+rect.width*i/(TICKS-1));tick.textContent=number(value);tick.classList.toggle('zero',Math.abs(value)<.0001);});
  frame.querySelectorAll('.left .rist-coordinate-tick').forEach((tick,i)=>{const value=yAt(rect.top+rect.height*i/(TICKS-1));tick.textContent=number(value);tick.classList.toggle('zero',Math.abs(value)<.0001);});
 }
 function update(){document.querySelectorAll('.map').forEach(decorateMap);document.querySelectorAll('.rist-art-studio main').forEach(decorateCanvas);}
 const queue=()=>window.RistRuntime?.frame?.('coordinates',update)??requestAnimationFrame(update);
 document.addEventListener('rist:dom-change',queue);document.addEventListener('rist:viewport-change',queue);queue();
})();
