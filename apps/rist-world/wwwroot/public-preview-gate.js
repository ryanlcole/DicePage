(()=>{
 'use strict';

 async function begin(mode){
  const intent=mode==='signup'?'signup':'login';
  sessionStorage.removeItem('rist-public-preview');
  delete document.documentElement.dataset.ristPublicPreview;
  try{
   localStorage.setItem('rist.auth.intent',intent);
   const cfg=await fetch('auth-config.json',{cache:'no-store'}).then(r=>{
    if(!r.ok)throw new Error(`auth-config ${r.status}`);
    return r.json();
   });
   if(!cfg?.apiBaseUrl)throw new Error('Auth endpoint is not configured.');
   location.href=`${cfg.apiBaseUrl.replace(/\/$/,'')}/auth/login`;
  }catch(error){
   console.error('RIST authentication could not start.',error);
   window.dispatchEvent(new CustomEvent('rist-auth-error',{detail:{message:'Authentication could not be started. Please try again.'}}));
  }
 }

 // Kept under the existing filename for deployment compatibility, but there is
 // deliberately no preview mode anymore. Anonymous users receive only the
 // authentication entry surface; the Blazor world is mounted after verification.
 window.RistEntry=Object.freeze({begin});
 sessionStorage.removeItem('rist-public-preview');
 delete document.documentElement.dataset.ristPublicPreview;
})();
