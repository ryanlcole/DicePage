(()=>{
 'use strict';
 const $=id=>document.getElementById(id);
 const game='/Game/index.html';
 const cookieName='rist_session';
 const authIntentKey='rist.auth.intent';
 const profileKey='account/profile.json';
 const status=$('status'),entry=$('entry'),profileWrap=$('profile-wrap'),profileForm=$('profile'),profileError=$('profile-error');
 let api='',sessionToken='',authProfile=null,launching=false;

 const setStatus=message=>{status.textContent=message||''};
 const setCookie=token=>{document.cookie=`${cookieName}=${encodeURIComponent(token)}; Path=/; Max-Age=28800; Secure; SameSite=Lax`;};
 const clearCookie=()=>{
  document.cookie=`${cookieName}=; Path=/; Max-Age=0; Secure; SameSite=Lax`;
  document.cookie=`${cookieName}=; Path=/Game/; Max-Age=0; Secure; SameSite=Lax`;
 };
 async function config(){
  if(api)return api;
  const r=await fetch('./auth-config.json',{cache:'no-store'});
  if(!r.ok)throw new Error('Account service configuration is unavailable.');
  const c=await r.json();api=(c.apiBaseUrl||'').replace(/\/$/,'');
  if(!api)throw new Error('Account service configuration is incomplete.');
  return api;
 }
 async function apiFetch(path,options={}){
  const base=await config();
  const headers=new Headers(options.headers||{});
  if(sessionToken)headers.set('Authorization','Bearer '+sessionToken);
  return fetch(base+path,{...options,headers,cache:'no-store'});
 }
 async function verify(){
  if(!sessionToken)return false;
  const r=await apiFetch('/me');
  if(!r.ok)return false;
  authProfile=await r.json();
  return true;
 }
 async function loadProfile(){
  const r=await apiFetch('/storage/download?key='+encodeURIComponent(profileKey));
  if(r.status===404)return null;
  if(!r.ok)throw new Error('Your RIST profile could not be checked.');
  const p=await r.json();
  if(!p?.url)return null;
  const file=await fetch(p.url,{cache:'no-store'});
  if(file.status===404)return null;
  if(!file.ok)throw new Error('Your RIST profile could not be checked.');
  return file.json();
 }
 async function saveProfile(alias,plan){
  const created={
   AccountId:crypto.randomUUID(),
   PlayerAlias:alias,
   Plan:plan,
   CreatedAtUtc:new Date().toISOString(),
   TermsAcceptedAtUtc:new Date().toISOString(),
   TermsVersion:'2026-08-30',
   ContentAccess:null
  };
  const prep=await apiFetch('/storage/upload',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:profileKey,contentType:'application/json'})});
  if(!prep.ok)throw new Error('Your RIST profile could not be created. Please try again.');
  const post=await prep.json();
  if(!post?.url||!post?.fields)throw new Error('Your RIST profile could not be created. Please try again.');
  const form=new FormData();
  Object.entries(post.fields).forEach(([key,value])=>form.append(key,value));
  form.append('file',new Blob([JSON.stringify(created)],{type:'application/json'}),'profile.json');
  const upload=await fetch(post.url,{method:'POST',body:form});
  if(!upload.ok)throw new Error('Your RIST profile could not be created. Please try again.');
  return created;
 }
 function enterGame(profileSetup=false){
  if(launching)return;
  launching=true;
  setCookie(sessionToken);
  sessionStorage.setItem('rist.session',sessionToken);
  sessionStorage.setItem('rist.lastActivity',String(Date.now()));
  sessionStorage.setItem('rist.launch.intent','load');
  sessionStorage.setItem('rist.launch.settings',JSON.stringify({role:'Roleplayer',domain:'Shaelvien MMO'}));
  if(profileSetup)sessionStorage.setItem('rist.profile.just-created','1');
  localStorage.removeItem(authIntentKey);
  setStatus('Entering Shaelvien…');
  location.assign(game);
 }
 function openProfile(){
  entry.hidden=true;profileWrap.hidden=false;setStatus('');
  const fallback=(authProfile?.displayName||authProfile?.DisplayName||'').trim().slice(0,32);
  $('alias').value=fallback;
  requestAnimationFrame(()=>$('alias').focus({preventScroll:true}));
 }
 function returnExistingSignupToLogin(){
  clearCookie();
  sessionStorage.removeItem('rist.session');
  sessionStorage.removeItem('rist.lastActivity');
  sessionStorage.removeItem(authIntentKey);
  localStorage.removeItem(authIntentKey);
  sessionToken='';
  authProfile=null;
  entry.hidden=false;
  profileWrap.hidden=true;
  setStatus('You already have a RIST account. Please Log In.');
  requestAnimationFrame(()=>$('login')?.focus({preventScroll:true}));
 }
 async function begin(intent){
  try{
   setStatus(intent==='signup'?'Opening secure sign up…':'Opening secure login…');
   sessionStorage.setItem(authIntentKey,intent);
   localStorage.setItem(authIntentKey,intent);
   const base=await config();
   location.assign(base+'/auth/login');
  }catch(e){setStatus(e?.message||'Unable to start authentication.');}
 }
 async function completeHandoff(handoff){
  const intent=sessionStorage.getItem(authIntentKey)||localStorage.getItem(authIntentKey)||'login';
  setStatus('Completing secure sign in…');
  const base=await config();
  const r=await fetch(base+'/auth/session?handoff='+encodeURIComponent(handoff),{cache:'no-store'});
  if(!r.ok)throw new Error('The sign-in handoff expired. Please try again.');
  const p=await r.json();
  if(!p.sessionToken)throw new Error('The account service returned an invalid session.');
  sessionToken=p.sessionToken;
  sessionStorage.setItem('rist.session',sessionToken);
  sessionStorage.setItem('rist.lastActivity',String(Date.now()));
  setCookie(sessionToken);
  if(!(await verify()))throw new Error('Your authenticated session could not be verified.');
  const existing=await loadProfile();
  if(intent==='signup'){
   if(existing){returnExistingSignupToLogin();return;}
   openProfile();
   return;
  }
  if(!existing){
   throw new Error('No RIST profile is connected to this Discord account. Choose Sign Up.');
  }
  enterGame(false);
 }
 async function resume(){
  const token=sessionStorage.getItem('rist.session');
  if(!token)return;
  sessionToken=token;
  try{
   if(await verify()){
    const existing=await loadProfile();
    if(existing){enterGame(false);return;}
   }
  }catch{}
  sessionStorage.removeItem('rist.session');
  sessionStorage.removeItem('rist.lastActivity');
  clearCookie();
  sessionToken='';
 }

 $('login').addEventListener('click',()=>void begin('login'));
 $('signup').addEventListener('click',()=>void begin('signup'));
 profileForm.addEventListener('submit',async e=>{
  e.preventDefault();profileError.textContent='';
  const alias=$('alias').value.trim();
  const plan=$('plan').value==='gm-player'?'gm-player':'player';
  if(alias.length<1||alias.length>32){profileError.textContent='Enter a player alias from 1 to 32 characters.';return;}
  if(!$('terms').checked){profileError.textContent='Accept the Terms and Privacy Policy to create the profile.';return;}
  const save=$('profile-save');save.disabled=true;save.textContent='Saving…';
  try{
   const existing=await loadProfile();
   if(!existing)await saveProfile(alias,plan);
   enterGame(true);
  }catch(err){profileError.textContent=err?.message||'Your profile could not be saved.';save.disabled=false;save.textContent='Save Profile & Enter Game';}
 });

 (async()=>{
  try{
   const q=new URLSearchParams(location.search),handoff=q.get('rist_handoff');
   if(handoff){history.replaceState(null,'',location.pathname);await completeHandoff(handoff);return;}
   await resume();
  }catch(e){
   clearCookie();sessionStorage.removeItem('rist.session');sessionStorage.removeItem('rist.lastActivity');
   sessionToken='';entry.hidden=false;profileWrap.hidden=true;setStatus(e?.message||'Authentication could not be completed.');
  }
 })();
})();
