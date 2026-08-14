window.ristWorld={
 point:(el,x,y)=>{const r=el.getBoundingClientRect();return[(x-r.left)/r.width,(y-r.top)/r.height]},
 worldPoint:(el,x,y,panX,panY,zoom)=>{
  const r=el.getBoundingClientRect();
  const sx=(x-r.left)/r.width;
  const sy=(y-r.top)/r.height;
  const z=Math.max(Number(zoom)||1,.01);
  return [((sx-.5)/z)+.5-(Number(panX)||0)/(r.width*z),((sy-.5)/z)+.5-(Number(panY)||0)/(r.height*z)];
 },
 dropPoint:(el,x,y,panX,panY,zoom)=>{
  const r=el.getBoundingClientRect();
  const inside=x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;
  if(!inside)return [0,0,0];
  const sx=(x-r.left)/r.width;
  const sy=(y-r.top)/r.height;
  const z=Math.max(Number(zoom)||1,.01);
  return [1,((sx-.5)/z)+.5-(Number(panX)||0)/(r.width*z),((sy-.5)/z)+.5-(Number(panY)||0)/(r.height*z)];
 }
};

(()=>{
 let scheduled=false;
 const centerOf=el=>{const r=el.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};};
 function resolveDiceCollisions(){
  scheduled=false;
  const map=document.querySelector('.map');
  if(!map)return;
  const dice=[...map.querySelectorAll('.rolled-die')];
  if(dice.length<2)return;
  const mr=map.getBoundingClientRect();
  const minDistance=Math.max(48,Math.min(62,mr.width*.1));
  const placed=[];
  dice.forEach((die,index)=>{
   die.style.setProperty('--collision-x','0px');
   die.style.setProperty('--collision-y','0px');
   let ox=0,oy=0;
   for(let pass=0;pass<32;pass++){
    const c=centerOf(die);
    let hit=null;
    for(const p of placed){
     const dx=c.x-p.x,dy=c.y-p.y;
     const d=Math.hypot(dx,dy);
     if(d<minDistance){hit={p,dx,dy,d};break;}
    }
    if(!hit)break;
    let ax=hit.dx,ay=hit.dy;
    if(hit.d<1){const angle=((index+1)*2.399963229728653);ax=Math.cos(angle);ay=Math.sin(angle);}
    const len=Math.max(Math.hypot(ax,ay),.001);
    const push=(minDistance-hit.d)+5;
    ox+=(ax/len)*push;
    oy+=(ay/len)*push;
    const base=centerOf(die);
    const nx=Math.min(mr.right-26,Math.max(mr.left+26,base.x+ox));
    const ny=Math.min(mr.bottom-26,Math.max(mr.top+26,base.y+oy));
    ox+=nx-(base.x+ox);
    oy+=ny-(base.y+oy);
    die.style.setProperty('--collision-x',`${ox.toFixed(1)}px`);
    die.style.setProperty('--collision-y',`${oy.toFixed(1)}px`);
   }
   placed.push(centerOf(die));
  });
 }
 function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(resolveDiceCollisions);}
 const observer=new MutationObserver(mutations=>{
  if(mutations.some(m=>m.type==='childList'&&(m.addedNodes.length||m.removedNodes.length)))schedule();
 });
 function start(){observer.observe(document.body,{childList:true,subtree:true});schedule();}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.addEventListener('resize',schedule,{passive:true});
 window.addEventListener('orientationchange',schedule,{passive:true});
})();
