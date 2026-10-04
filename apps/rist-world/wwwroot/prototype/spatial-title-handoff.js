(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;

const host=window.parent;
const nativePromptKey='__ristNativePromptV1';
if(typeof host[nativePromptKey]!=='function')host[nativePromptKey]=host.prompt.bind(host);
const nativePrompt=host[nativePromptKey];
let pending=null;

const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const selectedCells=snapshot=>Array.isArray(snapshot?.selectedCells)?snapshot.selectedCells:[];

function live(message){
  const node=document.getElementById('live');
  if(node)node.textContent=String(message||'');
}

function selectionCenter(snapshot){
  const minX=Number.isFinite(Number(snapshot?.canonicalMinX))?Number(snapshot.canonicalMinX):.5;
  const minY=Number.isFinite(Number(snapshot?.canonicalMinY))?Number(snapshot.canonicalMinY):.5;
  const maxX=Number.isFinite(Number(snapshot?.canonicalMaxX))?Number(snapshot.canonicalMaxX):minX;
  const maxY=Number.isFinite(Number(snapshot?.canonicalMaxY))?Number(snapshot.canonicalMaxY):minY;
  return{x:Math.max(0,Math.min(1,(minX+maxX)/2)),y:Math.max(0,Math.min(1,(minY+maxY)/2))};
}

function createDraftTitle(snapshot){
  const world=document.getElementById('world');
  if(!world)return null;
  document.querySelectorAll('[data-spatial-title-draft="true"]').forEach(node=>node.remove());
  const plane=document.getElementById('surfacePlane');
  const width=Math.max(1,Number(plane?.naturalWidth)||Number(world.scrollWidth)||2048);
  const height=Math.max(1,Number(plane?.naturalHeight)||Number(world.scrollHeight)||2048);
  const center=selectionCenter(snapshot);
  const node=document.createElement('div');
  node.className='user-image-placement user-label-placement spatial-title-draft';
  node.dataset.spatialTitleDraft='true';
  node.setAttribute('role','status');
  node.setAttribute('aria-live','polite');
  Object.assign(node.style,{
    position:'absolute',
    left:`${center.x*width}px`,
    top:`${center.y*height}px`,
    transform:'translate(-50%,-50%)',
    transformOrigin:'50% 50%',
    zIndex:'9999',
    pointerEvents:'none',
    minWidth:'180px',
    maxWidth:'70%',
    textAlign:'center',
    whiteSpace:'nowrap',
    overflow:'visible',
    font:'700 48px/1.1 system-ui,sans-serif',
    letterSpacing:'.02em',
    color:'#fff2c7',
    textShadow:'0 2px 5px #000,0 0 10px #000',
    opacity:'.72'
  });
  node.textContent='NAME';
  world.appendChild(node);
  return node;
}

function openLabelsComposer(){
  const keyboard=document.getElementById('viewerKeyboard');
  const toggle=document.getElementById('keyboardToggle');
  if(keyboard?.hidden)toggle?.click();
  let labels=[...document.querySelectorAll('#keyboardTabs button')].find(button=>String(button.textContent||'').trim().toLowerCase()==='labels');
  if(labels&&!labels.classList.contains('active'))labels.click();
  labels=[...document.querySelectorAll('#keyboardTabs button')].find(button=>String(button.textContent||'').trim().toLowerCase()==='labels');
  if(labels&&!labels.classList.contains('active'))labels.click();
  return document.querySelector('#keyboardKeys .label-text-input');
}

function removePendingDraft(){
  if(!pending)return;
  clearInterval(pending.pollId);
  if(pending.input&&pending.captureKeydown)pending.input.removeEventListener('keydown',pending.captureKeydown,true);
  if(pending.input&&pending.onInput)pending.input.removeEventListener('input',pending.onInput);
  pending.draft?.remove();
  pending=null;
}

async function commitTitleRepresentation(){
  const state=pending;
  if(!state||!state.awaitingSave)return;
  clearInterval(state.pollId);
  if(state.input&&state.captureKeydown)state.input.removeEventListener('keydown',state.captureKeydown,true);
  if(state.input&&state.onInput)state.input.removeEventListener('input',state.onInput);
  state.draft?.remove();

  const input=state.input?.isConnected?state.input:openLabelsComposer();
  if(!input){pending=null;live(`${state.name} saved. Open Labels to place its title.`);return;}
  input.readOnly=false;
  input.removeAttribute('aria-busy');
  input.value=state.name;
  input.dispatchEvent(new Event('input',{bubbles:true}));
  input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',bubbles:true,cancelable:true}));
  pending=null;

  await pause(0);
  const editor=document.querySelector('#keyboardKeys .label-text-input');
  if(editor){
    editor.placeholder='Edit title text';
    editor.focus({preventScroll:true});
  }
  live(`${state.name} saved. Title selected; adjust font and position, then use World Builder Save when finished.`);
}

function watchForBoundarySave(){
  if(!pending)return;
  clearInterval(pending.pollId);
  pending.pollId=setInterval(()=>{
    if(!pending?.awaitingSave)return;
    const api=window.ShaelvienPrototype;
    const snapshot=typeof api?.getSpatialSelection==='function'?api.getSpatialSelection():null;
    if(snapshot?.active===false)void commitTitleRepresentation();
  },50);
}

function beginSpatialTitle(defaultValue=''){
  const api=window.ShaelvienPrototype;
  const snapshot=typeof api?.getSpatialSelection==='function'?api.getSpatialSelection():null;
  if(!snapshot||selectedCells(snapshot).length===0)return nativePrompt('Name this space',defaultValue);

  removePendingDraft();
  const draft=createDraftTitle(snapshot);
  const input=openLabelsComposer();
  if(!draft||!input)return nativePrompt('Name this space',defaultValue);

  input.value='';
  input.placeholder=snapshot.kind==='INSTANCE'?'Name this scene · Enter to save':'Name this area · Enter to save';
  input.setAttribute('aria-label',input.placeholder);
  input.readOnly=false;
  input.removeAttribute('aria-invalid');

  return new Promise(resolve=>{
    const onInput=()=>{
      const value=String(input.value||'');
      draft.textContent=value.trim()||'NAME';
      draft.style.opacity=value.trim()?'.96':'.72';
      draft.style.fontSize=`${Math.max(32,Math.min(64,48-(Math.max(0,value.length-18)*.6)))}px`;
      input.removeAttribute('aria-invalid');
    };
    const captureKeydown=event=>{
      if(event.key==='Enter'){
        event.preventDefault();
        event.stopImmediatePropagation();
        const name=String(input.value||'').trim();
        if(!name){
          input.setAttribute('aria-invalid','true');
          draft.textContent='NAME REQUIRED';
          draft.style.opacity='1';
          live('Enter a name before saving this space.');
          input.focus({preventScroll:true});
          return;
        }
        if(pending?.awaitingSave)return;
        pending.name=name;
        pending.awaitingSave=true;
        input.readOnly=true;
        input.setAttribute('aria-busy','true');
        draft.textContent=name;
        draft.style.opacity='1';
        live(`${name} ready. Saving spatial identity…`);
        watchForBoundarySave();
        resolve(name);
        return;
      }
      if(event.key==='Escape'){
        event.preventDefault();
        event.stopImmediatePropagation();
        removePendingDraft();
        resolve('');
      }
    };
    pending={snapshot,draft,input,onInput,captureKeydown,name:'',awaitingSave:false,pollId:0};
    input.addEventListener('input',onInput);
    input.addEventListener('keydown',captureKeydown,true);
    requestAnimationFrame(()=>{
      input.focus({preventScroll:true});
      input.setSelectionRange(0,input.value.length);
    });
    live('Text editor active. Enter the title shown over the selected area, then press Enter to save.');
  });
}

const promptProxy=(message,defaultValue)=>{
  if(String(message||'')==='Name this space')return beginSpatialTitle(defaultValue);
  return nativePrompt(message,defaultValue);
};

host.prompt=promptProxy;
window.addEventListener('pagehide',()=>{
  removePendingDraft();
  try{if(host.prompt===promptProxy)host.prompt=nativePrompt}catch{}
},{once:true});
})();