(()=>{
 'use strict';
 const $=id=>document.getElementById(id);
 const intro=$('intro'),launcher=$('launcher'),entry=$('entry'),signup=$('signup'),welcome=$('welcome');
 const error=$('error'),status=$('status'),desktopBack=$('desktop-back');
 const views={entry,signup,welcome};
 const game='/Game/index.html';
 const cookieName='rist_session';
 const signupDraftKey='rist.signup.draft';
 const authIntentKey='rist.auth.intent';
 const profileKey='account/profile.json';
 const playSettings={role:'Roleplayer',domain:'Shaelvien MMO'};
 let api='',authenticated=false,profileReady=false,currentView='entry',launching=false;

 const setCookie=token=>{document.cookie=`${cookieName}=${encodeURIComponent(token)}; Path=/Game/; Max-Age=28800; Secure; SameSite=Lax`};
 const clearCookie=()=>{document.cookie=`${cookieName}=; Path=/Game/; Max-Age=0; Secure; SameSite=Lax`};
 const setView=name=>{
  currentView=name;
  Object.entries(views).forEach(([key,node])=>node.hidden=key!==name);
  desktopBack.classList.toggle('visible',name==='signup');
  error.textContent='';status.textContent='';
 };
 const showLauncher=name=>{intro.hidden=true;launcher.hidden=false;setView(name)};

 async function advanceIntro(){
  if(intro.hidden)return;
  if(authenticated&&profileReady){
   showLauncher('entry');
   status.textContent='Entering Shaelvien…';
   await launch();
   return;
  }
  showLauncher(authenticated?'signup':'entry');
 }

 async function config(){
  if(api)return api;
  const r=await fetch('./auth-config.json',{cache:'no-store'});
  if(!r.ok)throw new Error('Account service configuration is unavailable.');
  const c=await r.json();api=(c.apiBaseUrl||'').replace(/\/$/,'');
  if(!api)throw new Error('Account service configuration is incomplete.');
  return api;
 }
 async function verify(token){
  const base=await config();
  const r=await fetch(base+'/me',{headers:{Authorization:'Bearer '+token},cache:'no-store'});
  return r.ok;
 }
 async function loadProfile(token){
  const base=await config();
  const r=await fetch(base+'/storage/download?key='+encodeURIComponent(profileKey),{headers:{Authorization:'Bearer '+token},cache:'no-store'});
  if(r.status===404)return null;
  if(!r.ok)throw new Error('Your RIST profile could not be checked.');
  const p=await r.json();
  if(!p?.url)return null;
  const file=await fetch(p.url,{cache:'no-store'});
  if(file.status===404)return null;
  if(!file.ok)throw new Error('Your RIST profile could not be checked.');
  return await file.json();
 }
 async function createProfile(token,draft){
  const handle=(draft?.handle||'').trim();
  const plan=draft?.plan||'';
  if(handle.length<1||handle.length>32)throw new Error('Enter a handle from 1 to 32 characters.');
  if(plan!=='player'&&plan!=='gm-player')throw new Error('Choose a plan before continuing.');
  if(!draft?.agreements)throw new Error('Accept the agreements before continuing.');
  const existing=await loadProfile(token);
  if(existing){profileReady=true;return existing}
  const created={
   AccountId:crypto.randomUUID(),PlayerAlias:handle,Plan:plan,
   CreatedAtUtc:new Date().toISOString(),TermsAcceptedAtUtc:new Date().toISOString(),TermsVersion:'2026-08-30',
   NsfwAccessEnabled:false,Age21AttestedAtUtc:null,NsfwAttestationVersion:null,ContentAccess:null
  };
  const base=await config();
  const prep=await fetch(base+'/storage/upload',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({key:profileKey,contentType:'application/json'})});
  if(!prep.ok)throw new Error('Your RIST profile could not be created. Please try again.');
  const post=await prep.json();
  if(!post?.url||!post?.fields)throw new Error('Your RIST profile could not be created. Please try again.');
  const form=new FormData();
  Object.entries(post.fields).forEach(([key,value])=>form.append(key,value));
  form.append('file',new Blob([JSON.stringify(created)],{type:'application/json'}),'profile.json');
  const upload=await fetch(post.url,{method:'POST',body:form});
  if(!upload.ok)throw new Error('Your RIST profile could not be created. Please try again.');
  profileReady=true;
  return created;
 }
 async function launch(){
  if(launching)return;
  if(!authenticated){setView('entry');return}
  const token=sessionStorage.getItem('rist.session');
  if(!token){authenticated=false;profileReady=false;setView('entry');return}
  launching=true;
  try{
   status.textContent='Entering Shaelvien…';
   profileReady=!!(await loadProfile(token));
   if(!profileReady){
    launching=false;
    setView('signup');
    error.textContent='Complete your RIST profile before entering Shaelvien.';
    return;
   }
   sessionStorage.setItem('rist.launch.intent','play');
   sessionStorage.setItem('rist.launch.settings',JSON.stringify(playSettings));
   sessionStorage.setItem('rist.lastActivity',String(Date.now()));
   location.assign(game);
  }catch(e){
   launching=false;
   error.textContent=e?.message||'Shaelvien could not be started.';
  }
 }
 async function completeHandoff(handoff){
  intro.hidden=true;launcher.hidden=false;setView('entry');status.textContent='Completing secure sign in…';
  const authIntent=sessionStorage.getItem(authIntentKey);
  const base=await config();
  const r=await fetch(base+'/auth/session?handoff='+encodeURIComponent(handoff),{cache:'no-store'});
  if(!r.ok)throw new Error('The sign-in handoff expired. Please sign in again.');
  const p=await r.json();
  if(!p.sessionToken)throw new Error('The account service returned an invalid session.');
  sessionStorage.setItem('rist.session',p.sessionToken);
  sessionStorage.setItem('rist.lastActivity',String(Date.now()));
  setCookie(p.sessionToken);authenticated=true;
  const isSignup=authIntent==='signup';
  const rawDraft=isSignup?sessionStorage.getItem(signupDraftKey):null;
  sessionStorage.removeItem(authIntentKey);
  localStorage.removeItem(authIntentKey);
  if(isSignup){
   let draft=null;
   if(rawDraft){try{draft=JSON.parse(rawDraft)}catch{}}
   await createProfile(p.sessionToken,draft);
   const handle=draft?.handle||'';
   $('welcome-copy').textContent=handle?`Welcome, ${handle}. Your account is ready.`:'Your account is ready.';
   setView('welcome');
   return;
  }
  sessionStorage.removeItem(signupDraftKey);
  profileReady=!!(await loadProfile(p.sessionToken));
  if(profileReady){await launch();return}
  setView('signup');
  error.textContent='Complete your RIST profile before entering Shaelvien.';
 }
 async function resume(){
  const token=sessionStorage.getItem('rist.session');
  if(!token)return false;
  try{
   if(await verify(token)){
    setCookie(token);authenticated=true;
    profileReady=!!(await loadProfile(token));
    if(intro.hidden&&currentView==='entry'){
     if(profileReady)await launch();
     else setView('signup');
    }
    return true;
   }
  }catch{}
  sessionStorage.removeItem('rist.session');sessionStorage.removeItem('rist.lastActivity');clearCookie();
  authenticated=false;profileReady=false;
  return false;
 }
 async function begin(intent){
  error.textContent='';
  try{
   const base=await config();
   if(intent==='login'){
    sessionStorage.removeItem(signupDraftKey);
    localStorage.removeItem('rist.signup.alias');
    localStorage.removeItem('rist.signup.plan');
    localStorage.removeItem('rist.signup.termsAccepted');
   }
   sessionStorage.setItem(authIntentKey,intent);
   localStorage.setItem(authIntentKey,intent);
   location.assign(base+'/auth/login');
  }catch(e){error.textContent=e?.message||'Unable to start sign in.'}
 }

 $('continue').addEventListener('click',()=>{void advanceIntro()});
 document.addEventListener('keydown',e=>{if(!intro.hidden){e.preventDefault();void advanceIntro()}});
 $('signin').addEventListener('click',()=>{status.textContent='Opening Discord sign in…';void begin('login')});
 $('signup-open').addEventListener('click',()=>{setView('signup');$('handle').focus()});
 $('signup-back').addEventListener('click',()=>setView('entry'));
 desktopBack.addEventListener('click',()=>setView('entry'));
 signup.addEventListener('submit',async e=>{
  e.preventDefault();
  const submit=e.submitter;
  const handle=$('handle').value.trim();
  const plan=$('plan').value;
  if(handle.length<1||handle.length>32){error.textContent='Enter a handle from 1 to 32 characters.';return}
  if(plan!=='player'&&plan!=='gm-player'){error.textContent='Choose a plan before continuing.';return}
  if(!$('agreements').checked){error.textContent='Accept the agreements before continuing.';return}
  if(submit)submit.disabled=true;
  status.textContent='Continuing…';
  const draft={handle,plan,agreements:true,agreedAt:new Date().toISOString()};
  try{
   sessionStorage.setItem(signupDraftKey,JSON.stringify(draft));
   localStorage.setItem('rist.signup.alias',handle);
   localStorage.setItem('rist.signup.plan',plan);
   localStorage.setItem('rist.signup.termsAccepted','true');
  }catch{
   if(submit)submit.disabled=false;
   error.textContent='Account details could not be saved in this browser. Enable site storage and try again.';
   return;
  }
  const token=sessionStorage.getItem('rist.session');
  if(authenticated&&token){
   try{
    status.textContent='Creating your RIST profile…';
    await createProfile(token,draft);
    $('welcome-copy').textContent=`Welcome, ${handle}. Your account is ready.`;
    setView('welcome');
   }catch(e){
    if(submit)submit.disabled=false;
    error.textContent=e?.message||'Your RIST profile could not be created. Please try again.';
   }
   return;
  }
  await begin('signup');
  if(submit)submit.disabled=false;
 });
 $('welcome-continue').addEventListener('click',()=>{
  sessionStorage.removeItem(signupDraftKey);
  void launch();
 });

 (async()=>{
  try{
   const q=new URLSearchParams(location.search),handoff=q.get('rist_handoff');
   if(handoff){history.replaceState(null,'',location.pathname);await completeHandoff(handoff);return}
   authenticated=await resume();
  }catch(e){clearCookie();authenticated=false;profileReady=false;status.textContent='';error.textContent=e?.message||'Unable to complete sign in.'}
 })();
})();
