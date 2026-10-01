const bridges=new WeakMap();

function post(frame,message){
  try{frame?.contentWindow?.postMessage({source:"shaelvien-worldbuilder-host",...message},location.origin)}catch{}
}

function currentFrameContext(frame){
  try{
    const raw=frame?.getAttribute?.("src")||frame?.src||"";
    const url=new URL(raw,location.href);
    return{
      worldId:String(url.searchParams.get("worldId")||""),
      deedId:String(url.searchParams.get("deedId")||""),
      deedRegionId:String(url.searchParams.get("deedRegionId")||""),
      deedZoneId:String(url.searchParams.get("deedZone")||""),
      seed:String(url.searchParams.get("seed")||"")
    };
  }catch{
    return{worldId:"",deedId:"",deedRegionId:"",deedZoneId:"",seed:""};
  }
}

function messageMatchesCurrentFrame(frame,data){
  const current=currentFrameContext(frame);
  const fields=["worldId","deedId","deedRegionId","deedZoneId","seed"];
  for(const field of fields){
    const expected=String(current[field]||"");
    const actual=String(data?.[field]||"");
    // When the current iframe is deed-scoped, an older script that emits no
    // identity is stale by definition and must not control parent navigation.
    if(expected&&actual!==expected)return false;
    if(!expected&&actual)return false;
  }
  return true;
}

export async function save(frame){
  const fn=frame?.contentWindow?.ShaelvienPrototype?.save;
  if(typeof fn!=="function")return false;
  return (await fn())!==false;
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

export async function placeAsset(frame,payload){
  // Re-announce the host before every canonical commit. If attach() happened
  // before the iframe finished booting, its first bridge-ready message could
  // have been missed and saves would otherwise appear to do nothing.
  post(frame,{type:"bridge-ready"});
  const api=await waitForPrototype(frame);
  if(!api)return false;

  // Give the child one event turn to accept bridge-ready before its save path
  // checks worldSourceHostReady.
  await new Promise(resolve=>setTimeout(resolve,50));
  const fn=api.placeExternalAsset;
  if(typeof fn!=="function")return false;
  return (await fn(payload||{}))!==false;
}

export async function editCommand(frame,command){
  post(frame,{type:"bridge-ready"});
  const api=await waitForPrototype(frame);
  if(!api)return "Viewer editing tools are still loading.";
  await new Promise(resolve=>setTimeout(resolve,50));
  const fn=api.editCommand;
  if(typeof fn!=="function")return "This viewer does not support editing commands yet.";
  const result=await fn(String(command||"").toLowerCase());
  return typeof result==="string"?result:"";
}

export async function showAllParallax(frame){
  post(frame,{type:"bridge-ready"});
  const api=await waitForPrototype(frame);
  if(!api)return false;
  const fn=api.showAllParallax;
  if(typeof fn!=="function")return false;
  return fn()!==false;
}

export function setDepth(frame,tier,layer,scope,spatialNodeId="",spatialPath=""){
  const fn=frame?.contentWindow?.ShaelvienPrototype?.setExternalDepth;
  if(typeof fn!=="function")return false;
  fn({tier,layer,scope,spatialNodeId,spatialPath});
  return true;
}

export function reload(frame,worldSource){
  if(!worldSource)return false;
  post(frame,{type:"world-source",worldSource});
  return true;
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
    if(!data||data.source!=="shaelvien-worldbuilder")return;
    try{
      if(data.type==="home"){
        if(!messageMatchesCurrentFrame(frame,data))return;
        await dotnet.invokeMethodAsync("RequestHomeFromPrototypeAsync");
        return;
      }
      if(data.type==="ready"){
        const worldSource=await dotnet.invokeMethodAsync("GetWorldBuilderSourceForPrototypeAsync");
        post(frame,worldSource
          ?{type:"world-source",worldSource}
          :{type:"world-source-missing"});
        return;
      }
      if(data.type==="selection-context"){
        const selection=data.selection&&typeof data.selection==="object"?data.selection:{};
        await dotnet.invokeMethodAsync(
          "ReceiveWorldBuilderSelectionContextAsync",
          String(selection.placementId||""),
          String(selection.name||""),
          String(selection.assetId||""),
          String(selection.kind||""),
          Number.isFinite(Number(selection.tier))?Math.trunc(Number(selection.tier)):0,
          Number.isFinite(Number(selection.layer))?Math.trunc(Number(selection.layer)):0,
          Number.isFinite(Number(selection.x))?Number(selection.x):0,
          Number.isFinite(Number(selection.y))?Number(selection.y):0
        );
        return;
      }
      if(data.type==="save-source"){
        const requestId=String(data.requestId||"");
        const result=await dotnet.invokeMethodAsync("SaveWorldBuilderSourceFromPrototypeAsync",data.state||{});
        post(frame,{type:"source-saved",requestId,result});
      }
    }catch(error){
      post(frame,{
        type:"source-save-error",
        requestId:String(data?.requestId||""),
        message:String(error?.message||error||"World source database operation failed")
      });
    }
  };
  bridges.set(frame,handler);
  window.addEventListener("message",handler);
  post(frame,{type:"bridge-ready"});
  try{
    frame?.addEventListener?.("load",()=>post(frame,{type:"bridge-ready"}),{once:true});
  }catch{}
}
