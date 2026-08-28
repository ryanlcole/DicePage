(()=>{
  if(window.RistFauxDepth)return;

  let motionAttached=false;
  let motionRequested=false;
  let activeMouseMap=null;

  const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  const mapFor=target=>target?.closest?.('.map');

  function apply(map,x,y){
    if(!map)return;
    x=clamp(x,-18,18);
    y=clamp(y,-14,14);
    map.style.setProperty('--rist-depth-x',`${x.toFixed(2)}px`);
    map.style.setProperty('--rist-depth-y',`${y.toFixed(2)}px`);
    map.style.setProperty('--rist-depth-base-x',`${(-x*.18).toFixed(2)}px`);
    map.style.setProperty('--rist-depth-base-y',`${(-y*.18).toFixed(2)}px`);
    map.style.setProperty('--rist-depth-grid-x',`${(-x*.05).toFixed(2)}px`);
    map.style.setProperty('--rist-depth-grid-y',`${(-y*.05).toFixed(2)}px`);
    map.style.setProperty('--rist-depth-tile-x',`${(x*.12).toFixed(2)}px`);
    map.style.setProperty('--rist-depth-tile-y',`${(y*.12).toFixed(2)}px`);
    map.style.setProperty('--rist-depth-piece-x',`${(x*.34).toFixed(2)}px`);
    map.style.setProperty('--rist-depth-piece-y',`${(y*.34).toFixed(2)}px`);
  }

  function pointerDepth(event){
    if(event.pointerType && event.pointerType!=='mouse')return;
    if((event.buttons&1)!==1)return;
    const map=activeMouseMap||mapFor(event.target);
    if(!map)return;
    const rect=map.getBoundingClientRect();
    if(rect.width<=0||rect.height<=0)return;
    const nx=((event.clientX-rect.left)/rect.width-.5)*2;
    const ny=((event.clientY-rect.top)/rect.height-.5)*2;
    apply(map,nx*12,ny*9);
  }

  function attachMotion(){
    if(motionAttached)return;
    motionAttached=true;
    addEventListener('deviceorientation',event=>{
      const gamma=Number.isFinite(event.gamma)?event.gamma:0;
      const beta=Number.isFinite(event.beta)?event.beta:0;
      const map=document.querySelector('.map');
      if(map)apply(map,clamp(gamma/3,-14,14),clamp((beta-45)/5,-10,10));
    },{passive:true});
  }

  async function requestMotion(){
    if(motionRequested)return;
    motionRequested=true;
    try{
      const ctor=window.DeviceOrientationEvent;
      if(!ctor)return;
      if(typeof ctor.requestPermission==='function'){
        const permission=await ctor.requestPermission();
        if(permission!=='granted')return;
      }
      attachMotion();
    }catch{
      // Mouse drag remains available when motion permission is denied.
    }
  }

  document.addEventListener('pointerdown',event=>{
    const map=mapFor(event.target);
    if(!map)return;
    if(!event.pointerType||event.pointerType==='mouse'){
      if(event.button===0)activeMouseMap=map;
    }else{
      void requestMotion();
    }
  },{passive:true,capture:true});
  document.addEventListener('pointermove',pointerDepth,{passive:true,capture:true});
  document.addEventListener('pointerup',event=>{
    if(!event.pointerType||event.pointerType==='mouse')activeMouseMap=null;
  },{passive:true,capture:true});
  document.addEventListener('pointercancel',()=>{activeMouseMap=null;},{passive:true,capture:true});

  window.RistFauxDepth={apply,requestMotion};
})();
