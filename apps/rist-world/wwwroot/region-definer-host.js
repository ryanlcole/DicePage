const bridges=new WeakMap();
const stateRevisions=new WeakMap();

function beginStateRequest(frame){
  const revision=(stateRevisions.get(frame)||0)+1;
  stateRevisions.set(frame,revision);
  return revision;
}
function isCurrentStateRequest(frame,revision){
  return stateRevisions.get(frame)===revision;
}

function post(frame,message){
  try{frame?.contentWindow?.postMessage({source:"shaelvien-regiondefiner-host",...message},location.origin)}catch{}
}

async function sendState(frame,dotnet){
  const revision=beginStateRequest(frame);
  try{
    // Existing claims always request their exact source subset. No unfiltered
    // world image leaves the parent bridge while permissions are refreshing.
    const regionId=new URL(frame.getAttribute("src"),location.origin).searchParams.get("regionId")||"";
    const worldSource=regionId
      ?await dotnet.invokeMethodAsync("GetRegionSourceForPrototypeAsync",regionId)
      :await dotnet.invokeMethodAsync("GetWorldSourceForPrototype");
    if(!isCurrentStateRequest(frame,revision))return;
    post(frame,{type:"world-source",worldSource:worldSource||null});
  }catch(error){
    if(!isCurrentStateRequest(frame,revision))return;
    post(frame,{type:"map-load-error",message:String(error?.message||error||"Canonical map database is unavailable")});
  }
  try{
    const regions=await dotnet.invokeMethodAsync("GetRegionCatalogForPrototype");
    if(!isCurrentStateRequest(frame,revision))return;
    post(frame,{type:"catalog",regions:Array.isArray(regions)?regions:[]});
  }catch(error){
    if(!isCurrentStateRequest(frame,revision))return;
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
  stateRevisions.delete(frame);
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
        // The deed and its projected child source are handed back together so
        // the claim screen becomes the editor immediately instead of requiring
        // the user to leave and reopen RegionDefiner.
        let regionSource=null;
        try{
          regionSource=await dotnet.invokeMethodAsync("GetRegionSourceForPrototypeAsync",String(region?.id||""));
        }catch{}
        post(frame,{type:"region-created",region,worldSource:regionSource});
        if(!regionSource)post(frame,{type:"map-load-error",message:"The deed was saved, but its regional source could not be loaded yet."});
        return;
      }
      if(data.type==="save-map-region"){
        const requestId=String(data.requestId||"");
        const regionId=String(data.regionId||"").trim();
        const layers=Array.isArray(data.userLayers)?data.userLayers:[];
        const result=await dotnet.invokeMethodAsync("SaveRegionMapLayersFromPrototypeAsync",regionId,layers);
        let verified=false,persistedIds=[];
        if(result?.success){
          try{
            const readback=await dotnet.invokeMethodAsync("GetRegionSourceForPrototypeAsync",regionId);
            const state=readback?.state&&typeof readback.state==="object"?readback.state:{};
            const saved=Array.isArray(state.userLayers)?state.userLayers:[];
            persistedIds=saved
              .filter(item=>String(item?.regionId||"")===regionId)
              .map(item=>String(item?.id||""))
              .filter(Boolean);
            const wanted=layers.map(item=>String(item?.id||"")).filter(Boolean);
            const persisted=new Set(persistedIds);
            verified=wanted.every(id=>persisted.has(id));
          }catch{}
        }
        post(frame,{type:"map-region-saved",requestId,result,verified,persistedIds});
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
