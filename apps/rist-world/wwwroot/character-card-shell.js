(() => {
  const ICONS = [
    ['Profile','profile'],
    ['Defense','defense'],
    ['Records','records'],
    ['Equipment','equipment'],
    ['Linked','linked']
  ];

  function build(sheet){
    if (!sheet || sheet.querySelector(':scope > .character-card-shell')) return;

    const shell = document.createElement('div');
    shell.className = 'character-card-shell';
    shell.setAttribute('aria-label','Character card design prototype');

    shell.innerHTML = `
      <div class="ccs-topbar">
        <div class="ccs-back" aria-hidden="true"></div>
        <div class="ccs-titleplate"></div>
        <div class="ccs-help" aria-hidden="true"></div>
        <button class="ccs-close" type="button" aria-label="Close character card"></button>
      </div>

      <div class="ccs-identity">
        <div class="ccs-portrait-frame"><div class="ccs-portrait-inner"></div></div>
        <div class="ccs-nameplate"></div>
      </div>

      <div class="ccs-symbol-row">
        <div class="ccs-small-medallion ccs-symbol-a"></div>
        <div class="ccs-small-medallion ccs-symbol-b"></div>
        <div class="ccs-small-medallion ccs-symbol-c"></div>
        <div class="ccs-small-medallion ccs-symbol-d"></div>
        <div class="ccs-small-medallion ccs-symbol-e"></div>
      </div>

      <div class="ccs-card-grid">
        <div class="ccs-mini-card"><div class="ccs-mini-title"></div><div class="ccs-mini-circle"></div><div class="ccs-mini-dots"><i></i><i></i><i></i></div></div>
        <div class="ccs-mini-card"><div class="ccs-mini-title"></div><div class="ccs-mini-circle"></div><div class="ccs-mini-dots"><i></i><i></i><i></i></div></div>
        <div class="ccs-mini-card"><div class="ccs-mini-title"></div><div class="ccs-mini-circle"></div><div class="ccs-mini-dots"><i></i><i></i><i></i></div></div>
        <div class="ccs-mini-card"><div class="ccs-mini-title"></div><div class="ccs-mini-circle"></div><div class="ccs-mini-dots"><i></i><i></i><i></i></div></div>
        <div class="ccs-mini-card"><div class="ccs-mini-title"></div><div class="ccs-mini-circle"></div><div class="ccs-mini-dots"><i></i><i></i><i></i></div></div>
        <div class="ccs-mini-card"><div class="ccs-mini-title"></div><div class="ccs-mini-circle"></div><div class="ccs-mini-dots"><i></i><i></i><i></i></div></div>
      </div>

      <div class="ccs-lower-bars">
        <div class="ccs-meter"><button class="ccs-minus" type="button" aria-label="Decrease"></button><div class="ccs-meter-track"><i></i><i></i><i></i><i></i><i></i></div><button class="ccs-plus" type="button" aria-label="Increase"></button></div>
        <div class="ccs-meter"><button class="ccs-minus" type="button" aria-label="Decrease"></button><div class="ccs-meter-track"><i></i><i></i><i></i><i></i><i></i></div><button class="ccs-plus" type="button" aria-label="Increase"></button></div>
      </div>

      <nav class="ccs-nav" aria-label="Character card sections">
        ${ICONS.map(([label,key],i)=>`<button type="button" class="ccs-nav-button ${i===0?'active':''}" data-key="${key}" aria-label="${label}"><span class="ccs-nav-icon ${key}"></span></button>`).join('')}
      </nav>`;

    const close = shell.querySelector('.ccs-close');
    close?.addEventListener('click',()=>{
      const original = sheet.querySelector('.exact-sheet-toolbar button:last-child');
      if (original) original.click();
    });

    shell.querySelectorAll('.ccs-nav-button').forEach(btn=>{
      btn.addEventListener('click',()=>{
        shell.querySelectorAll('.ccs-nav-button').forEach(x=>x.classList.remove('active'));
        btn.classList.add('active');
      });
    });

    sheet.appendChild(shell);
  }

  function decorate(){
    document.querySelectorAll('.character-mixer.universal-sheet').forEach(build);
  }

  const observer = new MutationObserver(decorate);
  observer.observe(document.body,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',decorate);
  requestAnimationFrame(decorate);
})();
