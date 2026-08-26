(()=>{
 const active=new WeakMap();
 const waitFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>resolve()));
 const loadImage=tile=>new Promise(resolve=>{
   const img=new Image();
   img.className='map-packet-tile';
   img.alt='';
   img.draggable=false;
   img.decoding='async';
   img.style.left=`${tile.x}px`;
   img.style.top=`${tile.y}px`;
   img.style.width=`${tile.width}px`;
   img.style.height=`${tile.height}px`;
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
     host.style.setProperty('--map-source-width',String(manifest.width));
     host.style.setProperty('--map-source-height',String(manifest.height));
     const surface=document.createElement('div');
     surface.className='map-packet-surface';
     surface.style.width=`${manifest.width}px`;
     surface.style.height=`${manifest.height}px`;
     host.replaceChildren(surface);
     host.dataset.mapWidth=manifest.width;
     host.dataset.mapHeight=manifest.height;
     host.dataset.mapPackets=manifest.tiles.length;
     let loaded=0;
     for(const tile of manifest.tiles){
       if(token.cancel||!host.isConnected)break;
       const img=await loadImage(tile);
       if(img){surface.appendChild(img);loaded++;host.dataset.mapPacketsLoaded=String(loaded);}
       await waitFrame();
     }
     if(!token.cancel){host.classList.remove('loading');host.classList.add('ready');}
   }catch(err){
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
