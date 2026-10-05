(()=>{
 'use strict';

 function removeLegacyExternalPlayer(){
  // The old static /Play page is not an authoritative Shaelvien music surface.
  // Remove its legacy player entirely so it cannot fetch Drive audio or autoplay.
  if(!document.querySelector('[data-rist-play-entry]'))return;
  document.querySelectorAll('.ten-fairies-player').forEach(host=>{
   host.querySelectorAll('audio').forEach(audio=>{
    try{audio.pause();}catch{}
    audio.removeAttribute('src');
    audio.querySelectorAll('source').forEach(source=>source.removeAttribute('src'));
    try{audio.load();}catch{}
   });
   host.remove();
  });
 }

 if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',removeLegacyExternalPlayer,{once:true});
 }else{
  removeLegacyExternalPlayer();
 }
})();
