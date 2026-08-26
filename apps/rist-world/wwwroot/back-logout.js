(()=>{
  let installed=false;
  const cleanUrl=()=>location.pathname+location.search+location.hash;

  async function logoutFromBack(){
    const token=sessionStorage.getItem('rist.session');
    if(!token)return;
    try{
      const config=await fetch('auth-config.json',{cache:'no-store'}).then(r=>r.ok?r.json():null);
      const base=config?.apiBaseUrl||config?.ApiBaseUrl||'';
      if(base){
        await fetch(base.replace(/\/$/,'')+'/auth/logout',{
          method:'POST',
          headers:{Authorization:'Bearer '+token}
        }).catch(()=>{});
      }
    }catch{}
    try{window.ristAuth?.clearSession?.();}catch{}
    history.replaceState({ristLoggedOut:true},'',cleanUrl());
    location.reload();
  }

  function install(){
    if(installed||!sessionStorage.getItem('rist.session'))return;
    installed=true;
    history.pushState({ristBackLogoutGuard:true},'',cleanUrl());
    addEventListener('popstate',()=>{
      if(!sessionStorage.getItem('rist.session'))return;
      history.pushState({ristBackLogoutGuard:true},'',cleanUrl());
      void logoutFromBack();
    });
  }

  addEventListener('rist:app-ready',install,{once:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,0),{once:true});
  else setTimeout(install,0);
  setTimeout(install,1500);
})();
