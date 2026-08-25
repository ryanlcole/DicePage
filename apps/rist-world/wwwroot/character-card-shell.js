(() => {
  const ICONS = [
    ['Profile','profile'],
    ['Defense','defense'],
    ['Records','records'],
    ['Equipment','equipment'],
    ['Linked','linked']
  ];

  function openPortraitEditor(sheet){
    const portraitButton = [...sheet.querySelectorAll('.identity-badge-meta button')]
      .find(button => button.textContent.trim().toLowerCase().includes('portrait'));
    if (portraitButton) {
      portraitButton.click();
      return;
    }

    const editButton = [...sheet.querySelectorAll('.exact-sheet-toolbar button')]
      .find(button => button.textContent.trim().toLowerCase() === 'edit');
    if (editButton) {
      editButton.click();
      requestAnimationFrame(() => {
        const editorButton = [...sheet.querySelectorAll('.identity-badge-meta button')]
          .find(button => button.textContent.trim().toLowerCase().includes('portrait'));
        editorButton?.click();
      });
    }
  }

  function syncPortrait(sheet, shell){
    const source = sheet.querySelector('.exact-portrait.character-portrait img');
    const target = shell.querySelector('.ccs-portrait-photo');
    const empty = shell.querySelector('.ccs-portrait-empty');
    if (!target || !empty) return;

    const src = source?.getAttribute('src') || '';
    if (src) {
      if (target.getAttribute('src') !== src) target.setAttribute('src', src);
      target.hidden = false;
      empty.hidden = true;
    } else {
      target.removeAttribute('src');
      target.hidden = true;
      empty.hidden = false;
    }
  }

  function build(sheet){
    if (!sheet || sheet.querySelector(':scope > .character-card-shell')) return;

    const shell = document.createElement('div');
    shell.className = 'character-card-shell';
    shell.setAttribute('aria-label','Universal character card');

    shell.innerHTML = `
      <div class="ccs-topbar">
        <div class="ccs-back" aria-hidden="true"></div>
        <div class="ccs-titleplate"></div>
        <div class="ccs-help" aria-hidden="true"></div>
        <button class="ccs-close" type="button" aria-label="Close character card"></button>
      </div>

      <div class="ccs-identity">
        <button class="ccs-portrait-frame" type="button" aria-label="Edit character portrait">
          <div class="ccs-portrait-inner">
            <img class="ccs-portrait-photo" alt="Character portrait" hidden>
            <span class="ccs-portrait-empty" aria-hidden="true"></span>
          </div>
          <span class="ccs-portrait-edit" aria-hidden="true">✎</span>
        </button>
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

    shell.querySelector('.ccs-close')?.addEventListener('click',()=>{
      const original = sheet.querySelector('.exact-sheet-toolbar button:last-child');
      original?.click();
    });

    shell.querySelector('.ccs-portrait-frame')?.addEventListener('click',()=>openPortraitEditor(sheet));

    shell.querySelectorAll('.ccs-nav-button').forEach(btn=>{
      btn.addEventListener('click',()=>{
        shell.querySelectorAll('.ccs-nav-button').forEach(x=>x.classList.remove('active'));
        btn.classList.add('active');
      });
    });

    sheet.appendChild(shell);
    syncPortrait(sheet, shell);
  }

  function decorate(){
    document.querySelectorAll('.character-mixer.universal-sheet').forEach(sheet=>{
      build(sheet);
      const shell = sheet.querySelector(':scope > .character-card-shell');
      if (shell) syncPortrait(sheet, shell);
    });
  }

  const observer = new MutationObserver(decorate);
  observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
  document.addEventListener('DOMContentLoaded',decorate);
  requestAnimationFrame(decorate);
})();
