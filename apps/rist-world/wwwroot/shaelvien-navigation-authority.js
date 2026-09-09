(()=>{
 'use strict';
 const backLabel='← BACK';
 let guardArmed=false;
 let handlingPop=false;
 function isOpen(el){return !!el&&!el.hidden&&getComputedStyle(el).display!=='none';}
 function addStartBack(){
  const overlay=document.querySelector('.rist-start-overlay');
  const panel=overlay?.querySelector('.rist-start-panel');
  const sub=panel?.querySelector('.rist-start-sub');
  if(!isOpen(overlay)||!sub)return;
  let top=sub.querySelector(':scope > .rist-start-topnav');
  if(!top){
   top=document.createElement('div');
   top.className='rist-start-topnav';
   const back=document.createElement('button');
   back.type='button';back.className='rist-start-topback';back.textContent=backLabel;
   back.setAttribute('aria-label','Back to Start menu');
   back.addEventListener('click',()=>{
    const existing=sub.querySelector('[data-start-back]');
    if(existing)existing.click();
    else window.RistStartMenu?.open?.();
   });
   top.appendChild(back);
   sub.prepend(top);
  }
 }
 function normalizeWorkspaceBack(){
  const ribbon=document.querySelector('.alpha-world-ribbon');
  const button=ribbon?.querySelector('button');
  if(!button)return;
  if(button.dataset.shaelvienBack==='1')return;
  button.dataset.shaelvienBack='1';
  button.textContent=backLabel;
  button.setAttribute('aria-label','Back to Shaelvien hub');
 }
 function activeBackControl(){
  const overlay=document.querySelector('.rist-start-overlay');
  const sub=overlay?.querySelector('.rist-start-sub');
  if(isOpen(overlay)&&sub){
   const existing=sub.querySelector('[data-start-back]');
   if(existing)return existing;
  }
  const railBack=document.querySelector('.worldbuilder-studio .world-asset-rail .rail-back');
  if(railBack&&isOpen(railBack))return railBack;
  const ribbon=document.querySelector('.alpha-world-ribbon');
  const workspaceBack=ribbon?.querySelector('button');
  if(workspaceBack&&isOpen(ribbon))return workspaceBack;
  return null;
 }
 function armGuard(){
  if(guardArmed)return;
  try{
   history.replaceState({...history.state,shaelvienBase:true},'',location.href);
   history.pushState({shaelvienGuard:true},'',location.href);
   guardArmed=true;
  }catch{}
 }
 function shouldKeepGuard(){return !!activeBackControl();}
 function bindBrowserBack(){
  if(window.__shaelvienBackBound)return;window.__shaelvienBackBound=true;
  armGuard();
  addEventListener('popstate',()=>{
   if(handlingPop)return;
   guardArmed=false;
   const back=activeBackControl();
   if(!back)return;
   handlingPop=true;
   back.click();
   setTimeout(()=>{
    handlingPop=false;
    if(shouldKeepGuard())armGuard();
   },0);
  });
 }
 const update=()=>{addStartBack();normalizeWorkspaceBack();bindBrowserBack();if(shouldKeepGuard())armGuard();};
 const observer=new MutationObserver(update);
 function start(){observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class']});update();}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.ShaelvienNavigation={refresh:update,armBackGuard:armGuard};
})();
