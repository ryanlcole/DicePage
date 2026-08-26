(()=>{
 const watched=new WeakMap();
 const selector='#card-library img,.tile-browser img,.tray-item img,.spellbook-card-strip img';
 const io=new IntersectionObserver(entries=>{
  for(const entry of entries){
   const img=entry.target,meta=watched.get(img);if(!meta)continue;
   if(entry.isIntersecting){
    if(!img.getAttribute('src')&&meta.src)img.setAttribute('src',meta.src);
    img.dataset.ristResident='1';
   }else{
    img.dataset.ristResident='0';
    // Remove the decoded image surface from the live DOM. The browser HTTP
    // cache/service worker can still satisfy it instantly when it returns.
    if(img.complete&&img.getAttribute('src')){
      meta.src=img.getAttribute('src');
      img.removeAttribute('src');
    }
   }
  }
 },{root:null,rootMargin:'240px 240px',threshold:0});
 function watch(img){
  if(watched.has(img))return;
  const src=img.getAttribute('src');if(!src)return;
  watched.set(img,{src});img.dataset.ristSrc=src;io.observe(img);
 }
 function scan(root=document){root.querySelectorAll?.(selector).forEach(watch)}
 const mo=new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes)if(node.nodeType===1){if(node.matches?.(selector))watch(node);scan(node)}});
 function start(){scan();mo.observe(document.documentElement,{subtree:true,childList:true})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.ristViewportCache={scan};
})();
