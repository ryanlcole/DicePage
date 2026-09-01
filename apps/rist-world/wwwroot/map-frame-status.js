(()=>{
 'use strict';
 function sync(){
  const shell=document.querySelector('.release-map-region .map-shell');
  const source=shell?.querySelector('.map>.status');
  if(!shell||!source)return;
  let frame=shell.querySelector(':scope>.map-frame-status');
  if(!frame){
   frame=document.createElement('div');
   frame.className='map-frame-status';
   frame.setAttribute('aria-hidden','true');
   Object.assign(frame.style,{
    boxSizing:'border-box',
    gridColumn:'1',
    gridRow:'1',
    minWidth:'0',
    width:'100%',
    height:'100%',
    display:'flex',
    alignItems:'center',
    justifyContent:'center',
    padding:'0 42px',
    overflow:'hidden',
    whiteSpace:'nowrap',
    textOverflow:'ellipsis',
    background:'#071015',
    color:'#d7be80',
    font:'800 10px/1.2 system-ui,-apple-system,sans-serif',
    letterSpacing:'.05em',
    pointerEvents:'none'
   });
   shell.prepend(frame);
  }
  if(frame.textContent!==source.textContent)frame.textContent=source.textContent;
  source.style.setProperty('display','none','important');

  if(!shell.querySelector(':scope>.map-frame-corners')){
   const corners=document.createElement('div');
   corners.className='map-frame-corners';
   corners.setAttribute('aria-hidden','true');
   Object.assign(corners.style,{
    position:'absolute',
    inset:'0',
    zIndex:'160',
    pointerEvents:'none'
   });
   for(const pos of ['top-left','top-right','bottom-left','bottom-right']){
    const corner=document.createElement('span');
    corner.dataset.corner=pos;
    Object.assign(corner.style,{
     position:'absolute',
     width:'42px',
     height:'42px',
     background:'#071015'
    });
    if(pos.includes('top'))corner.style.top='0';else corner.style.bottom='0';
    if(pos.includes('left'))corner.style.left='0';else corner.style.right='0';
    corners.appendChild(corner);
   }
   shell.appendChild(corners);
  }
 }
 let attempts=0;
 const quick=setInterval(()=>{attempts++;sync();if(document.querySelector('.map-frame-status')||attempts>=100)clearInterval(quick)},100);
 setInterval(sync,1500);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();
