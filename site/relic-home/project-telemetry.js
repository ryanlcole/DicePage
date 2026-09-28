(()=>{'use strict';
const script=document.currentScript;
const explicit=(script?.dataset?.system||'').toLowerCase();
const system=explicit==='ai'||explicit==='game'?explicit:'';
if(!system)return;
(async()=>{
 try{
  const config=await fetch('/Game/authority-config.json?ts='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null);
  const api=String(config?.apiBaseUrl||'').replace(/\/$/,'');
  if(!api)return;
  await fetch(api+'/telemetry/visit',{
   method:'POST',
   headers:{'content-type':'application/json'},
   body:JSON.stringify({system,page:location.pathname}),
   cache:'no-store',
   keepalive:true
  });
 }catch{}
})();
})();
