(()=>{
 const NS='http://www.w3.org/2000/svg', W=1000,H=650,COLS=20,ROWS=13;
 const letters=n=>{let s='';for(n++;n>0;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s};
 const svgEl=(name,attrs={})=>{const e=document.createElementNS(NS,name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e};
 function addPolygon(svg,pts,label,cx,cy){const p=pts.map(([x,y])=>`${x.toFixed(2)},${y.toFixed(2)}`).join(' ');svg.appendChild(svgEl('polygon',{points:p,class:'cell-keyline'}));svg.appendChild(svgEl('polygon',{points:p,class:'cell'}));const t=svgEl('text',{x:cx,y:cy,class:'coord'});t.textContent=label;svg.appendChild(t)}
 function square(svg){const cw=W/COLS,ch=H/ROWS;for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){const x=c*cw,y=r*ch,pts=[[x,y],[x+cw,y],[x+cw,y+ch],[x,y+ch]];addPolygon(svg,pts,`${letters(c)}${r+1}`,x+cw/2,y+ch/2)}}
 function hex(svg){const radius=W/(1.5*(COLS-1)+2),hh=Math.sqrt(3)*radius;for(let c=0;c<COLS;c++){for(let r=0;r<ROWS;r++){const cx=radius+c*1.5*radius,cy=hh/2+r*hh+(c%2?hh/2:0);if(cy-hh/2>H||cy+hh/2<0)continue;const pts=[];for(let i=0;i<6;i++){const a=Math.PI/3*i;pts.push([cx+Math.cos(a)*radius,cy+Math.sin(a)*radius])}addPolygon(svg,pts,`${letters(c)}${r+1}`,cx,cy)}}}
 function decorate(stage){const grid=stage.querySelector(':scope > .grid');if(!grid)return;const mode=grid.classList.contains('hex')?'hex':grid.classList.contains('square')?'square':'none';let svg=stage.querySelector(':scope > .rist-grid-overlay');if(mode==='none'){svg?.remove();stage.dataset.ristGridMode='none';return}if(svg&&stage.dataset.ristGridMode===mode)return;svg?.remove();svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,preserveAspectRatio:'none',class:`rist-grid-overlay ${mode}`});(mode==='hex'?hex:square)(svg);grid.insertAdjacentElement('afterend',svg);stage.dataset.ristGridMode=mode}
 function scan(){document.querySelectorAll('.world-stage').forEach(decorate)}
 const mo=new MutationObserver(scan);mo.observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
 document.addEventListener('DOMContentLoaded',scan);requestAnimationFrame(scan);
})();
