window.ristWorld=window.ristWorld||{};

window.ristWorld.exportCurrentWorld=()=>{
  try{
    const key='rist.world.blazor.v6';
    const raw=localStorage.getItem(key);
    if(!raw)return;
    const blob=new Blob([raw],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;
    a.download='rist-world.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),0);
  }catch{}
};

window.ristWorld.importCurrentWorld=()=>{
  try{
    const input=document.createElement('input');
    input.type='file';
    input.accept='application/json,.json';
    input.onchange=async()=>{
      const file=input.files?.[0];
      if(!file)return;
      const raw=await file.text();
      JSON.parse(raw);
      localStorage.setItem('rist.world.blazor.v6',raw);
      location.reload();
    };
    input.click();
  }catch{}
};

window.ristWorld.worldBuilderZFramePoint=(element,clientY)=>{
  if(!element)return 0;
  const rect=element.getBoundingClientRect();
  if(rect.height<=0)return 0;
  const t=Math.max(0,Math.min(1,(clientY-rect.top)/rect.height));
  return 50-(t*100);
};
