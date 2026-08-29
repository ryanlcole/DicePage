(()=>{
  let installed=false;
  const cleanUrl=()=>location.pathname+location.search+location.hash;

  async function logoutFromBack(){
    const token=sessionStorage.getItem('rist.session');
    if(!token)return;
    try{
      const response=await fetch('auth-config.json',{cache:'no-store'});
      const config=response.ok?await response.json():null;
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

  install();
})();
