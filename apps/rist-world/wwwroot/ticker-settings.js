(()=>{
 'use strict';
 const KEY='rist.ticker.config.v1';
 const DEFAULTS={
  visible:{stars:true,sky:true,cal:true,ugc:true,date:true,utc:true,start:true},
  custom:[]
 };
 const esc=v=>String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
 function load(){
  try{
   const raw=JSON.parse(localStorage.getItem(KEY)||'null')||{};
   return {visible:{...DEFAULTS.visible,...(raw.visible||{})},custom:Array.isArray(raw.custom)?raw.custom:[]};
  }catch{return structuredClone(DEFAULTS)}
 }
 function save(cfg){localStorage.setItem(KEY,JSON.stringify(cfg));document.dispatchEvent(new CustomEvent('rist:ticker-config-changed',{detail:cfg}))}
 function row(label,control){return `<label class="rist-setting-row"><span>${label}</span><span>${control}</span></label>`}
 function checkbox(key,label,cfg){return row(label,`<input type="checkbox" data-ticker-visible="${key}" ${cfg.visible[key]?'checked':''} aria-label="Show ${esc(label)} on ticker">`)}
 function currentHtml(cfg){return [
  ['stars','Stars'],['sky','Sky'],['cal','Calendar'],['ugc','UGC'],['date','Date'],['utc','UTC Time'],['start','Start Menu']
 ].map(([k,l])=>checkbox(k,l,cfg)).join('')}
 function customSummary(x,i){
  const label=esc(x.label||x.type||'Context');
  let sample='';
  if(x.type==='date')sample=`${label}: ${esc(x.value||'05/22/8967')} ${esc(x.suffix||'DC')}`;
  else if(x.type==='time')sample=`${label}: ${esc(x.value||'14:76')} ${esc(x.suffix||'TW')}`;
  else if(x.type==='currency')sample=`${label}: ${esc(x.value||'0')} ${esc(x.suffix||'gp')}`;
  else if(x.type==='number')sample=`${label}: ${esc(x.value||'0')}`;
  else sample=esc(x.text||x.label||'Custom ticker message');
  return `<div class="rist-setting-row" data-ticker-custom-row="${i}"><span>${sample}</span><span><label style="display:inline-flex;align-items:center;gap:4px"><input type="checkbox" data-ticker-custom-visible="${i}" ${x.visible!==false?'checked':''}> Show</label> <button type="button" data-ticker-custom-edit="${i}">Edit</button> <button type="button" data-ticker-custom-delete="${i}" aria-label="Delete custom ticker context">×</button></span></div>`;
 }
 function builder(type='text',item=null,index=''){
  const x=item||{};
  const typeSelect=`<select data-ticker-type><option value="date" ${type==='date'?'selected':''}>Date</option><option value="time" ${type==='time'?'selected':''}>Time</option><option value="currency" ${type==='currency'?'selected':''}>Currency</option><option value="number" ${type==='number'?'selected':''}>Number</option><option value="text" ${type==='text'?'selected':''}>Message</option></select>`;
  let fields='';
  if(type==='date')fields=`${row('Label',`<input data-ticker-label value="${esc(x.label||'Dwarven Date')}" placeholder="Dwarven Date">`)}${row('Current date',`<input data-ticker-value value="${esc(x.value||'05/22/8967')}" placeholder="05/22/8967">`)}${row('Era / suffix',`<input data-ticker-suffix value="${esc(x.suffix||'DC')}" placeholder="DC">`)}`;
  else if(type==='time')fields=`${row('Label',`<input data-ticker-label value="${esc(x.label||'Dwarven Time')}" placeholder="Dwarven Time">`)}${row('Seconds per unit',`<input type="number" min="1" max="9999" data-ticker-ratio value="${Number(x.ratio)||80}">`)}${row('Current time',`<input data-ticker-value value="${esc(x.value||'14:76')}" placeholder="14:76">`)}${row('AM/PM / suffix',`<input data-ticker-suffix value="${esc(x.suffix||'TW')}" placeholder="TW or Titan Wakes">`)}`;
  else if(type==='currency')fields=`${row('Label',`<input data-ticker-label value="${esc(x.label||'Treasury')}" placeholder="Treasury">`)}${row('Value',`<input data-ticker-value value="${esc(x.value||'0')}" placeholder="125">`)}${row('Currency / suffix',`<input data-ticker-suffix value="${esc(x.suffix||'gp')}" placeholder="gp">`)}`;
  else if(type==='number')fields=`${row('Label',`<input data-ticker-label value="${esc(x.label||'Count')}" placeholder="Count">`)}${row('Value',`<input data-ticker-value value="${esc(x.value||'0')}" placeholder="0">`)}`;
  else fields=row('Message',`<textarea data-ticker-text maxlength="1200" placeholder="It is the morning of the Equinox festival...">${esc(x.text||'')}</textarea>`);
  return `<section data-ticker-builder data-index="${index}"><h3>${index===''?'Add Context':'Edit Context'}</h3>${row('Type',typeSelect)}<div data-ticker-fields>${fields}</div><div class="rist-setting-row"><span></span><span><button type="button" data-ticker-save>${index===''?'Add to Ticker':'Save'}</button> <button type="button" data-ticker-cancel>Cancel</button></span></div></section>`;
 }
 function renderTickerPanel(panel){
  const cfg=load();
  panel.innerHTML=`<section class="rist-start-sub" data-ticker-panel><h2>Ticker</h2><p class="rist-start-note">Checked items are visible in the header ticker. Add custom dates, clocks, currencies, numbers, or scrolling context messages.</p><h3>Current Context</h3>${currentHtml(cfg)}<h3>Custom Context</h3><div data-ticker-custom-list>${cfg.custom.length?cfg.custom.map(customSummary).join(''):'<p class="rist-start-note">No custom ticker context yet.</p>'}</div><button type="button" class="rist-start-button" data-ticker-add aria-label="Add ticker context">＋ Add Context</button><div data-ticker-builder-host></div><button type="button" class="rist-start-back" data-ticker-back>Back</button><button type="button" class="rist-start-exit" data-ticker-exit>Exit</button></section>`;
 }
 function renameWorldButton(){document.querySelectorAll('[data-start-section="World"]').forEach(b=>{if(b.textContent!=='Ticker')b.textContent='Ticker'})}
 function panel(){return document.querySelector('.rist-start-panel')}
 function openTicker(){const p=panel();if(p)renderTickerPanel(p)}
 function showBuilder(type='text',item=null,index=''){const host=panel()?.querySelector('[data-ticker-builder-host]');if(host)host.innerHTML=builder(type,item,index)}
 function readBuilder(){
  const b=panel()?.querySelector('[data-ticker-builder]');if(!b)return null;
  const type=b.querySelector('[data-ticker-type]')?.value||'text';
  return {type,label:b.querySelector('[data-ticker-label]')?.value.trim()||'',value:b.querySelector('[data-ticker-value]')?.value.trim()||'',suffix:b.querySelector('[data-ticker-suffix]')?.value.trim()||'',ratio:Math.max(1,Number(b.querySelector('[data-ticker-ratio]')?.value)||60),text:b.querySelector('[data-ticker-text]')?.value.trim()||'',visible:true,startedAt:Date.now()};
 }
 function wire(){
  document.addEventListener('click',e=>{
   const t=e.target instanceof Element?e.target:null;if(!t)return;
   const world=t.closest('[data-start-section="World"]');
   if(world){e.preventDefault();e.stopImmediatePropagation();openTicker();return}
   if(t.closest('[data-ticker-add]')){showBuilder();return}
   const edit=t.closest('[data-ticker-custom-edit]');if(edit){const cfg=load(),i=+edit.dataset.tickerCustomEdit,x=cfg.custom[i];if(x)showBuilder(x.type,x,String(i));return}
   const del=t.closest('[data-ticker-custom-delete]');if(del){const cfg=load();cfg.custom.splice(+del.dataset.tickerCustomDelete,1);save(cfg);openTicker();return}
   if(t.closest('[data-ticker-cancel]')){const host=panel()?.querySelector('[data-ticker-builder-host]');if(host)host.innerHTML='';return}
   if(t.closest('[data-ticker-save]')){const item=readBuilder(),b=panel()?.querySelector('[data-ticker-builder]');if(!item||!b)return;const cfg=load(),idx=b.dataset.index;if(idx==='')cfg.custom.push(item);else cfg.custom[+idx]=item;save(cfg);openTicker();return}
   if(t.closest('[data-ticker-back]')){window.RistStartMenu?.open?.();setTimeout(renameWorldButton,0);return}
   if(t.closest('[data-ticker-exit]')){window.RistStartMenu?.close?.();return}
  },true);
  document.addEventListener('change',e=>{
   const t=e.target;if(!(t instanceof Element))return;
   if(t.matches('[data-ticker-visible]')){const cfg=load();cfg.visible[t.dataset.tickerVisible]=t.checked;save(cfg);return}
   if(t.matches('[data-ticker-custom-visible]')){const cfg=load(),i=+t.dataset.tickerCustomVisible;if(cfg.custom[i]){cfg.custom[i].visible=t.checked;save(cfg)}return}
   if(t.matches('[data-ticker-type]')){showBuilder(t.value,null,'');return}
  });
  const obs=new MutationObserver(renameWorldButton);obs.observe(document.body,{childList:true,subtree:true});renameWorldButton();
 }
 window.RistTickerSettings={load,save,open:openTicker};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
})();