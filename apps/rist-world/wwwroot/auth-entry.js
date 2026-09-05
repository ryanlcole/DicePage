(()=>{
 'use strict';

 async function begin(mode){
  const intent=mode==='signup'?'signup':'login';
  try{
   localStorage.setItem('rist.auth.intent',intent);
   const response=await fetch('auth-config.json',{cache:'no-store'});
   if(!response.ok)throw new Error(`auth-config ${response.status}`);
   const cfg=await response.json();
   if(!cfg?.apiBaseUrl)throw new Error('Auth endpoint is not configured.');
   location.assign(`${cfg.apiBaseUrl.replace(/\/$/,'')}/auth/login`);
  }catch(error){
   console.error('RIST authentication could not start.',error);
   window.dispatchEvent(new CustomEvent('rist-auth-error',{detail:{message:'Authentication could not be started. Please try again.'}}));
  }
 }

 window.RistEntry=Object.freeze({begin});
})();
