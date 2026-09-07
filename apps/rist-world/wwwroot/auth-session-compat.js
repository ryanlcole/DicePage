(()=>{
 'use strict';
 const auth=window.ristAuth;if(!auth)return;
 auth.clearEdgeCookie=()=>{document.cookie='rist_session=; Path=/; Max-Age=0; SameSite=Lax; Secure';};
 const originalClear=auth.clearSession?.bind(auth);
 auth.clearSession=()=>{originalClear?.();auth.clearEdgeCookie();};
 auth.installIdleExpiry=()=>{
  if(auth.idleInstalled)return;
  auth.idleInstalled=true;
  const expire=()=>{
   if(!sessionStorage.getItem('rist.session'))return;
   const last=Number(sessionStorage.getItem('rist.lastActivity'))||Date.now();
   const remaining=auth.idleMs-(Date.now()-last);
   clearTimeout(auth.idleTimer);
   if(remaining<=0){auth.clearSession();location.replace('/Play/index.html?reason=session');return;}
   auth.idleTimer=setTimeout(expire,remaining);
  };
  const activity=()=>{
   if(!sessionStorage.getItem('rist.session'))return;
   sessionStorage.setItem('rist.lastActivity',String(Date.now()));
   clearTimeout(auth.idleTimer);
   auth.idleTimer=setTimeout(expire,auth.idleMs);
  };
  ['pointerdown','keydown','touchstart'].forEach(name=>addEventListener(name,activity,{passive:true}));
  addEventListener('visibilitychange',()=>{if(!document.hidden)expire();},{passive:true});
  activity();
 };
 if(sessionStorage.getItem('rist.session'))auth.installIdleExpiry();
})();
