let handler=null;
export function attach(dotnet){
  detach();
  handler=event=>{
    if(event.origin!==location.origin)return;
    const data=event.data;
    if(!data||data.source!=="rist-legacy-binder"||data.type!=="open-entry")return;
    dotnet.invokeMethodAsync("OpenLegacyEntryFromBinderAsync",String(data.worldId||""),String(data.entryId||"")).catch(()=>{});
  };
  window.addEventListener("message",handler);
}
export function detach(){
  if(handler)window.removeEventListener("message",handler);
  handler=null;
}
