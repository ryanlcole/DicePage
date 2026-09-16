(()=>{
 'use strict';

 const MODE='admin';
 const STATE_KEY='rist.worldbuilder.adminKeyboard.v1';
 const STYLE_ID='rist-worldbuilder-admin-keyboard-css';
 let root=null,keyboard=null,modeRow=null,keysNode=null,modeName=null,observer=null,raf=0,active=false;
 let overlay=null;
 let state=readState();

 function readState(){
  try{return Object.assign({anchor:null,cursor:null,selection:[],name:'',fill:'#4b6ea8',fillOpacity:.28,borderColor:'#f1d58a',borderWidth:2,borderStyle:'solid',borderType:'administrative',principal:'',grant:'View',stopsInheritance:false},JSON.parse(localStorage.getItem(STATE_KEY)||'{}'))}catch{return{anchor:null,cursor:null,selection:[],name:'',fill:'#4b6ea8',fillOpacity:.28,borderColor:'#f1d58a',borderWidth:2,borderStyle:'solid',borderType:'administrative',principal:'',grant:'View',stopsInheritance:false}}
 }
 function saveState(){try{localStorage.setItem(STATE_KEY,JSON.stringify(state))}catch{}}
 function studio(){return document.querySelector('.worldbuilder-studio')}
 function viewer(){return root?.querySelector('.studio-viewer-canvas')||null}
 function cursorApi(){return window.RistWorldBuilderGridCursor||null}
 function announce(text){const live=keyboard?.querySelector('.wb-device-live-region');if(live)live.textContent=text}
 function emit(name,detail={}){window.dispatchEvent(new CustomEvent(name,{detail:{...detail,source:'admin-keyboard'},bubbles:true,composed:true}))}
 function ensureStyle(){if(document.getElementById(STYLE_ID))return;const link=document.createElement('link');link.id=STYLE_ID;link.rel='stylesheet';link.href='./css/worldbuilder-admin-keyboard.css?v=20260915-admin-keyboard-2';document.head.appendChild(link)}
 function cellKey(col,row,n){return`${n}:${col}:${row}`}
 function cursor(){const c=cursorApi()?.get?.();return c&&Number.isFinite(c.col)&&Number.isFinite(c.row)?{col:c.col,row:c.row,n:c.n||12}:null}
 function selectionCells(){return new Set(Array.isArray(state.selection)?state.selection:[])}
 function setSelection(set){state.selection=[...set];saveState();renderOverlay();renderAdmin();emit('rist:worldbuilder-admin-selection',{selection:state.selection,summary:selectionSummary()})}
 function selectionSummary(){
  const cells=state.selection||[];if(!cells.length)return{count:0,label:'No map squares selected'};
  const parsed=cells.map(k=>k.split(':').map(Number)).filter(x=>x.length===3&&x.every(Number.isFinite));
  const cols=parsed.map(x=>x[1]),rows=parsed.map(x=>x[2]);
  return{count:parsed.length,minColumn:Math.min(...cols),maxColumn:Math.max(...cols),minRow:Math.min(...rows),maxRow:Math.max(...rows),label:`${parsed.length} square${parsed.length===1?'':'s'} selected`};
 }
 function markAnchor(){const c=cursor();if(!c)return;state.anchor=c;state.cursor=c;saveState();announce(`Admin selection anchor set at column ${c.col+1}, row ${c.row+1}`);renderAdmin()}
 function selectRectangle(){const c=cursor();if(!c)return;if(!state.anchor||state.anchor.n!==c.n)state.anchor=c;state.cursor=c;const minC=Math.min(state.anchor.col,c.col),maxC=Math.max(state.anchor.col,c.col),minR=Math.min(state.anchor.row,c.row),maxR=Math.max(state.anchor.row,c.row);const next=new Set();for(let r=minR;r<=maxR;r++)for(let col=minC;col<=maxC;col++)next.add(cellKey(col,r,c.n));setSelection(next);announce(`${next.size} grid squares selected as a rectangle`)}
 function toggleCurrent(){const c=cursor();if(!c)return;const set=selectionCells(),key=cellKey(c.col,c.row,c.n);if(set.has(key))set.delete(key);else set.add(key);setSelection(set);announce(`${set.has(key)?'Added':'Removed'} column ${c.col+1}, row ${c.row+1}`)}
 function clearSelection(){state.anchor=null;state.cursor=null;setSelection(new Set());announce('Admin region selection cleared')}
 function selectAllVisible(){const c=cursor();if(!c)return;const set=new Set();for(let r=0;r<c.n;r++)for(let col=0;col<c.n;col++)set.add(cellKey(col,r,c.n));setSelection(set);announce(`Selected all ${c.n*c.n} visible grid squares`)}

 function gridRect(){const area=viewer(),grid=root?.querySelector('.studio-viewer-grid');const rect=(grid&&getComputedStyle(grid).display!=='none'?grid:area)?.getBoundingClientRect();if(!area||!rect||rect.width<1||rect.height<1)return null;const side=Math.min(rect.width,rect.height);return{area:area.getBoundingClientRect(),left:rect.left+(rect.width-side)/2,top:rect.top+(rect.height-side)/2,width:side,height:side}}
 function renderOverlay(){
  const area=viewer();if(!area)return;
  if(!overlay||!overlay.isConnected){overlay=document.createElement('div');overlay.className='wb-admin-region-overlay';overlay.setAttribute('aria-hidden','true');area.appendChild(overlay)}
  overlay.replaceChildren();const bounds=gridRect();if(!bounds)return;
  const selected=(state.selection||[]).map(k=>k.split(':').map(Number)).filter(x=>x.length===3&&x.every(Number.isFinite));
  const selectedKeys=new Set(selected.map(([n,col,row])=>cellKey(col,row,n)));
  const borderWidth=Math.max(1,Number(state.borderWidth)||1),borderStyle=state.borderStyle||'solid',borderColor=state.borderColor||'#f1d58a';
  const border=`${borderWidth}px ${borderStyle} ${borderColor}`;
  for(const [n,col,row] of selected){
   const cell=bounds.width/n,mark=document.createElement('div');
   mark.className='wb-admin-selected-cell';
   mark.style.left=`${bounds.left-bounds.area.left+col*cell}px`;
   mark.style.top=`${bounds.top-bounds.area.top+row*cell}px`;
   mark.style.width=`${cell}px`;mark.style.height=`${cell}px`;
   mark.style.backgroundColor=hexWithAlpha(state.fill,state.fillOpacity);
   if(!selectedKeys.has(cellKey(col,row-1,n)))mark.style.borderTop=border;
   if(!selectedKeys.has(cellKey(col+1,row,n)))mark.style.borderRight=border;
   if(!selectedKeys.has(cellKey(col,row+1,n)))mark.style.borderBottom=border;
   if(!selectedKeys.has(cellKey(col-1,row,n)))mark.style.borderLeft=border;
   mark.dataset.borderType=state.borderType||'administrative';
   overlay.appendChild(mark);
  }
 }
 function hexWithAlpha(hex,opacity){const value=String(hex||'#4b6ea8').replace('#','');if(!/^[0-9a-fA-F]{6}$/.test(value))return`rgba(75,110,168,${opacity})`;const r=parseInt(value.slice(0,2),16),g=parseInt(value.slice(2,4),16),b=parseInt(value.slice(4,6),16);return`rgba(${r},${g},${b},${Math.max(0,Math.min(1,Number(opacity)||0))})`}

 function key(label,sub,action,{disabled=false,activeKey=false,danger=false}={}){const b=document.createElement('button');b.type='button';b.className='wb-device-key wb-admin-key';if(activeKey)b.classList.add('active');if(danger)b.classList.add('danger');b.disabled=disabled;b.dataset.accessRole='admin-key';b.dataset.accessTranslation='available';b.setAttribute('aria-label',sub?`${label}. ${sub}`:label);const strong=document.createElement('strong');strong.textContent=label;b.appendChild(strong);if(sub){const small=document.createElement('small');small.textContent=sub;b.appendChild(small)}b.addEventListener('click',action);return b}
 function inputRow(label,type,value,onChange,options={}){const wrap=document.createElement('label');wrap.className='wb-admin-field';const span=document.createElement('span');span.textContent=label;const input=document.createElement('input');input.type=type;input.value=value??'';if(options.min!=null)input.min=String(options.min);if(options.max!=null)input.max=String(options.max);if(options.step!=null)input.step=String(options.step);input.setAttribute('aria-label',label);input.addEventListener('input',()=>onChange(input.value));wrap.append(span,input);return wrap}
 function selectRow(label,value,values,onChange){const wrap=document.createElement('label');wrap.className='wb-admin-field';const span=document.createElement('span');span.textContent=label;const select=document.createElement('select');select.setAttribute('aria-label',label);for(const item of values){const option=document.createElement('option');option.value=item;option.textContent=item;select.appendChild(option)}select.value=value;select.addEventListener('change',()=>onChange(select.value));wrap.append(span,select);return wrap}
 function regionPayload(kind){const summary=selectionSummary();return{entityType:'administrative-region',schemaVersion:1,name:(state.name||'').trim(),geometry:{kind:'grid-mask',cells:[...(state.selection||[])],presentationSelection:true,selectionDensity:cursor()?.n||null},cartography:{fill:state.fill,fillOpacity:Number(state.fillOpacity),border:{color:state.borderColor,width:Number(state.borderWidth),style:state.borderStyle,type:state.borderType}},selectionSummary:summary,operation:kind}}
 function applyCartography(){if(!(state.selection||[]).length){announce('Select map squares before applying admin cartography');return}emit('rist:worldbuilder-admin-region-write',regionPayload('cartography'));announce(`Administrative cartography prepared for ${selectionSummary().label}`)}
 function defineBorder(){if(!(state.selection||[]).length){announce('Select map squares before defining a border');return}const payload=regionPayload('border');payload.boundary={model:'shared-edge-perimeter',semanticType:state.borderType,color:state.borderColor,width:Number(state.borderWidth),style:state.borderStyle};emit('rist:worldbuilder-admin-border-write',payload);announce(`Shared ${state.borderType} border prepared around ${selectionSummary().label}`)}
 function permissionRequest(){if(!(state.selection||[]).length){announce('Select map squares before assigning permissions');return}const principal=(state.principal||'').trim();if(!principal&&state.grant!=='Public'){announce('Enter a user or principal before assigning this permission');return}const payload={resourceSelection:{kind:'admin-grid-region',cells:[...(state.selection||[])],summary:selectionSummary()},principal:state.grant==='Public'?'*':principal,grant:state.grant,stopsInheritance:!!state.stopsInheritance,requiresSharedRecursiveAuthority:true};emit('rist:worldbuilder-admin-permission-request',payload);announce(`${state.grant} permission request prepared for ${payload.principal}. Shared authority must approve and persist it.`)}

 function renderAdmin(){
  if(!active||!keysNode?.isConnected)return;
  keysNode.replaceChildren();
  const summary=selectionSummary();const status=document.createElement('div');status.className='wb-admin-status';status.setAttribute('role','status');status.textContent=`Admin region · ${summary.label}`;keysNode.appendChild(status);
  [key('Anchor','Start region at D-pad square',markAnchor),key('Rectangle','Anchor → D-pad',selectRectangle),key('Add / Remove','Current D-pad square',toggleCurrent),key('All Visible','Current N×N view',selectAllVisible),key('Clear','Region selection',clearSelection,{disabled:summary.count===0,danger:true})].forEach(n=>keysNode.appendChild(n));

  const fields=document.createElement('div');fields.className='wb-admin-fields';
  fields.append(
   inputRow('Region name','text',state.name,v=>{state.name=v;saveState()}),
   inputRow('Fill color','color',state.fill,v=>{state.fill=v;saveState();renderOverlay()}),
   inputRow('Fill opacity','range',state.fillOpacity,v=>{state.fillOpacity=Number(v);saveState();renderOverlay()},{min:0,max:1,step:.05}),
   inputRow('Border color','color',state.borderColor,v=>{state.borderColor=v;saveState();renderOverlay()}),
   inputRow('Border width','range',state.borderWidth,v=>{state.borderWidth=Number(v);saveState();renderOverlay()},{min:1,max:12,step:1}),
   selectRow('Border style',state.borderStyle,['solid','dashed','dotted','double'],v=>{state.borderStyle=v;saveState();renderOverlay()}),
   selectRow('Border type',state.borderType,['administrative','continent','country','state','province','county','district','realm','zone'],v=>{state.borderType=v;saveState();renderOverlay()})
  );
  keysNode.appendChild(fields);
  keysNode.append(key('Apply Color',state.name||'Administrative region',applyCartography,{disabled:summary.count===0}),key('Set Border','Shared perimeter edges',defineBorder,{disabled:summary.count===0}));

  const permissions=document.createElement('div');permissions.className='wb-admin-permission-fields';
  permissions.append(
   inputRow('User / principal','text',state.principal,v=>{state.principal=v;saveState()}),
   selectRow('Permission',state.grant,['View','Edit','Public','Deny'],v=>{state.grant=v;saveState();renderAdmin()})
  );
  const inherit=document.createElement('label');inherit.className='wb-admin-check';const cb=document.createElement('input');cb.type='checkbox';cb.checked=!!state.stopsInheritance;cb.addEventListener('change',()=>{state.stopsInheritance=cb.checked;saveState()});inherit.append(cb,document.createTextNode('Stop inherited permissions at this region'));permissions.appendChild(inherit);keysNode.appendChild(permissions);
  const note=document.createElement('div');note.className='wb-admin-authority-note';note.textContent='Permissions are not inferred from map color or borders. View / Edit / Public / Deny is handed to Recursive Authority for approval and persistence.';keysNode.appendChild(note);
  keysNode.append(key('Assign Permission',state.grant,permissionRequest,{disabled:summary.count===0||(!String(state.principal||'').trim()&&state.grant!=='Public')}));
  renderOverlay();
 }

 function enterAdmin(){active=true;try{localStorage.setItem('rist.worldbuilder.deviceKeyboard.mode.adminOverlay.v1','true')}catch{}patch();if(modeName)modeName.textContent='Admin keyboard';modeRow?.querySelectorAll('.wb-device-mode').forEach(b=>{const on=b.dataset.mode===MODE;b.classList.toggle('active',on);b.setAttribute('aria-selected',on?'true':'false')});renderAdmin();announce('Admin keyboard. Use the persistent D-pad to position the grid cursor, then Anchor and Rectangle or Add / Remove to select a region.')}
 function leaveAdmin(){active=false;try{localStorage.removeItem('rist.worldbuilder.deviceKeyboard.mode.adminOverlay.v1')}catch{}overlay?.remove();overlay=null}
 function patch(){
  root=studio();keyboard=root?.querySelector('.wb-device-keyboard');if(!root||!keyboard)return;
  ensureStyle();modeRow=keyboard.querySelector('.wb-device-mode-row');keysNode=keyboard.querySelector('.wb-device-keys');modeName=keyboard.querySelector('.wb-device-mode-name');if(!modeRow||!keysNode)return;
  let button=modeRow.querySelector('.wb-device-mode[data-mode="admin"]');if(!button){button=document.createElement('button');button.type='button';button.className='wb-device-mode';button.dataset.mode=MODE;button.textContent='Admin';button.setAttribute('role','tab');button.setAttribute('aria-label','Admin keyboard');button.dataset.accessTranslation='available';button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();enterAdmin()});modeRow.appendChild(button)}
  for(const other of modeRow.querySelectorAll('.wb-device-mode:not([data-mode="admin"])'))if(other.dataset.adminLeaveWired!=='1'){other.dataset.adminLeaveWired='1';other.addEventListener('click',leaveAdmin,{capture:true})}
  if(active)renderAdmin();
 }
 function schedule(){if(raf)return;raf=requestAnimationFrame(()=>{raf=0;patch();renderOverlay()})}
 function onCursor(event){if(!active)return;state.cursor=event.detail||cursor();saveState();renderAdmin()}
 function start(){patch();observer=new MutationObserver(schedule);observer.observe(document.documentElement,{childList:true,subtree:true});window.addEventListener('rist:worldbuilder-grid-cursor',onCursor);window.addEventListener('resize',schedule,{passive:true});window.addEventListener('orientationchange',schedule,{passive:true})}

 window.RistWorldBuilderAdmin={
  open:enterAdmin,
  close:leaveAdmin,
  getState:()=>JSON.parse(JSON.stringify(state)),
  clearSelection,
  applyCartography,
  defineBorder,
  requestPermission:permissionRequest
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();