const bridges=new WeakMap();

function post(frame,message){
  try{frame?.contentWindow?.postMessage({source:"shaelvien-regiondefiner-host",...message},location.origin)}catch{}
}

export function detach(frame){
  const existing=bridges.get(frame);
  if(!existing)return;
  window.removeEventListener("message",existing);
  bridges.delete(frame);
}

export function attach(frame,dotnet){
  detach(frame);
  const handler=async event=>{
    if(event.origin!==location.origin||event.source!==frame?.contentWindow)return;
    const data=event.data;
    if(!data||data.source!=="shaelvien-regiondefiner")return;
    try{
      if(data.type==="ready"){
        const regions=await dotnet.invokeMethodAsync("GetRegionCatalogForPrototype");
        post(frame,{type:"catalog",regions:Array.isArray(regions)?regions:[]});
        return;
      }
      if(data.type==="create-region"){
        const name=String(data.name||"").trim();
        const cells=Array.isArray(data.cells)?data.cells.map(Number).filter(Number.isInteger):[];
        const tierIndex=Math.max(0,Math.min(2,Math.trunc(Number(data.tierIndex)||0)));
        const region=await dotnet.invokeMethodAsync("CreateRegionFromPrototypeAsync",name,cells,tierIndex);
        post(frame,{type:"region-created",region});
      }
    }catch(error){
      post(frame,{type:"error",message:String(error?.message||error||"Region operation failed")});
    }
  };
  bridges.set(frame,handler);
  window.addEventListener("message",handler);
  post(frame,{type:"bridge-ready"});
}
