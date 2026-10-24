const gates=new WeakMap();
let activeRoot;
const controls='button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href],[tabindex]:not([tabindex="-1"])';
const visible=e=>e.getClientRects().length&&!e.closest('[inert]');
function modal(root){return root.querySelector('[role="alertdialog"]')||root.querySelector('[role="dialog"]');}
function focus(state){const target=modal(state.root);if(!target)return;state.modal=target;const input=target.querySelector('#world-name,#world-delete-approval');(input||[...target.querySelectorAll(controls)].find(visible)||target).focus({preventScroll:true});}
export function mount(root,dotnet){
 if(gates.has(root)){refresh(root);return;}
 const state={root,dotnet,previous:document.activeElement,inert:[]};
 // Disable only branches outside this modal, never an ancestor containing it.
 for(let branch=root;branch&&branch!==document.body;branch=branch.parentElement){
  for(const sibling of branch.parentElement?.children||[]){if(sibling!==branch&&!['SCRIPT','STYLE','LINK'].includes(sibling.tagName)){state.inert.push([sibling,sibling.inert]);sibling.inert=true;}}
 }
 state.key=event=>{
  const current=modal(root);if(!current)return;
  if(event.key==='Escape'){event.preventDefault();void dotnet.invokeMethodAsync('CloseWorldChooserAsync');return;}
  if(event.key!=='Tab')return;
  const list=[...current.querySelectorAll(controls)].filter(visible);if(!list.length){event.preventDefault();return;}
  const index=list.indexOf(document.activeElement);
  if(event.shiftKey&&(index<=0)){event.preventDefault();list.at(-1).focus();}
  else if(!event.shiftKey&&(index<0||index===list.length-1)){event.preventDefault();list[0].focus();}
 };
 state.focus=()=>{if(!modal(root)?.contains(document.activeElement))focus(state);};
 document.addEventListener('keydown',state.key,true);document.addEventListener('focusin',state.focus,true);
 activeRoot=root;gates.set(root,state);focus(state);
}
export function refresh(root){const state=gates.get(root);if(state&&state.modal!==modal(root))focus(state);}
export function release(){const root=activeRoot;const state=gates.get(root);if(!state)return;gates.delete(root);activeRoot=undefined;document.removeEventListener('keydown',state.key,true);document.removeEventListener('focusin',state.focus,true);for(const [node,inert] of state.inert)node.inert=inert;if(state.previous?.isConnected)state.previous.focus({preventScroll:true});}
