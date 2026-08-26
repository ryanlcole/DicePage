(()=>{
 const NS='http://www.w3.org/2000/svg',TICKS=5;
 const number=v=>{const a=Math.abs(v);let d=a>=100?0:a>=10?1:a>=1?2:a>=.1?3:a>=.01?4:5;const n=Math.abs(v)<Math.pow(10,-d)/2?0:v;return n.toFixed(d).replace(/\.0+$|(?<=\.[0-9]*?)0+$/,'').replace(/\.$/,'')};
 const svg=(name,attrs={})=>{const e=document.createElementNS(NS,name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e};
 function parseScale(map){const s=map.querySelector('.status')?.textContent||'';const m=s.match(/([0-9]+(?:\.[0-9]+)?)\s*(mi|km|m|yd|ft)\/(?:sq|hex)/i);return m?{distance:Number(m[1])||1,unit:m[2]}:{distance:1,unit:''}}
 function ensureFrame(host,kind){let f=host.querySelector(':scope > .rist-coordinate-frame');if(f)return f;f=document.createElement('div');f.className=`rist-coordinate-frame ${kind}`;f.setAttribute('aria-hidden','true');for(const side of ['top','right','bottom','left']){const a=document.createElement('div');a.className=`rist-coordinate-axis ${side}`;for(let i=0;i<TICKS;i++){const t=document.createElement('span');t.className='rist-coordinate-tick';t.style.setProperty('--p',`${i/(TICKS-1)*100}%`);a.appendChild(t)}f.appendChild(a)}host.appendChild(f);return f}
 function syncHex(stage){const grid=stage.querySelector(':scope > .grid');if(!grid)return;let layer=stage.querySelector(':scope > .rist-hex-grid');if(!grid.classList.contains('hex')){layer?.remove();return}if(layer)return;const W=1200,H=780,r=32,hh=Math.sqrt(3)*r;layer=svg('svg',{class:'rist-hex-grid',viewBox:`0 0 ${W} ${H}`,preserveAspectRatio:'none','aria-hidden':'true'});const make=(cls,cx,cy)=>{const pts=[];for(let i=0;i<6;i++){const a=Math.PI/3*i;pts.push(`${(cx+r*Math.cos(a)).toFixed(2)},${(cy+r*Math.sin(a)).toFixed(2)}`)}const p=svg('polygon',{points:pts.join(' '),class:cls});layer.appendChild(p)};for(let col=-1,cx=0;cx<=W+r;col++,cx=col*1.5*r){for(let row=-1,cy=0;cy<=H+hh;row++,cy=row*hh+(col&1?hh/2:0)){make('hex-shadow',cx,cy);make('hex-line',cx,cy)}}grid.insertAdjacentElement('afterend',layer)}
 function setTick(t,value,unit,inside,zeroTolerance){
  if(!inside){t.textContent='';t.classList.remove('zero');t.classList.add('outside-world');return}
  t.classList.remove('outside-world');
  t.textContent=`${number(value)}${unit?` ${unit}`:''}`;
  t.classList.toggle('zero',Math.abs(value)<zeroTolerance);
 }
 function decorateMap(map){
  map.querySelectorAll('.rist-grid-overlay').forEach(x=>x.remove());
  const stage=map.querySelector('.world-stage');if(!stage)return;
  syncHex(stage);
  const frame=ensureFrame(map,'map-coordinates');
  const mr=map.getBoundingClientRect(),sr=stage.getBoundingClientRect();
  if(mr.width<2||mr.height<2||sr.width<2||sr.height<2)return;
  const scale=parseScale(map),cols=20,rows=13;
  const halfX=cols*scale.distance/2,halfY=rows*scale.distance/2;
  const xAt=x=>Math.max(-halfX,Math.min(halfX,(((x-sr.left)/sr.width)-.5)*cols*scale.distance));
  const yAt=y=>Math.max(-halfY,Math.min(halfY,(.5-((y-sr.top)/sr.height))*rows*scale.distance));
  const insideX=x=>x>=sr.left-.5&&x<=sr.right+.5;
  const insideY=y=>y>=sr.top-.5&&y<=sr.bottom+.5;
  const xs=[...frame.querySelectorAll('.top .rist-coordinate-tick, .bottom .rist-coordinate-tick')],ys=[...frame.querySelectorAll('.left .rist-coordinate-tick, .right .rist-coordinate-tick')];
  xs.forEach((t,i)=>{const x=mr.left+mr.width*(i%TICKS)/(TICKS-1);setTick(t,xAt(x),scale.unit,insideX(x),scale.distance/1000)});
  ys.forEach((t,i)=>{const y=mr.top+mr.height*(i%TICKS)/(TICKS-1);setTick(t,yAt(y),scale.unit,insideY(y),scale.distance/1000)});
 }
 function decorateCanvas(main){const canvas=main.querySelector(':scope > canvas');if(!canvas)return;const frame=ensureFrame(main,'canvas-coordinates'),r=canvas.getBoundingClientRect();if(r.width<2||r.height<2)return;const z=main.closest('.rist-art-studio')?.querySelector('.rist-art-zoom-value')?.textContent||'1×',zoom=Math.max(1,Number.parseFloat(z)||1);const xAt=x=>((x-r.left)-r.width/2)/zoom,yAt=y=>(r.height/2-(y-r.top))/zoom;const xs=[...frame.querySelectorAll('.top .rist-coordinate-tick, .bottom .rist-coordinate-tick')],ys=[...frame.querySelectorAll('.left .rist-coordinate-tick, .right .rist-coordinate-tick')];xs.forEach((t,i)=>{const v=xAt(r.left+r.width*(i%TICKS)/(TICKS-1));t.textContent=number(v);t.classList.toggle('zero',Math.abs(v)<.0001)});ys.forEach((t,i)=>{const v=yAt(r.top+r.height*(i%TICKS)/(TICKS-1));t.textContent=number(v);t.classList.toggle('zero',Math.abs(v)<.0001)})}
 function update(){document.querySelectorAll('.map').forEach(decorateMap);document.querySelectorAll('.rist-art-studio main').forEach(decorateCanvas)}
 let raf=0;const queue=()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;update()})};
 new MutationObserver(queue).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class','style','data-pan-x','data-pan-y','data-zoom']});
 addEventListener('resize',queue,{passive:true});addEventListener('pointermove',queue,{passive:true});addEventListener('wheel',queue,{passive:true});document.addEventListener('DOMContentLoaded',queue);queue();
})();