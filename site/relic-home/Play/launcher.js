(()=>{
 'use strict';
 const $=id=>document.getElementById(id);
 const intro=$('intro'),launcher=$('launcher'),desktopBack=$('desktop-back');
 const views={entry:$('entry'),signup:$('signup'),welcome:$('welcome'),home:$('home'),settings:$('settings')};
 const error=$('error'),status=$('status');
 const game='/Game/index.html';
 const previewGame='/Game/index.html?preview=Geonaph';
 const cookieName='rist_session';
 const signupDraftKey='rist.signup.draft';
 const authIntentKey='rist.auth.intent';
 const profileKey='account/profile.json';
 const settingsKey='rist.launch.settings';
 const defaultSettings={role:'Roleplayer',domain:'Shaelvien MMO'};
 let api='',authenticated=false,profileReady=false,currentView='entry',launching=false;

 const readSettings=()=>{
  try{
   const saved=JSON.parse(localStorage.getItem(settingsKey)||'null');
   return {
    role:saved?.role==='GameMaster'?'GameMaster':'Roleplayer',
    domain:saved?.domain==='RIST Sandbox'?'RIST Sandbox':'Shaelvien MMO'
   };
  }catch{return {...defaultSettings}}
 };
 const saveSettings=value=>{
  const next={
   role:value?.role==='GameMaster'?'GameMaster':'Roleplayer',
   domain:value?.domain==='RIST Sandbox'?'RIST Sandbox':'Shaelvien MMO'
  };
  localStorage.setItem(settingsKey,JSON.stringify(next));
  return next;
 };
 const setCookie=token=>{document.cookie=`${cookieName}=${encodeURIComponent(token)}; Path=/Game/; Max-Age=28800; Secure; SameSite=Lax`};
 const clearCookie=()=>{document.cookie=`${cookieName}=; Path=/Game/; Max-Age=0; Secure; SameSite=Lax`};
 const clearMessages=()=>{error.textContent='';status.textContent=''};
 const focusView=name=>requestAnimationFrame(()=>{
  const node=views[name];
  const target=node?.querySelector('button:not([disabled]),input:not([disabled]),select:not([disabled])');
  target?.focus({preventScroll:true});
 });
 const setView=name=>{
  currentView=name;
  Object.entries(views).forEach(([key,node])=>node.hidden=key!==name);
  desktopBack.classList.toggle('visible',name==='signup'||name==='settings');
  clearMessages();
  if(name==='home')renderSettingsSummary();
  if(name==='settings')hydrateSettings();
  focusView(name);
 };
 const showLauncher=name=>{intro.hidden=true;launcher.hidden=false;setView(name)};
 const renderSettingsSummary=()=>{
  const s=readSettings();
  const host=$('setting-summary');
  if(host)host.textContent=`Role: ${s.role} · Domain: ${s.domain}`;
 };
 const hydrateSettings=()=>{
  const s=readSettings();
  $('role').value=s.role;$('domain').value=s.domain;
 };
 const showAuthenticatedHome=()=>showLauncher(profileReady?'home':'signup');

 async function advanceIntro(){
  if(intro.hidden)return;
  if(authenticated){showAuthenticatedHome();return}
  showLauncher('entry');
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
 async function launch(intent){
  if(launching)return;
  const preview=intent==='preview';
  if(!preview&&!authenticated){setView('entry');return}
  if(!preview&&!profileReady){setView('signup');return}
  launching=true;
  try{
   const settings=preview?{role:'Roleplayer',domain:'RIST Sandbox',inviteCode:'Geonaph'}:readSettings();
   sessionStorage.setItem('rist.launch.intent',preview?'preview':intent||'load');
   sessionStorage.setItem('rist.launch.settings',JSON.stringify(settings));
   sessionStorage.setItem('rist.lastActivity',String(Date.now()));
   status.textContent=preview?'Opening public preview…':'Entering Shaelvien…';
   location.assign(preview?previewGame:game);
  }catch(e){
   launching=false;
   error.textContent=e?.message||'Shaelvien could not be started.';
  }
 }
 async function completeHandoff(handoff){
  intro.hidden=true;launcher.hidden=false;setView('entry');status.textContent='Completing secure sign in…';
  const authIntent=sessionStorage.getItem(authIntentKey)||localStorage.getItem(authIntentKey);
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
  sessionStorage.removeItem(authIntentKey);localStorage.removeItem(authIntentKey);
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
  showAuthenticatedHome();
 }
 async function resume(){
  const token=sessionStorage.getItem('rist.session');
  if(!token)return false;
  try{
   if(await verify(token)){
    setCookie(token);authenticated=true;
    profileReady=!!(await loadProfile(token));
    return true;
   }
  }catch{}
  sessionStorage.removeItem('rist.session');sessionStorage.removeItem('rist.lastActivity');clearCookie();
  authenticated=false;profileReady=false;
  return false;
 }
 async function begin(intent){
  clearMessages();
  try{
   const base=await config();
   if(intent==='login'){
    sessionStorage.removeItem(signupDraftKey);
    localStorage.removeItem('rist.signup.alias');
    localStorage.removeItem('rist.signup.plan');
    localStorage.removeItem('rist.signup.termsAccepted');
   }
   sessionStorage.setItem(authIntentKey,intent);localStorage.setItem(authIntentKey,intent);
   location.assign(base+'/auth/login');
  }catch(e){error.textContent=e?.message||'Unable to start sign in.'}
 }

 $('continue').addEventListener('click',()=>{void advanceIntro()});
 document.addEventListener('keydown',e=>{
  if(!intro.hidden)return;
  if(e.key==='Tab'||e.key==='Shift'||e.key==='Control'||e.key==='Alt'||e.key==='Meta')return;
  e.preventDefault();void advanceIntro();
 });
 $('signin').addEventListener('click',()=>{status.textContent='Opening Discord sign in…';void begin('login')});
 $('signup-open').addEventListener('click',()=>setView('signup'));
 $('preview').addEventListener('click',()=>{void launch('preview')});
 $('signup-back').addEventListener('click',()=>setView(authenticated&&profileReady?'home':'entry'));
 desktopBack.addEventListener('click',()=>setView(currentView==='settings'?'home':authenticated&&profileReady?'home':'entry'));
 views.signup.addEventListener('submit',async e=>{
  e.preventDefault();
  const submit=e.submitter;
  const handle=$('handle').value.trim(),plan=$('plan').value;
  if(handle.length<1||handle.length>32){error.textContent='Enter a handle from 1 to 32 characters.';return}
  if(plan!=='player'&&plan!=='gm-player'){error.textContent='Choose a plan before continuing.';return}
  if(!$('agreements').checked){error.textContent='Accept the agreements before continuing.';return}
  if(submit)submit.disabled=true;
  status.textContent='Continuing…';
  const draft={handle,plan,agreements:true,agreedAt:new Date().toISOString()};
  try{
   sessionStorage.setItem(signupDraftKey,JSON.stringify(draft));
   localStorage.setItem('rist.signup.alias',handle);localStorage.setItem('rist.signup.plan',plan);localStorage.setItem('rist.signup.termsAccepted','true');
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
   }catch(e){error.textContent=e?.message||'Your RIST profile could not be created. Please try again.'}
   finally{if(submit)submit.disabled=false}
   return;
  }
  await begin('signup');
  if(submit)submit.disabled=false;
 });
 $('welcome-continue').addEventListener('click',()=>{sessionStorage.removeItem(signupDraftKey);setView('home')});
 $('new-campaign').addEventListener('click',()=>{void launch('new')});
 $('load-campaign').addEventListener('click',()=>{void launch('load')});
 $('settings-open').addEventListener('click',()=>setView('settings'));
 $('settings-back').addEventListener('click',()=>setView('home'));
 views.settings.addEventListener('submit',e=>{
  e.preventDefault();saveSettings({role:$('role').value,domain:$('domain').value});setView('home');status.textContent='Settings saved.';
 });

 (async()=>{
  try{
   saveSettings(readSettings());
   const q=new URLSearchParams(location.search),handoff=q.get('rist_handoff');
   if(handoff){history.replaceState(null,'',location.pathname);await completeHandoff(handoff);return}
   authenticated=await resume();
  }catch(e){clearCookie();authenticated=false;profileReady=false;status.textContent='';error.textContent=e?.message||'Unable to complete sign in.'}
 })();
})();