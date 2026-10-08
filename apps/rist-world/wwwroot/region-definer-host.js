const bridges=new WeakMap();
const resumeHandlers=new WeakMap();
const REGION_TOOL_SRC="./region-volume-tools.js?v=20261008-mobile-region-repair-1";

function post(frame,message){
  try{frame?.contentWindow?.postMessage({source:"shaelvien-regiondefiner-host",...message},location.origin)}catch{}
}

function suppressLegacyRegionPreview(frame){
  try{
    const doc=frame?.contentDocument;
    const stage=doc?.getElementById("stage");
    if(!doc||!stage)return false;
    stage.classList.remove("region-tier-previewing","region-selection-only");
    delete stage.dataset.regionEntry;
    for(const node of doc.querySelectorAll(".region-tier-preview")){
      node.hidden=true;
      node.style.setProperty("display","none","important");
      node.style.setProperty("pointer-events","none","important");
    }
    return true;
  }catch{return false}
}

function controllerModeLabel(phase){
  switch(String(phase||"").toLowerCase()){
    case "xy":return "BOUNDS";
    case "z":return "Z";
    case "save":return "60°";
    case "saved":
    case "existing":return "REGION";
    default:return "BOUNDS";
  }
}

function normalizeControllerState(raw){
  const state=raw&&typeof raw==="object"?raw:{};
  const phase=String(state.phase||"idle");
  return {
    phase,
    selectedCount:Math.max(0,Math.trunc(Number(state.selectedCount)||0)),
    gridShape:controllerModeLabel(phase),
    tierIndex:Math.max(0,Math.trunc(Number(state.tierIndex)||0)),
    pending:state.pending===true,
    exitRequested:state.exitRequested===true,
    regionId:String(state.regionId||""),
    regionName:String(state.regionName||"")
  };
}

async function ensureRegionTools(frame){
  const doc=frame?.contentDocument,win=frame?.contentWindow;
  if(!doc||!win)return false;
  suppressLegacyRegionPreview(frame);
  const activated=()=>doc.getElementById("stage")?.dataset?.regionVolumeV3==="true"
    && typeof win.ShaelvienPrototype?.enterRegionController==="function";
  if(activated())return true;

  const old=doc.getElementById("region-volume-tools-v3");
  if(old&&!String(old.src||"").includes("20261008-mobile-region-repair-1"))old.remove();
  let script=doc.getElementById("region-volume-tools-v3");
  if(!script){
    script=doc.createElement("script");
    script.id="region-volume-tools-v3";
    script.src=new URL(REGION_TOOL_SRC,win.location.href).href;
    script.async=false;
    (doc.body||doc.documentElement).appendChild(script);
  }

  const started=Date.now();
  while(Date.now()-started<5000){
    suppressLegacyRegionPreview(frame);
    if(activated())return true;
    await new Promise(resolve=>setTimeout(resolve,40));
  }
  return false;
}

async function waitForPrototype(frame,timeoutMs=5000){
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
  suppressLegacyRegionPreview(frame);
  const loaded=await ensureRegionTools(frame);
  if(!loaded)return null;
  const api=frame?.contentWindow?.ShaelvienPrototype,fn=api?.[name];
  if(typeof fn!=="function")return null;
  return await fn(...args);
}

async function readControllerState(frame){
  return normalizeControllerState(await callPrototype(frame,"getRegionControllerState"));
}

async function sendState(frame,dotnet){
  suppressLegacyRegionPreview(frame);
  await ensureRegionTools(frame);
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
  }catch{}
}

async function resumeFrame(frame,dotnet){
  if(document.visibilityState==="hidden")return;
  suppressLegacyRegionPreview(frame);
  const api=await waitForPrototype(frame,1200);
  if(!api){
    try{frame.contentWindow.location.reload()}catch{}
    return;
  }
  await ensureRegionTools(frame);
  try{api.showAllParallax?.()}catch{}
  try{frame.contentWindow.dispatchEvent(new Event("resize"))}catch{}
  await sendState(frame,dotnet);
  await callPrototype(frame,"enterRegionController");
}

