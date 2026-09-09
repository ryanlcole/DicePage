(()=>{
 let bypass=false;
 let initialized=false;
 const guardKey='ristBrowserBackGuard';

 const visible=el=>!!el&&el.getClientRects().length>0;
 const activeBackTarget=()=>{
  const libraryBack=document.querySelector('.world-asset-rail .rail-back');
  if(visible(libraryBack))return libraryBack;

  const workspaceBack=document.querySelector('.alpha-world-ribbon button[aria-label="Back to Shaelvien hub"]');
  if(visible(workspaceBack))return workspaceBack;

  const worldBuilderHome=document.querySelector('.worldbuilder-studio .studio-home');
  if(visible(worldBuilderHome))return worldBuilderHome;

  return null;
 };

 const arm=()=>{
  const state=history.state||{};
  if(state&&state[guardKey])return;
  history.pushState({...state,[guardKey]:true},'',location.href);
 };

 const onPopState=()=>{
  if(bypass){bypass=false;return;}
  const target=activeBackTarget();
  if(target){
   target.click();
   setTimeout(arm,0);
   return;
  }
  bypass=true;
  history.back();
 };

 const init=()=>{
  if(initialized)return;
  initialized=true;
  arm();
  window.addEventListener('popstate',onPopState);
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
 else init();
})();
