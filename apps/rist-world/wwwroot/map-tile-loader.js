(()=>{
 const active=new WeakMap();
 const waitFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>resolve()));
 const loadImage=(tile,width,height)=>new Promise(resolve=>{
   const img=new Image();
   img.className='map-packet-tile';
   img.alt='';
   img.draggable=false;
   img.decoding='async';
   img.style.left=`${tile.x/width*100}%`;
   img.style.top=`${tile.y/height*100}%`;
   img.style.width=`${tile.width/width*100}%`;
   img.style.height=`${tile.height/height*100}%`;
   img.onload=()=>resolve(img);
   img.onerror=()=>resolve(null);
   img.src=tile.image;
 });
 async function hydrate(host){
   const manifestUrl=host.dataset.mapManifest;
   if(!manifestUrl||active.has(host))return;
   const token={cancel:false};active.set(host,token);
   host.classList.add('loading');
   try{
     const response=await fetch(manifestUrl,{cache:'force-cache'});
     if(!response.ok)throw new Error(`Map manifest ${response.status}`);
     const manifest=await response.json();
     if(token.cancel)return;
     const surface=document.createElement('div');
     surface.className='map-packet-surface';
     host.replaceChildren(surface);
     host.dataset.mapWidth=manifest.width;
     host.dataset.mapHeight=manifest.height;
     host.dataset.mapPackets=manifest.tiles.length;
     let loaded=0;
     for(const tile of manifest.tiles){
       if(token.cancel||!host.isConnected)break;
       const img=await loadImage(tile,manifest.width,manifest.height);
       if(img){surface.appendChild(img);loaded++;host.dataset.mapPacketsLoaded=String(loaded);}
       await waitFrame();
     }
     if(!token.cancel){host.classList.remove('loading');host.classList.add('ready');}
   }catch{
     host.classList.remove('loading');host.classList.add('error');
     host.dataset.mapError='Map packets unavailable';
   }
 }
 function scan(){document.querySelectorAll('.map-tile-map[data-map-manifest]').forEach(hydrate)}
 const observer=new MutationObserver(scan);
 function start(){observer.observe(document.documentElement,{subtree:true,childList:true});scan()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.ristMapPackets={scan};
})();
