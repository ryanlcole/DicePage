(()=>{
 'use strict';

 function enforceUserControlledPlayback(){
  document.querySelectorAll('.ten-fairies-player audio').forEach(audio=>{
   audio.autoplay=false;
   audio.removeAttribute('autoplay');
  });
 }

 if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',enforceUserControlledPlayback,{once:true});
 }else{
  enforceUserControlledPlayback();
 }
})();