export async function refresh(frame,dotnet){await sendState(frame,dotnet)}
export async function enterControllerRegionSelection(frame){
  suppressLegacyRegionPreview(frame);
  const result=await callPrototype(frame,"enterRegionController");
  return result!==false;
}
export async function publishControllerState(frame){
  await callPrototype(frame,"publishRegionControllerState");
  return await readControllerState(frame);
}
export async function getControllerState(frame){return await readControllerState(frame)}
export async function controllerPrimary(frame,name=""){
  await callPrototype(frame,"regionControllerPrimary",String(name||""));
  return await readControllerState(frame);
}
export async function controllerBack(frame){
  await callPrototype(frame,"regionControllerBack");
  return await readControllerState(frame);
}
export async function controllerStep(frame,axis,direction){return (await callPrototype(frame,"regionControllerStep",String(axis||""),Math.sign(Number(direction)||0)))!==false}
export async function controllerSelect(frame){return (await callPrototype(frame,"regionControllerSelect"))!==false}
export async function controllerToggleGrid(frame){
  await callPrototype(frame,"publishRegionControllerState");
  return true;
}
export async function setDepth(frame,tier,layer,scope,spatialNodeId="",spatialPath=""){return (await callPrototype(frame,"setExternalDepth",{tier,layer,scope,spatialNodeId,spatialPath}))!==false}
export async function placeAsset(frame,payload){return (await callPrototype(frame,"placeExternalAsset",payload||{}))!==false}
export async function editCommand(frame,command){const result=await callPrototype(frame,"editCommand",String(command||"").toLowerCase());return typeof result==="string"?result:""}
export async function showAllParallax(frame){return (await callPrototype(frame,"showAllParallax"))!==false}

export function detach(frame){
  const existing=bridges.get(frame);
  if(existing){window.removeEventListener("message",existing);bridges.delete(frame)}
  const resume=resumeHandlers.get(frame);
  if(resume){
    window.removeEventListener("pageshow",resume);
    document.removeEventListener("visibilitychange",resume);
    frame?.removeEventListener?.("load",resume);
    resumeHandlers.delete(frame);
  }
}

export async function attach(frame,dotnet){
  detach(frame);
  const initial=await waitForPrototype(frame);
  if(initial)await ensureRegionTools(frame);
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
        suppressLegacyRegionPreview(frame);
        await sendState(frame,dotnet);
        return;
      }
      if(data.type==="controller-state"){
        const state=normalizeControllerState(data.state);
        await dotnet.invokeMethodAsync("ReceiveControllerStateAsync",state.phase,state.selectedCount,state.gridShape,state.tierIndex,state.pending,state.exitRequested,state.regionId,state.regionName);
        return;
      }
      if(data.type==="request-claim"){
        const cells=Array.isArray(data.cells)?data.cells.map(Number).filter(Number.isInteger):[];
        const tierIndex=Math.max(0,Math.trunc(Number(data.tierIndex)||0));
        const sourceLayerOffsets=Array.isArray(data.sourceLayerOffsets)
          ? data.sourceLayerOffsets.map(Number).filter(value=>Number.isInteger(value)&&value>=0&&value<100)
          : Array.from({length:10},(_,index)=>index);
        const gridShape="square";
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
          region=await dotnet.invokeMethodAsync("CreateRegionFromPrototypeAsync",name,cells,tierIndex,sourceLayerOffsets,"square");
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

  let resumePending=false;
  const resume=()=>{
    if(resumePending||document.visibilityState==="hidden")return;
    resumePending=true;
    setTimeout(async()=>{try{await resumeFrame(frame,dotnet)}finally{resumePending=false}},80);
  };
  resumeHandlers.set(frame,resume);
  window.addEventListener("pageshow",resume);
  document.addEventListener("visibilitychange",resume);
  frame?.addEventListener?.("load",resume);

  suppressLegacyRegionPreview(frame);
  post(frame,{type:"bridge-ready"});
}