(()=>{
 'use strict';
 const FRAME_HEIGHT=12;
 function sync(){
  const shell=document.querySelector('.release-map-region .map-shell');
  const source=shell?.querySelector('.map>.status');
  const map=shell?.querySelector(':scope>.map');
  if(!shell||!source||!map)return;

  let frame=shell.querySelector(':scope>.map-frame-status');
  if(!frame){
   frame=document.createElement('div');
   frame.className='map-frame-status';
   frame.setAttribute('aria-hidden','true');
   Object.assign(frame.style,{
    position:'absolute',
    top:'0',
    left:'0',
    right:'0',
    boxSizing:'border-box',
    minWidth:'0',
    width:'100%',
    height:`${FRAME_HEIGHT}px`,
    minHeight:`${FRAME_HEIGHT}px`,
    maxHeight:`${FRAME_HEIGHT}px`,
    display:'flex',
    alignItems:'center',
    justifyContent:'center',
    overflow:'hidden',
    whiteSpace:'nowrap',
    textOverflow:'ellipsis',
    paddingTop:'0',
    paddingBottom:'0',
    margin:'0',
    background:'#071015',
    color:'#d7be80',
    font:'800 8px/1 system-ui,-apple-system,sans-serif',
    letterSpacing:'.04em',
    pointerEvents:'none',
    zIndex:'159'
   });
   shell.prepend(frame);
  }

  // Reassert container authority in case older runtime styles are still cached.
  frame.style.height=`${FRAME_HEIGHT}px`;
  frame.style.minHeight=`${FRAME_HEIGHT}px`;
  frame.style.maxHeight=`${FRAME_HEIGHT}px`;
  frame.style.paddingTop='0';
  frame.style.paddingBottom='0';
  frame.style.font='800 8px/1 system-ui,-apple-system,sans-serif';

  if(frame.textContent!==source.textContent)frame.textContent=source.textContent;
  source.style.setProperty('display','none','important');

  const staleCorners=shell.querySelector(':scope>.map-frame-corners');
  if(staleCorners)staleCorners.remove();

  const shellRect=shell.getBoundingClientRect();
  const mapRect=map.getBoundingClientRect();
  const leftFrameWidth=Math.max(0,Math.round(mapRect.left-shellRect.left));
  const rightFrameWidth=Math.max(0,Math.round(shellRect.right-mapRect.right));

  frame.style.paddingLeft=`${leftFrameWidth}px`;
  frame.style.paddingRight=`${rightFrameWidth}px`;
 }

 let attempts=0;
 const quick=setInterval(()=>{
  attempts++;
  sync();
  if(document.querySelector('.map-frame-status')||attempts>=100)clearInterval(quick);
 },100);

 setInterval(sync,1500);
 window.addEventListener('resize',()=>requestAnimationFrame(sync));
 window.addEventListener('orientationchange',()=>setTimeout(sync,150));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();
