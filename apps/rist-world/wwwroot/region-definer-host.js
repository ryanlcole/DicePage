const bridges=new WeakMap();

function post(frame,message){
  try{frame?.contentWindow?.postMessage({source:"shaelvien-regiondefiner-host",...message},location.origin)}catch{}
}

async function sendState(frame,dotnet){
  try{
    const worldSource=await dotnet.invokeMethodAsync("GetWorldSourceForPrototype");
    post(frame,{type:"world-source",worldSource:worldSource||null});
  }catch(error){
    post(frame,{type:"map-load-error",message:String(error?.message||error||"Canonical map database is unavailable")});
  }
  try{
    const regions=await dotnet.invokeMethodAsync("GetRegionCatalogForPrototype");
    post(frame,{type:"catalog",regions:Array.isArray(regions)?regions:[]});
  }catch(error){
    post(frame,{type:"catalog-error",message:String(error?.message||error||"Region permissions are unavailable")});
  }
}

export async function refresh(frame,dotnet){
  await sendState(frame,dotnet);
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
      if(data.type==="home"){
        await dotnet.invokeMethodAsync("RequestHomeFromPrototypeAsync");
        return;
      }
      if(data.type==="ready"){
        await sendState(frame,dotnet);
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
        // Switch from parent-world preview to the server-projected child source.
        const regionSource=await dotnet.invokeMethodAsync("GetRegionSourceForPrototypeAsync",String(region?.id||""));
        post(frame,{type:"world-source",worldSource:regionSource});
        return;
      }
      if(data.type==="save-map-region"){
        const requestId=String(data.requestId||"");
        const regionId=String(data.regionId||"").trim();
        const layers=Array.isArray(data.userLayers)?data.userLayers:[];
        const relativeTiers=Array.isArray(data.relativeTiers)?data.relativeTiers:[{id:regionId+":tier:0",index:0,label:"Region Base"}];
        const result=await dotnet.invokeMethodAsync("SaveRegionMapLayersFromPrototypeAsync",regionId,layers,relativeTiers);
        post(frame,{type:"map-region-saved",requestId,result});
        return;
      }
      if(data.type==="promote-world-source"){
        const state=data.state&&typeof data.state==="object"?data.state:{};
        const result=await dotnet.invokeMethodAsync("PromoteWorldSourceFromPrototypeAsync",state);
        if(result?.success){
          const worldSource=await dotnet.invokeMethodAsync("GetWorldSourceForPrototype");
          post(frame,{type:"world-source",worldSource:worldSource||null});
        }else{
          post(frame,{type:"map-load-error",message:"Canonical World Builder source could not be promoted to the database."});
        }
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
