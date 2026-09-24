const sessions=new WeakMap();

function viewer(frame){
  try{return frame?.contentWindow?.ShaelvienPrototype||null}catch{return null}
}

function state(frame){
  try{return viewer(frame)?.getViewerState?.()||null}catch{return null}
}

async function emit(frame,dotnet,force=false){
  const current=state(frame);
  if(!current)return false;
  const zoom=Math.max(0.000001,Number(current.detailScale)||1);
  const session=sessions.get(frame);
  if(!force&&session&&Math.abs(zoom-session.lastZoom)<0.002)return true;
  if(session)session.lastZoom=zoom;
  try{
    await dotnet.invokeMethodAsync('UpdateCameraFromPrototypeAsync',zoom);
    return true;
  }catch{return false}
}

export function attach(frame,dotnet){
  detach(frame);
  if(!frame||!dotnet)return;
  const onLoad=()=>{void emit(frame,dotnet,true)};
  frame.addEventListener('load',onLoad);
  const timer=setInterval(()=>{void emit(frame,dotnet,false)},90);
  sessions.set(frame,{dotnet,onLoad,timer,lastZoom:-1});
  setTimeout(()=>{void emit(frame,dotnet,true)},250);
}

export function fitWorld(frame){
  try{
    const api=viewer(frame);
    if(api?.fitWorld)return !!api.fitWorld();
    frame?.contentWindow?.document?.getElementById('settingsFit')?.click();
    return true;
  }catch{return false}
}

export function focusBounds(frame,x,y,width,height){
  try{
    const api=viewer(frame);
    if(!api?.focusNormalizedBounds)return false;
    return !!api.focusNormalizedBounds({x:Number(x),y:Number(y),width:Number(width),height:Number(height)});
  }catch{return false}
}

export function currentZoom(frame){
  return Math.max(0.000001,Number(state(frame)?.detailScale)||1);
}

export function detach(frame){
  const session=sessions.get(frame);
  if(!session)return;
  clearInterval(session.timer);
  frame?.removeEventListener('load',session.onLoad);
  sessions.delete(frame);
}
