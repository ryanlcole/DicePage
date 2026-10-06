const bridges=new WeakMap();
const GEOMETRY_TOOL_SRC="/Game/prototype/region-geometry-tools.js?v=20261006-region-border-1";

function post(frame,message){
  try{frame?.contentWindow?.postMessage({source:"shaelvien-regiondefiner-host",...message},location.origin)}catch{}
}

async function ensureRegionGeometryTools(frame){
  const doc=frame?.contentDocument;
  if(!doc)return false;
  if(doc.getElementById("region-geometry-tools-v2"))return true;
  return await new Promise(resolve=>{
    const script=doc.createElement("script");
    script.id="region-geometry-tools-v2";
    script.src=GEOMETRY_TOOL_SRC;
    script.async=false;
    script.onload=()=>resolve(true);
    script.onerror=()=>resolve(false);
    (doc.body||doc.documentElement).appendChild(script);
  });
}

async function waitForPrototype(frame,timeoutMs=3000){
  const started=Date.now();
  while(Date.now()-started<timeoutMs){
    const api=frame?.contentWindow?.ShaelvienPrototype;
    if(api)return api;
    await new Promise(resolve=>setTimeout(resolve,50));
  }
  return null;
}
async function callPrototype(frame,name,...args){
  const initial=await waitForPrototype(frame);
  if(!initial)return null;
  const loaded=await ensureRegionGeometryTools(frame);
  if(!loaded)return null;
  const api=frame?.contentWindow?.ShaelvienPrototype,fn=api?.[name];
  if(typeof fn!=="function")return null;
  return await fn(...args);
}
async function sendState(frame,dotnet){
  await ensureRegionGeometryTools(frame);
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
  try{
    const regions=await dotnet.invokeMethodAsync("GetRegionGeometryCatalogForPrototype");
    post(frame,{type:"catalog-v2",regions:Array.isArray(regions)?regions:[]});
  }catch{
    // Geometry-v2 is additive. Older cached clients continue on the legacy catalog.
  }
}

export async function refresh(frame,dotnet){await sendState(frame,dotnet)}
export async function enterControllerRegionSelection(frame){return (await callPrototype(frame,"enterRegionController"))!==false}
export async function publishControllerState(frame){return await callPrototype(frame,"publishRegionControllerState")}
export async function getControllerState(frame){return await callPrototype(frame,"getRegionControllerState")}
export async function controllerPrimary(frame,name=""){return await callPrototype(frame,"regionControllerPrimary",String(name||""))}
export async function controllerBack(frame){return await callPrototype(frame,"regionControllerBack")}
export async function controllerStep(frame,axis,direction){return (await callPrototype(frame,"regionControllerStep",String(axis||""),Math.sign(Number(direction)||0)))!==false}
export async function controllerSelect(frame){return (await callPrototype(frame,"regionControllerSelect"))!==false}
export async function controllerToggleGrid(frame){return (await callPrototype(frame,"regionControllerToggleGrid"))!==false}
export async function setDepth(frame,tier,layer,scope,spatialNodeId="",spatialPath=""){return (await callPrototype(frame,"setExternalDepth",{tier,layer,scope,spatialNodeId,spatialPath}))!==false}
export async function placeAsset(frame,payload){return (await callPrototype(frame,"placeExternalAsset",payload||{}))!==false}
export async function editCommand(frame,command){const result=await callPrototype(frame,"editCommand",String(command||"").toLowerCase());return typeof result==="string"?result:""}
export async function showAllParallax(frame){return (await callPrototype(frame,"showAllParallax"))!==false}

export function detach(frame){
  const existing=bridges.get(frame);
  if(!existing)return;
  window.removeEventListener("message",existing);
  bridges.delete(frame);
}

export async function attach(frame,dotnet){
  detach(frame);
  const initial=await waitForPrototype(frame);
  if(initial)await ensureRegionGeometryTools(frame);
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
      if(data.type==="controller-state"){
        const state=data.state&&typeof data.state==="object"?data.state:{};
        await dotnet.invokeMethodAsync("ReceiveControllerStateAsync",String(state.phase||"idle"),Math.max(0,Math.trunc(Number(state.selectedCount)||0)),String(state.gridShape||"none"),Math.max(0,Math.trunc(Number(state.tierIndex)||0)),state.pending===true,state.exitRequested===true,String(state.regionId||""),String(state.regionName||""));
        return;
      }
      if(data.type==="request-claim"){
        const cells=Array.isArray(data.cells)?data.cells.map(Number).filter(Number.isInteger):[];
        const tierIndex=Math.max(0,Math.trunc(Number(data.tierIndex)||0));
        const sourceLayerOffsets=Array.isArray(data.sourceLayerOffsets)
          ? data.sourceLayerOffsets.map(Number).filter(value=>Number.isInteger(value)&&value>=0&&value<100)
          : Array.from({length:10},(_,index)=>index);
        const gridShape=String(data.gridShape||"square").toLowerCase()==="hex"?"hex":"square";
        const name=String(data.name||"").trim();
        const result=await dotnet.invokeMethodAsync("SubmitRegionClaimRequestFromPrototypeAsync",name,cells,tierIndex,sourceLayerOffsets,gridShape);
        post(frame,{type:"claim-requested",result});
        return;
      }
      if(data.type==="create-region"){
        let region;
        if(Math.trunc(Number(data.version)||0)>=2){
          region=await dotnet.invokeMethodAsync("CreateRegionGeometryFromPrototypeAsync",data);
        }else{
          const name=String(data.name||"").trim();
          const cells=Array.isArray(data.cells)?data.cells.map(Number).filter(Number.isInteger):[];
          const tierIndex=Math.max(0,Math.trunc(Number(data.tierIndex)||0));
          const sourceLayerOffsets=Array.isArray(data.sourceLayerOffsets)
            ? data.sourceLayerOffsets.map(Number).filter(value=>Number.isInteger(value)&&value>=0&&value<10)
            : Array.from({length:10},(_,index)=>index);
          const gridShape=String(data.gridShape||"square").toLowerCase()==="hex"?"hex":"square";
          region=await dotnet.invokeMethodAsync("CreateRegionFromPrototypeAsync",name,cells,tierIndex,sourceLayerOffsets,gridShape);
        }
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
