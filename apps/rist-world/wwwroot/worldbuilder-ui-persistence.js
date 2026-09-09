(()=>{
 const key='rist.worldbuilder.rails.v1';
 const read=()=>{try{return JSON.parse(localStorage.getItem(key)||'{}')}catch{return {}}};
 const write=value=>{try{localStorage.setItem(key,JSON.stringify(value))}catch{}};
 const find=()=>({top:document.querySelector('.worldbuilder-studio .studio-top-slider'),bottom:document.querySelector('.worldbuilder-studio .studio-command-rail')});
 window.ristWorldBuilderUi={
  captureRails(){
   const {top,bottom}=find();
   const current=read();
   if(top)current.top=top.scrollLeft;
   if(bottom)current.bottom=bottom.scrollLeft;
   write(current);
  },
  restoreRails(){
   const state=read();
   requestAnimationFrame(()=>{
    const {top,bottom}=find();
    if(top&&Number.isFinite(state.top))top.scrollLeft=state.top;
    if(bottom&&Number.isFinite(state.bottom))bottom.scrollLeft=state.bottom;
   });
  }
 };
 document.addEventListener('scroll',e=>{
  if(e.target?.matches?.('.worldbuilder-studio .studio-top-slider,.worldbuilder-studio .studio-command-rail'))window.ristWorldBuilderUi.captureRails();
 },true);
 window.addEventListener('pagehide',()=>window.ristWorldBuilderUi.captureRails());
})();
