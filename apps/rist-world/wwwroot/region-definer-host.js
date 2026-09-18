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
        const [regions,worldSource]=await Promise.all([
          dotnet.invokeMethodAsync("GetRegionCatalogForPrototype"),
          dotnet.invokeMethodAsync("GetWorldSourceForPrototype")
        ]);
        post(frame,{type:"world-source",worldSource:worldSource||null});
        post(frame,{type:"catalog",regions:Array.isArray(regions)?regions:[]});
        return;
      }
      if(data.type==="request-claim"){
        const cells=Array.isArray(data.cells)?data.cells.map(Number).filter(Number.isInteger):[];
        const tierIndex=Math.max(0,Math.min(2,Math.trunc(Number(data.tierIndex)||0)));
        const sourceLayerOffsets=Array.isArray(data.sourceLayerOffsets)
          ? data.sourceLayerOffsets.map(Number).filter(value=>Number.isInteger(value)&&value>=0&&value<10)
          : Array.from({length:10},(_,index)=>index);
        const gridShape=String(data.gridShape||"square").toLowerCase()==="hex"?"hex":"square";
        const name=String(data.name||"").trim();
        const result=await dotnet.invokeMethodAsync("SubmitRegionClaimRequestFromPrototypeAsync",name,cells,tierIndex,sourceLayerOffsets,gridShape);
        post(frame,{type:"claim-requested",result});
        return;
      }
      if(data.type==="create-region"){
        const name=String(data.name||"").trim();
        const cells=Array.isArray(data.cells)?data.cells.map(Number).filter(Number.isInteger):[];
        const tierIndex=Math.max(0,Math.min(2,Math.trunc(Number(data.tierIndex)||0)));
        const sourceLayerOffsets=Array.isArray(data.sourceLayerOffsets)
          ? data.sourceLayerOffsets.map(Number).filter(value=>Number.isInteger(value)&&value>=0&&value<10)
          : Array.from({length:10},(_,index)=>index);
        const gridShape=String(data.gridShape||"square").toLowerCase()==="hex"?"hex":"square";
        const region=await dotnet.invokeMethodAsync("CreateRegionFromPrototypeAsync",name,cells,tierIndex,sourceLayerOffsets,gridShape);
        post(frame,{type:"region-created",region});
        return;
      }
      if(data.type==="save-map-region"){
        const requestId=String(data.requestId||"");
        const regionId=String(data.regionId||"").trim();
        const layers=Array.isArray(data.userLayers)?data.userLayers:[];
        const result=await dotnet.invokeMethodAsync("SaveRegionMapLayersFromPrototypeAsync",regionId,layers);
        post(frame,{type:"map-region-saved",requestId,result});
        return;
      }
    }catch(error){
      if(data?.type==="save-map-region"){
        post(frame,{type:"map-region-save-error",requestId:String(data?.requestId||""),message:String(error?.message||error||"Map save failed")});
      }else{
        post(frame,{type:"error",message:String(error?.message||error||"Region operation failed")});
      }
    }
  };
  bridges.set(frame,handler);
  window.addEventListener("message",handler);
  post(frame,{type:"bridge-ready"});
}
