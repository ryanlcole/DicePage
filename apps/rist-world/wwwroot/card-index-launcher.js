let observer=null;
let button=null;
let dotnet=null;

function mount(){
 const primary=document.querySelector('.launcher-hub .launcher-primary');
 if(!primary){button?.remove();button=null;return;}
 if(button?.isConnected)return;
 button=document.createElement('button');
 button.type='button';
 button.className='launcher-card assets rist-card-index-launcher';
 button.innerHTML='<span class="card-icon">▧</span><strong>CARD INDEX</strong><small>Your cards, library, store and custom card creator.</small>';
 button.addEventListener('click',()=>dotnet?.invokeMethodAsync('OpenCardIndexFromJs').catch(()=>{}));
 primary.appendChild(button);
}

export function attach(ref){
 dotnet=ref;
 mount();
 observer=new MutationObserver(()=>mount());
 observer.observe(document.body,{childList:true,subtree:true});
 return {dispose(){observer?.disconnect();observer=null;button?.remove();button=null;dotnet=null;}};
}
