const bridges=new WeakMap();

function post(frame,message){
  try{frame?.contentWindow?.postMessage({source:"shaelvien-worldbuilder-host",...message},location.origin)}catch{}
}

export async function save(frame){
  const fn=frame?.contentWindow?.ShaelvienPrototype?.save;
  if(typeof fn!=="function")return false;
  await fn();
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
}
