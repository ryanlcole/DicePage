(()=>{
'use strict';
const stages=['Testing','QATest','Staging','QAStaging'];
let activeStage='Testing';
let apiBase='';
let sessionToken='';
let profile=null;
let releaseApi='';
const $=id=>document.getElementById(id);
const setBadge=(text,kind='waiting')=>{const el=$('systemBadge');el.textContent=text;el.className='system-badge '+kind};
const setActionState=(enabled,message)=>{ $('promoteButton').disabled=!enabled; $('revokeButton').disabled=!enabled; $('actionHint').textContent=message; };
const setPanel=(record={})=>{
 $('stageTitle').textContent=activeStage;
 $('artifactId').textContent=record.artifactId||'—';
 $('healthState').textContent=record.health||'—';
 $('testState').textContent=record.tests||'—';
 $('deployedAt').textContent=record.deployedAt||'—';
 $('releaseStatus').textContent=record.message||'No release record loaded.';
 const state=$('stageState'); state.textContent=record.state||'Unknown'; state.className='state-pill '+(record.state==='Ready'?'good':'');
};
async function json(url,options={}){
 const headers={Accept:'application/json',...(options.headers||{})};
 if(sessionToken) headers.Authorization='Bearer '+sessionToken;
 const response=await fetch(url,{...options,headers,cache:'no-store'});
 if(response.status===401||response.status===403) throw new Error('unauthorized');
 if(!response.ok) throw new Error('http '+response.status);
 if(response.status===204) return null;
 return response.json();
}
async function loadConfig(){
 const [auth,release]=await Promise.all([
  fetch('../auth-config.json',{cache:'no-store'}).then(r=>r.ok?r.json():{}).catch(()=>({})),
  fetch('release-control-config.json',{cache:'no-store'}).then(r=>r.ok?r.json():{}).catch(()=>({}))
 ]);
 apiBase=(auth.apiBaseUrl||'').replace(/\/$/,'');
 releaseApi=(release.apiBaseUrl||'').replace(/\/$/,'');
}
async function authenticate(){
 if(!apiBase||!window.ristAuth||typeof window.ristAuth.captureSession!=='function') throw new Error('auth unavailable');
 sessionToken=await window.ristAuth.captureSession(apiBase)||'';
 if(!sessionToken){
  setBadge('LOGIN REQUIRED','bad');
  $('identityLine').textContent='Discord login is required to use Launcher.';
  setActionState(false,'Release controls are locked until Discord authentication succeeds.');
  return false;
 }
 profile=await json(apiBase+'/me');
 if(!profile) throw new Error('profile unavailable');
 $('identityLine').textContent=`${profile.displayName||'Authenticated user'} · Discord verified`;
 setBadge('AUTHENTICATED','good');
 return true;
}
async function refresh(){
 if(!releaseApi){setPanel({message:'Release-control authority is not deployed yet. Launcher is read-only.'});setActionState(false,'AWS release-control API must be deployed before Promote/Revoke can operate.');return;}
 try{
  const data=await json(`${releaseApi}/release/environments/${encodeURIComponent(activeStage)}`);
  setPanel(data||{});
  const allowed=Boolean(data&&data.canManage);
  setActionState(allowed,allowed?'Promotion changes are authorized and recorded by AWS.':'Your authenticated account does not have release-management permission.');
 }catch(err){
  setPanel({state:'Unavailable',message:'AWS release-control authority could not be reached.'});
  setActionState(false,'Promotion is locked because server-side authority is unavailable.');
 }
}
async function change(direction){
 const button=direction==='promote'?$('promoteButton'):$('revokeButton');
 if(button.disabled||!releaseApi)return;
 button.disabled=true;
 try{
  await json(`${releaseApi}/release/${direction}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:activeStage})});
  await refresh();
 }catch(err){
  $('releaseStatus').textContent=`${direction==='promote'?'Promotion':'Revoke'} failed safely. No local state was changed.`;
 }finally{button.disabled=false;}
}
document.querySelectorAll('.stage-tab').forEach(tab=>tab.addEventListener('click',async()=>{
 activeStage=tab.dataset.stage;
 document.querySelectorAll('.stage-tab').forEach(x=>x.classList.toggle('active',x===tab));
 setPanel({message:'Loading authoritative environment state…'});
 await refresh();
}));
$('promoteButton').addEventListener('click',()=>change('promote'));
$('revokeButton').addEventListener('click',()=>change('revoke'));
(async()=>{
 try{await loadConfig();if(await authenticate()) await refresh();}
 catch(err){setBadge('LOCKED','bad');$('identityLine').textContent='Launcher could not validate the Discord session.';setActionState(false,'Fail-closed: release controls remain unavailable.');}
})();
})();
