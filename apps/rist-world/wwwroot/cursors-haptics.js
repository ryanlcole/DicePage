(() => {
  const SOURCE = 'assets/ui/cursors/shaelvien-cursors.jpg?v=1';
  const CELLS = {
    sword:[0,0], grab:[0,1], grabOpen:[0,2], grabPinch:[0,3], compass:[0,4], colorPicker:[0,5],
    resizeX:[1,0], resizeY:[1,1], resizeNE:[1,2], resizeNW:[1,3], move:[1,4], moveRing:[1,5],
    pen:[2,0], text:[2,1], card:[2,2], paint:[2,3], fill:[2,4], erase:[2,5],
    zoomIn:[3,0], zoomOut:[3,1], rotate:[3,2], cards:[3,3], link:[3,4], forbidden:[3,5],
    help:[4,0], wait:[4,1], light:[4,2], select:[4,3], selectAlt:[4,4], selectAlt2:[4,5],
    selectTug:[5,0], penSun:[5,1], penBlue:[5,2], penLight:[5,3], penDrop:[5,4], pointer:[5,5]
  };
  const HOT = {
    sword:[8,4], pointer:[7,5], colorPicker:[8,4], text:[17,8], pen:[49,49], penSun:[49,49], penBlue:[49,49], penLight:[49,49], penDrop:[49,49],
    grab:[31,31], grabOpen:[31,31], grabPinch:[31,31], select:[31,31], selectTug:[31,31], move:[31,31], moveRing:[31,31],
    resizeX:[31,31], resizeY:[31,31], resizeNE:[31,31], resizeNW:[31,31], paint:[45,40], fill:[45,40], erase:[44,39],
    zoomIn:[23,23], zoomOut:[23,23], rotate:[31,31], cards:[31,31], card:[31,31], link:[31,31], forbidden:[31,31], help:[31,31], wait:[31,31], light:[31,31], compass:[31,31]
  };

  const isBg = (r,g,b) => {
    const hi=Math.max(r,g,b), lo=Math.min(r,g,b);
    return hi>224 && hi-lo<20;
  };

  function makeCursor(img,row,col){
    const sw=img.naturalWidth/6, sh=img.naturalHeight/6;
    const canvas=document.createElement('canvas'); canvas.width=64; canvas.height=64;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.drawImage(img,col*sw,row*sh,sw,sh,0,0,64,64);
    const image=ctx.getImageData(0,0,64,64), p=image.data;
    const candidate=new Uint8Array(64*64), transparent=new Uint8Array(64*64), queue=[];
    for(let i=0;i<64*64;i++) candidate[i]=isBg(p[i*4],p[i*4+1],p[i*4+2])?1:0;
    const push=i=>{if(candidate[i]&&!transparent[i]){transparent[i]=1;queue.push(i)}};
    for(let x=0;x<64;x++){push(x);push(63*64+x)}
    for(let y=0;y<64;y++){push(y*64);push(y*64+63)}
    for(let q=0;q<queue.length;q++){
      const i=queue[q], x=i%64, y=(i/64)|0;
      if(x>0)push(i-1); if(x<63)push(i+1); if(y>0)push(i-64); if(y<63)push(i+64);
    }
    for(let i=0;i<transparent.length;i++) if(transparent[i]) p[i*4+3]=0;
    ctx.putImageData(image,0,0);
    return canvas.toDataURL('image/png');
  }

  function installCursors(){
    if(matchMedia('(hover:none),(pointer:coarse)').matches) return;
    const img=new Image();
    img.onload=()=>{
      const root=document.documentElement.style;
      Object.entries(CELLS).forEach(([name,[row,col]])=>{
        const [hx,hy]=HOT[name]||[31,31];
        const fallback=name==='text'?'text':(name.startsWith('resize')?'move':(name.includes('grab')?'grab':'pointer'));
        root.setProperty(`--rist-cursor-${name}`,`url("${makeCursor(img,row,col)}") ${hx} ${hy}, ${fallback}`);
      });
      document.documentElement.classList.add('shaelvien-cursors-ready');
    };
    img.src=SOURCE;
  }

  const canVibrate=()=>typeof navigator.vibrate==='function';
  let lastFluid=0, fluidActive=false;
  function pulse(ms=5){
    if(!canVibrate() || document.hidden) return;
    try{navigator.vibrate(ms)}catch{}
  }
  const interactive='button,a,input,textarea,select,label,[role="button"],[draggable="true"],.tile-item,.token-item,.library-playing-card,.ccs-nav-button,.ccs-portrait-frame';
  const fluidTargets='input[type="range"],[draggable="true"],.map,.world-map,.map-surface,.board,[data-pan-surface]';

  addEventListener('pointerdown',e=>{
    if(e.pointerType!=='touch'&&e.pointerType!=='pen') return;
    const t=e.target instanceof Element?e.target:null;
    if(t?.closest(interactive)){pulse(5);}
    fluidActive=!!t?.closest(fluidTargets);
    lastFluid=performance.now();
  },{passive:true,capture:true});
  addEventListener('pointermove',e=>{
    if(!fluidActive || (e.pointerType!=='touch'&&e.pointerType!=='pen')) return;
    const now=performance.now();
    if(now-lastFluid>82){lastFluid=now;pulse(2)}
  },{passive:true,capture:true});
  addEventListener('pointerup',e=>{
    if(e.pointerType==='touch'||e.pointerType==='pen'){
      if(fluidActive)pulse(4);
      fluidActive=false;
    }
  },{passive:true,capture:true});
  addEventListener('pointercancel',()=>{fluidActive=false},{passive:true,capture:true});
  addEventListener('input',e=>{
    const t=e.target;
    if(t instanceof HTMLInputElement && (t.type==='range'||t.type==='color')){
      const now=performance.now(); if(now-lastFluid>72){lastFluid=now;pulse(2)}
    }
  },{passive:true,capture:true});
  addEventListener('change',e=>{
    const t=e.target;
    if(t instanceof HTMLSelectElement || (t instanceof HTMLInputElement && (t.type==='range'||t.type==='color'))) pulse(6);
  },{passive:true,capture:true});
  addEventListener('dragstart',()=>pulse(7),{passive:true,capture:true});
  addEventListener('drop',()=>pulse(9),{passive:true,capture:true});

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',installCursors,{once:true});
  else installCursors();
})();