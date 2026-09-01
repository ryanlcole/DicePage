(()=>{
 const KEY='rist.asset.scope';
 let scope=sessionStorage.getItem(KEY)==='private'?'private':'public';

 function apply(next){
  scope=next==='private'?'private':'public';
  sessionStorage.setItem(KEY,scope);
  const root=document.querySelector('.rist.release-world');
  if(root)root.dataset.assetScope=scope;
  document.querySelectorAll('.asset-scope-toggle button').forEach(button=>{
   const active=button.dataset.scope===scope;
   button.classList.toggle('active',active);
   button.setAttribute('aria-pressed',active?'true':'false');
  });
 }

 function makeToggle(){
  const nav=document.createElement('nav');
  nav.className='asset-scope-toggle';
  nav.setAttribute('aria-label','Asset visibility');
  for(const [key,label] of [['public','Public'],['private','Private']]){
   const button=document.createElement('button');
   button.type='button';
   button.dataset.scope=key;
   button.textContent=label;
   button.addEventListener('click',()=>apply(key));
   nav.appendChild(button);
  }
  return nav;
 }

 function install(){
  const root=document.querySelector('.rist.release-world');
  if(!root)return false;
  root.dataset.assetScope=scope;
  document.querySelectorAll('.release-public-region .asset-rail-header,.release-private-region .asset-rail-header').forEach(header=>{
   if(!header.querySelector('.asset-scope-toggle'))header.prepend(makeToggle());
  });
  apply(scope);
  return true;
 }

 window.RistAssetScope={
  set:apply,
  toggle:()=>apply(scope==='public'?'private':'public'),
  get:()=>scope
 };

 let attempts=0;
 const quick=setInterval(()=>{
  attempts++;
  if(install()||attempts>=100)clearInterval(quick);
 },100);
 // Blazor can replace a header while changing asset filters. This slow, idempotent
 // check restores the switch without observing or reacting to every DOM mutation.
 setInterval(install,1500);
})();