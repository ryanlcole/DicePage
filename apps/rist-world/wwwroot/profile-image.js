(()=>{
 'use strict';
 const IMAGE_KEY='rist.profile.image.v1';
 const ALIAS_KEY='rist.profile.alias.v1';
 const PROFILE_MAP_KEY='rist.profile.images.v1';
 let sourceData='';
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 const esc=s=>window.CSS?.escape?CSS.escape(String(s)):String(s).replace(/["\\]/g,'\\$&');
 function profileMap(){try{return JSON.parse(localStorage.getItem(PROFILE_MAP_KEY)||'{}')||{}}catch{return{}}}
 function saveMap(map){localStorage.setItem(PROFILE_MAP_KEY,JSON.stringify(map))}
 function currentAlias(){return (localStorage.getItem(ALIAS_KEY)||q('.rist-start-sub input[placeholder="Alias"]')?.value||q('[data-player-name]')?.getAttribute('data-player-name')||'').trim()}
 function currentImage(){return localStorage.getItem(IMAGE_KEY)||''}
 function imageFor(name){
  name=(name||'').trim();
  if(name){
   const map=profileMap();if(map[name])return map[name];
   const selectors=[`[data-player-name="${esc(name)}"] img`,`[data-private-chat-name="${esc(name)}"] img`,`[data-profile-name="${esc(name)}"] img`];
   for(const selector of selectors){const img=q(selector);if(img?.src)return img.src;}
  }
  const alias=currentAlias();if(!name||!alias||name===alias)return currentImage();return '';
 }
 function persistImage(data){
  if(data)localStorage.setItem(IMAGE_KEY,data);else localStorage.removeItem(IMAGE_KEY);
  const alias=currentAlias();if(alias){const map=profileMap();if(data)map[alias]=data;else delete map[alias];saveMap(map)}
  document.dispatchEvent(new CustomEvent('rist:profile-image-changed',{detail:{alias,image:data||'',src:data||''}}));
 }
 function cropData(img,zoom,x,y){
  const size=512,canvas=document.createElement('canvas');canvas.width=size;canvas.height=size;const ctx=canvas.getContext('2d');if(!ctx)return img.src;
  const iw=img.naturalWidth||1,ih=img.naturalHeight||1,base=Math.max(size/iw,size/ih),scale=base*(Number(zoom)||1),w=iw*scale,h=ih*scale;
  const px=(Number(x)||50)/100,py=(Number(y)||50)/100;const dx=(size-w)/2+((px-.5)*size),dy=(size-h)/2+((py-.5)*size);
  ctx.clearRect(0,0,size,size);ctx.drawImage(img,dx,dy,w,h);return canvas.toDataURL('image/png',.92);
 }
 function editorHtml(){return `<div class="rist-profile-image-editor"><div class="rist-profile-preview"><img alt="Profile preview"></div><label class="rist-profile-file">Choose image<input type="file" accept="image/png,image/jpeg,image/webp" data-profile-file></label><label>Zoom <input type="range" min="1" max="3" step="0.01" value="1" data-profile-zoom></label><label>Horizontal <input type="range" min="0" max="100" value="50" data-profile-x></label><label>Vertical <input type="range" min="0" max="100" value="50" data-profile-y></label><div class="rist-profile-actions"><button type="button" data-profile-save>Save image</button><button type="button" data-profile-clear>Clear</button></div><p class="rist-start-note">GM and Private chat use this player profile image. Roleplay uses the active character portrait.</p></div>`}
 function renderPreview(host){const img=q('.rist-profile-preview img',host),zoom=q('[data-profile-zoom]',host),x=q('[data-profile-x]',host),y=q('[data-profile-y]',host);if(!img)return;const z=Number(zoom?.value)||1,xp=Number(x?.value)||50,yp=Number(y?.value)||50;img.style.transform=`translate(${(xp-50)*.8}%,${(yp-50)*.8}%) scale(${z})`}
 function wireEditor(host){
  if(host.dataset.profileWired==='1')return;host.dataset.profileWired='1';const img=q('.rist-profile-preview img',host),file=q('[data-profile-file]',host);sourceData=currentImage();if(sourceData)img.src=sourceData;
  qa('input[type="range"]',host).forEach(r=>r.addEventListener('input',()=>renderPreview(host)));
  file?.addEventListener('change',()=>{const f=file.files?.[0];if(!f)return;const reader=new FileReader();reader.onload=()=>{sourceData=String(reader.result||'');img.src=sourceData;renderPreview(host)};reader.readAsDataURL(f)});
  q('[data-profile-save]',host)?.addEventListener('click',()=>{if(!img?.src)return;const data=cropData(img,q('[data-profile-zoom]',host)?.value,q('[data-profile-x]',host)?.value,q('[data-profile-y]',host)?.value);persistImage(data);sourceData=data;img.src=data;qa('input[type="range"]',host).forEach(r=>r.value=r.hasAttribute('data-profile-zoom')?'1':'50');renderPreview(host);patchChatPortrait()});
  q('[data-profile-clear]',host)?.addEventListener('click',()=>{persistImage('');sourceData='';img.removeAttribute('src');patchChatPortrait()});
 }
 function patchSettings(){
  const profile=q('.rist-start-sub .rist-account-profile');if(!profile)return;
  const alias=q('.rist-start-sub input[placeholder="Alias"]');if(alias&&alias.dataset.profileAlias!=='1'){alias.dataset.profileAlias='1';alias.value=localStorage.getItem(ALIAS_KEY)||alias.value;alias.addEventListener('change',()=>{const previous=currentAlias();localStorage.setItem(ALIAS_KEY,alias.value.trim());const image=currentImage();if(image){const map=profileMap();if(previous&&previous!==alias.value.trim())delete map[previous];if(alias.value.trim())map[alias.value.trim()]=image;saveMap(map)}patchChatPortrait()})}
  let host=q('.rist-profile-image-editor',profile.parentElement);if(!host){profile.insertAdjacentHTML('afterend',editorHtml());host=q('.rist-profile-image-editor',profile.parentElement)}wireEditor(host);
  const avatar=q('.rist-account-avatar',profile),saved=currentImage();if(avatar){avatar.innerHTML=saved?`<img src="${saved}" alt="">`:''}
 }
 function chatMode(){const active=qa('.rist-chat-themed-tabs button').find(b=>b.classList.contains('active'));const mode=(active?.textContent||'Roleplay').trim().toLowerCase();return mode==='gm'?'gm':mode==='private'?'private':'roleplay'}
 function patchChatPortrait(){
  const mode=chatMode();if(mode==='roleplay')return;
  const output=q('.rist-themed-chat-output');if(!output)return;const src=currentImage();
  let portrait=q('.rist-themed-chat-portrait',output);if(!portrait){portrait=document.createElement('div');portrait.className='rist-themed-chat-portrait';output.prepend(portrait)}
  portrait.replaceChildren();if(src){const img=document.createElement('img');img.src=src;img.alt='Player profile';portrait.appendChild(img)}else{const back=document.createElement('span');back.className='rist-chat-portrait-placeholder';back.textContent='?';portrait.appendChild(back)}
 }
 function scan(){patchSettings();patchChatPortrait()}
 let queued=false;function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;scan()})}
 document.addEventListener('rist:private-recipient-changed',patchChatPortrait);document.addEventListener('rist:profile-image-changed',patchChatPortrait);document.addEventListener('click',e=>{if(e.target.closest?.('.rist-chat-themed-tabs'))setTimeout(patchChatPortrait,0)});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{scan();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true})},{once:true});else{scan();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true})}
 window.RistProfileImage={imageFor,current:currentImage,get:currentImage};
})();