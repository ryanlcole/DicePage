(()=>{
 'use strict';
 const selector='button,[role="button"],label,a,.rist-bottom-folder-card,.rist-bottom-asset-card,.rist-folder-fixed';
 let active=null,clearTimer=0,lastDieTouch=0;
 const clear=()=>{if(clearTimer){clearTimeout(clearTimer);clearTimer=0}if(active){active.classList.remove('rist-touch-active');active=null}};
 function ensureLiveRegion(){let live=document.getElementById('rist-die-touch-result');if(live)return live;live=document.createElement('div');live.id='rist-die-touch-result';live.setAttribute('aria-live','assertive');live.setAttribute('aria-atomic','true');live.style.cssText='position:fixed;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;';document.body.appendChild(live);return live}
 function dieValue(die){const title=String(die?.getAttribute('title')||'');if(/rolling/i.test(title))return null;const matches=title.match(/-?\d+/g);if(!matches?.length)return null;const value=Number(matches[matches.length-1]);return Number.isFinite(value)?value:null}
 function numberPattern(value){const pattern=[];const magnitude=Math.abs(Math.trunc(value));if(value<0)pattern.push(110,55,110,150);const tens=Math.floor(magnitude/10),ones=magnitude%10;for(let i=0;i<tens;i++){pattern.push(180);if(i<tens-1||ones)pattern.push(95)}for(let i=0;i<ones;i++){pattern.push(45);if(i<ones-1)pattern.push(55)}if(magnitude===0)pattern.push(260);return pattern}
 function tactileDie(die){const value=dieValue(die);if(value===null)return;const now=Date.now();if(now-lastDieTouch<180)return;lastDieTouch=now;try{if(typeof navigator.vibrate==='function')navigator.vibrate(numberPattern(value))}catch{}const live=ensureLiveRegion();live.textContent='';requestAnimationFrame(()=>{live.textContent=`Die result ${value}`});die.setAttribute('aria-label',`Die result ${value}`);document.dispatchEvent(new CustomEvent('rist:die-tactile-result',{detail:{value}}))}
 document.addEventListener('pointerdown',event=>{
  if(event.pointerType&&event.pointerType!=='touch'&&event.pointerType!=='pen')return;
  const source=event.target instanceof Element?event.target:null;
  const die=source?.closest('.rolled-die');
  if(die){tactileDie(die);return}
  const target=source?.closest(selector)||null;
  if(!target||target.matches(':disabled,[aria-disabled="true"]'))return;
  clear();active=target;target.classList.add('rist-touch-active');
 },{capture:true,passive:true});
 for(const type of ['pointerup','pointercancel','lostpointercapture'])document.addEventListener(type,()=>{clearTimer=setTimeout(clear,90)},{capture:true,passive:true});
 document.addEventListener('click',()=>{clearTimer=setTimeout(clear,110)},{capture:true,passive:true});
})();
