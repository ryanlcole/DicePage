(()=>{
 'use strict';
 const auth=window.ristAuth;if(!auth)return;
 auth.clearEdgeCookie=()=>{document.cookie='rist_session=; Path=/; Max-Age=0; SameSite=Lax; Secure';};
 const originalClear=auth.clearSession?.bind(auth);
 auth.clearSession=()=>{
  originalClear?.();
  auth.clearEdgeCookie();
 };
 // Compatibility only: the provider-issued session expiry is authoritative.
 // Do not install an activity/idle timer here.
 if(sessionStorage.getItem('rist.session'))auth.installSessionExpiry?.();
})();