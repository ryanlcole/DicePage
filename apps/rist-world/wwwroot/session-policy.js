export function applyEightHourSessionPolicy(){
 const auth=window.ristAuth;
 if(!auth)return;
 const maxMs=8*60*60*1000;
 auth.idleMs=maxMs;
 const token=sessionStorage.getItem('rist.session');
 if(!token)return;
 let started=Number(sessionStorage.getItem('rist.sessionStarted'));
 if(!Number.isFinite(started)||started<=0){started=Date.now();sessionStorage.setItem('rist.sessionStarted',String(started));}
 const remaining=maxMs-(Date.now()-started);
 if(auth.hardTimer)clearTimeout(auth.hardTimer);
 if(remaining<=0){auth.clearSession();sessionStorage.removeItem('rist.sessionStarted');location.reload();return;}
 clearTimeout(auth.idleTimer);
 sessionStorage.setItem('rist.lastActivity',String(Date.now()));
 auth.idleTimer=setTimeout(()=>{auth.clearSession();sessionStorage.removeItem('rist.sessionStarted');location.reload();},maxMs);
 auth.hardTimer=setTimeout(()=>{auth.clearSession();sessionStorage.removeItem('rist.sessionStarted');location.reload();},remaining);
 const originalClear=auth.clearSession;
 if(!auth.eightHourClearWrapped){
  auth.eightHourClearWrapped=true;
  auth.clearSession=()=>{clearTimeout(auth.hardTimer);sessionStorage.removeItem('rist.sessionStarted');originalClear();};
 }
}
