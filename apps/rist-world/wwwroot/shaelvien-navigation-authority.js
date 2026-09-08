(()=>{
 'use strict';
 const backLabel='← BACK';
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
 function bindBrowserBack(){
  if(window.__shaelvienBackBound)return;window.__shaelvienBackBound=true;
  addEventListener('popstate',()=>{
   const overlay=document.querySelector('.rist-start-overlay');
   const sub=overlay?.querySelector('.rist-start-sub');
   if(isOpen(overlay)&&sub){
    const existing=sub.querySelector('[data-start-back]');
    if(existing){existing.click();return;}
   }
  });
 }
 const update=()=>{addStartBack();normalizeWorkspaceBack();bindBrowserBack();};
 const observer=new MutationObserver(update);
 function start(){observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class']});update();}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.ShaelvienNavigation={refresh:update};
})();
