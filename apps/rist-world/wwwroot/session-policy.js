const TOKEN_KEY='rist.session';
const START_KEY='rist.sessionStarted';
const LAST_KEY='rist.lastActivity';
const MAX_MS=8*60*60*1000;

export function restorePersistentSession(){
 const token=localStorage.getItem(TOKEN_KEY);
 if(!token)return;
 const started=Number(localStorage.getItem(START_KEY));
 if(Number.isFinite(started)&&started>0&&Date.now()-started>=MAX_MS){
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(START_KEY);
  localStorage.removeItem(LAST_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(START_KEY);
  sessionStorage.removeItem(LAST_KEY);
  return;
 }
 sessionStorage.setItem(TOKEN_KEY,token);
 if(Number.isFinite(started)&&started>0)sessionStorage.setItem(START_KEY,String(started));
 const last=localStorage.getItem(LAST_KEY);
 if(last)sessionStorage.setItem(LAST_KEY,last);
}

export function applyEightHourSessionPolicy(){
 const auth=window.ristAuth;
 if(!auth)return;
 auth.idleMs=MAX_MS;
 const token=sessionStorage.getItem(TOKEN_KEY);
 if(!token)return;
 let started=Number(sessionStorage.getItem(START_KEY)||localStorage.getItem(START_KEY));
 if(!Number.isFinite(started)||started<=0)started=Date.now();
 sessionStorage.setItem(START_KEY,String(started));
 localStorage.setItem(TOKEN_KEY,token);
 localStorage.setItem(START_KEY,String(started));
 const remaining=MAX_MS-(Date.now()-started);
 if(auth.hardTimer)clearTimeout(auth.hardTimer);
 if(remaining<=0){auth.clearSession();location.reload();return;}
 clearTimeout(auth.idleTimer);
 const now=String(Date.now());
 sessionStorage.setItem(LAST_KEY,now);
 localStorage.setItem(LAST_KEY,now);
 auth.idleTimer=setTimeout(()=>{auth.clearSession();location.reload();},remaining);
 auth.hardTimer=setTimeout(()=>{auth.clearSession();location.reload();},remaining);
 const originalClear=auth.clearSession;
 if(!auth.eightHourClearWrapped){
  auth.eightHourClearWrapped=true;
  auth.clearSession=()=>{
   clearTimeout(auth.hardTimer);
   localStorage.removeItem(TOKEN_KEY);
   localStorage.removeItem(START_KEY);
   localStorage.removeItem(LAST_KEY);
   sessionStorage.removeItem(START_KEY);
   originalClear();
  };
 }
}
