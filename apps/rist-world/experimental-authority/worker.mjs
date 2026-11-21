/** Fail-closed edge gateway for an isolated, single-player Endemar pilot.
 * Bootstrap credential is a deployment secret; it is NOT owner identity or GM permission.
 */
export {EndemarRoom} from './room.mjs';
const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
const response=(data,code=200)=>new Response(JSON.stringify(data),{status:code,headers});
function bearer(request){return /^Bearer (.{32,256})$/.exec(request.headers.get('authorization')||'')?.[1]||'';}
function safeEqual(a,b){if(typeof a!=='string'||typeof b!=='string')return false;let d=a.length^b.length;for(let i=0;i<Math.max(a.length,b.length);i++)d|=(a.charCodeAt(i)||0)^(b.charCodeAt(i)||0);return d===0;}
export default {
  async fetch(request,env){
    const path=new URL(request.url).pathname;
    if(path==='/api/endemar/health' && request.method==='GET')return response({state:'EXPERIMENTAL_NOT_PRODUCTION',world:'end:pilot:one'});
    if(!env?.ENDEMAR_ROOM)return response({error:'UNCONFIGURED'},503);
    const objectId=env.ENDEMAR_ROOM.idFromName('end:pilot:one');
    const room=env.ENDEMAR_ROOM.get(objectId);
    if(path==='/api/endemar/session' && request.method==='POST'){
      if(typeof env.ENDEMAR_BOOTSTRAP_KEY!=='string'||env.ENDEMAR_BOOTSTRAP_KEY.length<32)return response({error:'BOOTSTRAP_DISABLED'},503);
      if(!safeEqual(bearer(request),env.ENDEMAR_BOOTSTRAP_KEY))return response({error:'NOT_AUTHORIZED'},403);
      return room.fetch(new Request('https://internal.local/internal/issue',{method:'POST'}));
    }
    if(path==='/api/endemar/snapshot' && request.method==='GET')return room.fetch(new Request('https://internal.local/internal/snapshot',{headers:{authorization:request.headers.get('authorization')||''}}));
    if(path==='/api/endemar/intent' && request.method==='POST'){
      // Explicit body bound before forwarding to the trusted room.
      const body=await request.text();
      if(body.length>1024)return response({error:'INTENT_TOO_LARGE'},413);
      return room.fetch(new Request('https://internal.local/internal/intent',{method:'POST',headers:{authorization:request.headers.get('authorization')||'', 'content-type':'application/json'},body}));
    }
    return response({error:'NOT_FOUND'},404);
  }
};
