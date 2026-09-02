(()=>{
 'use strict';
 const KEY='rist.playerProfileImage.v1';
 const q=(s,r=document)=>r?.querySelector(s);
 let source='',zoom=1,x=50,y=50,queued=false;
 const saved=()=>localStorage.getItem(KEY)||'';
 function profileImage(){return saved()}
 function dispatch(){document.dispatchEvent(new CustomEvent('rist:profile-image-changed',{detail:{src:saved()}}))}
 function crop(dataUrl,z,cx,cy,size=512){
  return new Promise((resolve,reject)=>{
   const img=new Image();
   img.onload=()=>{
    const canvas=document.createElement('canvas');canvas.width=size;canvas.height=size;
    const ctx=canvas.getContext('2d');
    const scale=Math.max(size/img.naturalWidth,size/img.naturalHeight)*Math.max(1,Number(z)||1);
    const w=img.naturalWidth*scale,h=img.naturalHeight*scale;
    const maxX=Math.max(0,w-size),maxY=Math.max(0,h-size);
    const dx=-(maxX*(Number(cx)||50)/100),dy=-(maxY*(Number(cy)||50)/100);
    ctx.clearRect(0,0,size,size);ctx.drawImage(img,dx,dy,w,h);
    resolve(canvas.toDataURL('image/png'));
   };
   img.onerror=reject;img.src=dataUrl;
  });
 }
 function preview(host){
  const frame=q('[data-profile-image-preview]',host);if(!frame)return;
  frame.replaceChildren();
  const imgSrc=source||saved();
  if(imgSrc){const img=document.createElement('img');img.src=imgSrc;img.alt='Profile preview';img.style.transform=`scale(${zoom})`;img.style.transformOrigin=`${x}% ${y}%`;frame.appendChild(img)}
  else{const span=document.createElement('span');span.textContent='?';frame.appendChild(span)}
 }
 function inject(){
  const panel=q('.rist-start-panel');if(!panel)return;
  const sub=q('.rist-start-sub',panel);if(!sub)return;
  const heading=q('h2',sub);if(!heading||heading.textContent.trim()!=='Account')return;
  if(q('[data-profile-image-editor]',sub))return;
  const block=document.createElement('section');block.className='rist-profile-image-editor';block.dataset.profileImageEditor='1';
  block.innerHTML=`<h3>Profile image</h3><div class="rist-profile-image-work"><div class="rist-profile-image-preview" data-profile-image-preview></div><div class="rist-profile-image-controls"><label>Image<input type="file" accept="image/png,image/jpeg,image/webp" data-profile-image-file></label><label>Zoom<input type="range" min="1" max="3" step="0.05" value="1" data-profile-image-zoom></label><label>Left / right<input type="range" min="0" max="100" value="50" data-profile-image-x></label><label>Up / down<input type="range" min="0" max="100" value="50" data-profile-image-y></label><div><button type="button" data-profile-image-apply>Apply</button><button type="button" data-profile-image-remove>Remove</button></div></div></div><p class="rist-start-note">GM and Private chat use this player profile image. Roleplay uses the active character portrait.</p>`;
  const account=q('.rist-account-profile',sub);(account||heading).insertAdjacentElement('afterend',block);
  source=saved();zoom=1;x=50;y=50;preview(block);
  q('[data-profile-image-file]',block).addEventListener('change',event=>{const file=event.target.files?.[0];if(!file)return;const reader=new FileReader();reader.onload=()=>{source=String(reader.result||'');zoom=1;x=50;y=50;preview(block)};reader.readAsDataURL(file)});
  q('[data-profile-image-zoom]',block).addEventListener('input',event=>{zoom=Number(event.target.value)||1;preview(block)});
  q('[data-profile-image-x]',block).addEventListener('input',event=>{x=Number(event.target.value)||50;preview(block)});
  q('[data-profile-image-y]',block).addEventListener('input',event=>{y=Number(event.target.value)||50;preview(block)});
  q('[data-profile-image-apply]',block).addEventListener('click',async()=>{if(!source)return;try{const result=typeof window.ristCropPortrait==='function'?await window.ristCropPortrait(source,zoom,x,y,512):await crop(source,zoom,x,y,512);localStorage.setItem(KEY,result);source=result;zoom=1;x=50;y=50;preview(block);dispatch()}catch{}});
  q('[data-profile-image-remove]',block).addEventListener('click',()=>{localStorage.removeItem(KEY);source='';zoom=1;x=50;y=50;preview(block);dispatch()});
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;inject()})}
 function start(){inject();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});}
 window.RistProfileImage={get:profileImage};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();