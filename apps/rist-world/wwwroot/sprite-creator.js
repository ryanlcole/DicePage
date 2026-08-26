(()=>{
 function openSpriteCreator(){
  const library=document.querySelector('#card-library');if(!library)return;
  const create=[...library.querySelectorAll('.card-library-tools button')].find(b=>/create custom card/i.test(b.textContent||''));
  if(!create)return;create.click();
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const modal=document.querySelector('.custom-card-editor-modal');if(!modal)return;
    const title=modal.querySelector('#custom-card-title');if(title)title.textContent='Create sprite';
    const labels=[...modal.querySelectorAll('label')];
    const findLabel=text=>labels.find(l=>(l.childNodes[0]?.textContent||l.textContent||'').trim().toLowerCase().startsWith(text));
    const lib=findLabel('library')?.querySelector('input');
    const type=findLabel('type')?.querySelector('input,select');
    const folder=findLabel('folder path')?.querySelector('input');
    if(lib){lib.value='Universal';lib.dispatchEvent(new Event('change',{bubbles:true}));}
    if(type){type.value='Sprite';type.dispatchEvent(new Event('change',{bubbles:true}));}
    if(folder){folder.value='Sprites > Custom';folder.dispatchEvent(new Event('change',{bubbles:true}));}
    const save=modal.querySelector('.custom-card-save');if(save)save.textContent='Create sprite';
  }));
 }
 function decorate(){
  const tools=document.querySelector('#card-library .card-library-tools');if(!tools||tools.querySelector('.sprite-create-action'))return;
  const b=document.createElement('button');b.type='button';b.className='sprite-create-action';b.textContent='Create sprite';b.addEventListener('click',openSpriteCreator);
  const first=tools.querySelector('button');first?.insertAdjacentElement('afterend',b);
 }
 const mo=new MutationObserver(decorate);mo.observe(document.documentElement,{subtree:true,childList:true});document.addEventListener('DOMContentLoaded',decorate);requestAnimationFrame(decorate);
})();
