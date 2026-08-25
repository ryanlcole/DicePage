(() => {
  const ICONS = [
    ['Profile','profile'],
    ['Defense','defense'],
    ['Records','records'],
    ['Equipment','equipment'],
    ['Linked','linked']
  ];

  const PAGE_FIELDS = {
    profile:[['Character name','Name'],['Identity / concept','Concept'],['Description','Description'],['Profile notes','Notes']],
    defense:[['Defense','Defense'],['Resistances','Resistances'],['Conditions','Conditions'],['Defense notes','Notes']],
    records:[['History','History'],['Goals','Goals'],['Contacts / factions','Contacts'],['Record notes','Notes']],
    equipment:[['Loadout','Loadout'],['Containers','Containers'],['Currency / resources','Resources'],['Inventory notes','Notes']],
    linked:[['Linked asset','Linked'],['Locations','Locations'],['Relationships','Relationships'],['Linked notes','Notes']]
  };

  const DEFAULT_THEME = {
    font:'#5b4932',
    colors:['#f7efdf','#ead9b8','#bfe8ff','#ffffff'],
    colorCount:1,
    pattern:'soft',
    frame:'gold',
    whitespace:'default'
  };

  const METALS = {
    gold:'#b38a48', silver:'#9e9e9e', bronze:'#8f6337', obsidian:'#2b2a31', none:'transparent'
  };

  function cloneTheme(theme){return {...theme,colors:[...(theme.colors||DEFAULT_THEME.colors)]};}

  function openPortraitEditor(sheet){
    const portraitButton = [...sheet.querySelectorAll('.identity-badge-meta button')]
      .find(button => button.textContent.trim().toLowerCase().includes('portrait'));
    if (portraitButton) { portraitButton.click(); return; }
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
      target.hidden = false; empty.hidden = true;
    } else {
      target.removeAttribute('src'); target.hidden = true; empty.hidden = false;
    }
  }

  function hexToRgb(hex){
    const clean=(hex||'#000000').replace('#','');
    const full=clean.length===3?clean.split('').map(x=>x+x).join(''):clean.padEnd(6,'0');
    return [0,2,4].map(i=>parseInt(full.slice(i,i+2),16)/255);
  }
  function rgbToHex(rgb){return '#'+rgb.map(v=>Math.round(Math.max(0,Math.min(1,v))*255).toString(16).padStart(2,'0')).join('');}
  function additiveLight(colors){
    const out=[0,0,0];
    colors.forEach(hex=>{const c=hexToRgb(hex);for(let i=0;i<3;i++)out[i]=1-(1-out[i])*(1-c[i]);});
    return rgbToHex(out);
  }
  function tint(hex, amount){const c=hexToRgb(hex);return rgbToHex(c.map(v=>v+(1-v)*amount));}
  function shade(hex, amount){const c=hexToRgb(hex);return rgbToHex(c.map(v=>v*(1-amount)));}

  function loadTheme(){
    try { const stored=JSON.parse(localStorage.getItem('rist-character-theme')||'{}'); return cloneTheme({...DEFAULT_THEME,...stored,colors:stored.colors||DEFAULT_THEME.colors}); }
    catch { return cloneTheme(DEFAULT_THEME); }
  }
  function saveTheme(theme){try{localStorage.setItem('rist-character-theme',JSON.stringify(theme));}catch{}}

  function themeGradient(theme){
    const colors=theme.colors.slice(0,Math.max(1,theme.colorCount));
    const light=additiveLight(colors);
    const c=colors.length===1?[colors[0],tint(colors[0],.38)]:colors;
    switch(theme.pattern){
      case 'radial': return `radial-gradient(circle at 38% 32%, ${tint(light,.38)} 0%, ${c[0]} 35%, ${c[Math.min(1,c.length-1)]} 68%, ${shade(light,.28)} 100%)`;
      case 'diagonal': return `linear-gradient(135deg, ${c.map((x,i)=>`${x} ${Math.round(i*100/Math.max(1,c.length-1))}%`).join(',')})`;
      case 'bands': return `linear-gradient(90deg, ${c.map((x,i)=>`${x} ${Math.round(i*100/Math.max(1,c.length-1))}%`).join(',')})`;
      case 'facets': {
        const a=c[0],b=c[Math.min(1,c.length-1)],d=c[Math.min(2,c.length-1)],e=c[Math.min(3,c.length-1)];
        return `linear-gradient(145deg,transparent 0 28%,${tint(light,.32)}55 28% 40%,transparent 40%),linear-gradient(35deg,${a} 0 25%,${b} 25% 50%,${d} 50% 75%,${e} 75%)`;
      }
      default: return `linear-gradient(115deg, ${c.map((x,i)=>`${x} ${Math.round(i*100/Math.max(1,c.length-1))}%`).join(',')})`;
    }
  }

  function applyTheme(shell,theme){
    const active=theme.colors.slice(0,Math.max(1,theme.colorCount));
    const light=additiveLight(active);
    const white=theme.whitespace==='white'?'#ffffff':theme.whitespace==='black'?'#101216':'#f7efdf';
    shell.style.setProperty('--font-color',theme.font);
    shell.style.setProperty('--gem-light',light);
    shell.style.setProperty('--gem-highlight',tint(light,.50));
    shell.style.setProperty('--gem-shadow',shade(light,.46));
    shell.style.setProperty('--frame-metal',METALS[theme.frame]||METALS.gold);
    shell.style.setProperty('--whitespace',white);
    shell.style.setProperty('--card-fill',themeGradient(theme));
    shell.dataset.whitespace=theme.whitespace;
  }

  function fieldStorageKey(key){return `rist-character-shell-field:${key}`;}
  function buildFields(page){
    return (PAGE_FIELDS[page]||[]).map(([label,key],i)=>`
      <label class="ccs-field ${i===2||i===3?'wide':''}"><span>${label}</span>${i>=2?`<textarea data-field-key="${page}.${key}" rows="2"></textarea>`:`<input data-field-key="${page}.${key}" type="text">`}</label>`).join('');
  }
  function loadFields(shell){
    shell.querySelectorAll('[data-field-key]').forEach(el=>{
      try{el.value=localStorage.getItem(fieldStorageKey(el.dataset.fieldKey))||'';}catch{}
      el.addEventListener('input',()=>{try{localStorage.setItem(fieldStorageKey(el.dataset.fieldKey),el.value);}catch{}});
    });
  }
  function renderPage(shell,key){
    shell.dataset.page=key; shell.querySelector('.ccs-page-fields').innerHTML=buildFields(key); loadFields(shell);
    shell.querySelectorAll('.ccs-nav-button').forEach(x=>x.classList.toggle('active',x.dataset.key===key));
  }

  function buildThemeEditor(shell){
    const modal=shell.querySelector('.ccs-theme-modal');
    const form=modal.querySelector('.ccs-theme-controls');
    let savedTheme=loadTheme();
    let draftTheme=cloneTheme(savedTheme);
    applyTheme(shell,savedTheme);

    const syncControls=()=>{
      form.querySelector('[name=font]').value=draftTheme.font;
      form.querySelector('[name=count]').value=draftTheme.colorCount;
      form.querySelector('[name=pattern]').value=draftTheme.pattern;
      form.querySelector('[name=frame]').value=draftTheme.frame;
      form.querySelectorAll('[data-gem-color]').forEach((input,i)=>{input.value=draftTheme.colors[i];input.closest('label').hidden=i>=draftTheme.colorCount;});
      form.querySelectorAll('[name=whitespace]').forEach(x=>x.checked=x.value===draftTheme.whitespace);
    };
    const preview=()=>{applyTheme(shell,draftTheme);syncControls();};
    const open=()=>{savedTheme=loadTheme();draftTheme=cloneTheme(savedTheme);syncControls();applyTheme(shell,draftTheme);modal.hidden=false;requestAnimationFrame(()=>{modal.querySelector('.ccs-theme-panel').scrollTop=0;});};
    const cancel=()=>{draftTheme=cloneTheme(savedTheme);applyTheme(shell,savedTheme);modal.hidden=true;};
    const apply=()=>{savedTheme=cloneTheme(draftTheme);saveTheme(savedTheme);applyTheme(shell,savedTheme);modal.hidden=true;};

    form.addEventListener('input',e=>{
      const t=e.target;
      if(t.name==='font')draftTheme.font=t.value;
      else if(t.name==='count')draftTheme.colorCount=Math.max(1,Math.min(4,Number(t.value)||1));
      else if(t.name==='pattern')draftTheme.pattern=t.value;
      else if(t.name==='frame')draftTheme.frame=t.value;
      else if(t.name==='whitespace')draftTheme.whitespace=t.value;
      else if(t.dataset.gemColor!==undefined)draftTheme.colors[Number(t.dataset.gemColor)]=t.value;
      preview();
    });
    form.addEventListener('change',e=>form.dispatchEvent(new Event('input',{bubbles:false})));
    modal.querySelector('.ccs-theme-close')?.addEventListener('click',cancel);
    modal.querySelector('.ccs-theme-cancel')?.addEventListener('click',cancel);
    modal.querySelector('.ccs-theme-apply')?.addEventListener('click',apply);
    modal.addEventListener('click',e=>{if(e.target===modal)cancel();});
    shell.querySelector('.ccs-theme-trigger')?.addEventListener('click',open);
    syncControls();
  }

  function build(sheet){
    if (!sheet || sheet.querySelector(':scope > .character-card-shell')) return;
    const shell=document.createElement('div');
    shell.className='character-card-shell'; shell.setAttribute('aria-label','Universal character card');
    shell.innerHTML=`
      <div class="ccs-topbar"><div class="ccs-back" aria-hidden="true"></div><div class="ccs-titleplate"></div><button class="ccs-theme-trigger" type="button" aria-label="Character sheet appearance"><img src="assets/ui/character-sheet/theme-wheel.jpeg" alt="" onerror="this.hidden=true"><span aria-hidden="true"></span></button><button class="ccs-close" type="button" aria-label="Close character card"></button></div>
      <div class="ccs-identity"><button class="ccs-portrait-frame" type="button" aria-label="Edit character portrait"><div class="ccs-portrait-inner"><img class="ccs-portrait-photo" alt="Character portrait" hidden><span class="ccs-portrait-empty" aria-hidden="true"></span></div><span class="ccs-portrait-edit" aria-hidden="true">✎</span></button><div class="ccs-nameplate"></div></div>
      <div class="ccs-page-fields"></div>
      <div class="ccs-symbol-row"><div class="ccs-small-medallion"></div><div class="ccs-small-medallion"></div><div class="ccs-small-medallion"></div><div class="ccs-small-medallion"></div><div class="ccs-small-medallion"></div></div>
      <div class="ccs-card-grid">${Array.from({length:6},()=>`<div class="ccs-mini-card"><div class="ccs-mini-title"></div><div class="ccs-mini-circle"></div><div class="ccs-mini-dots"><i></i><i></i><i></i></div></div>`).join('')}</div>
      <div class="ccs-lower-bars">${Array.from({length:2},()=>`<div class="ccs-meter"><button class="ccs-minus" type="button" aria-label="Decrease"></button><div class="ccs-meter-track"><i></i><i></i><i></i><i></i><i></i></div><button class="ccs-plus" type="button" aria-label="Increase"></button></div>`).join('')}</div>
      <nav class="ccs-nav" aria-label="Character card sections">${ICONS.map(([label,key],i)=>`<button type="button" class="ccs-nav-button ${i===0?'active':''}" data-key="${key}" aria-label="${label}"><span class="ccs-nav-icon ${key}"></span></button>`).join('')}</nav>
      <div class="ccs-theme-modal" hidden><section class="ccs-theme-panel" role="dialog" aria-modal="true" aria-label="Character sheet appearance"><header><strong>Appearance</strong><button class="ccs-theme-close" type="button" aria-label="Cancel appearance changes">×</button></header><div class="ccs-theme-wheel-large"><img src="assets/ui/character-sheet/theme-wheel.jpeg" alt="Color wheel" onerror="this.hidden=true"><span aria-hidden="true"></span></div><div class="ccs-theme-preview"><div class="ccs-preview-card"><span>Live preview</span><strong>Character Card</strong><p>Gemstone light passes through the selected colors.</p></div></div><div class="ccs-theme-controls"><label>Font color<input name="font" type="color"></label><label>Gem colors<select name="count"><option value="1">1 color</option><option value="2">2 colors</option><option value="3">3 colors</option><option value="4">4 colors</option></select></label><div class="ccs-color-picks">${[0,1,2,3].map(i=>`<label>Color ${i+1}<input data-gem-color="${i}" type="color"></label>`).join('')}</div><label>Fade pattern<select name="pattern"><option value="soft">Soft fade</option><option value="radial">Radiant center</option><option value="diagonal">Diagonal</option><option value="bands">Bands</option><option value="facets">Faceted</option></select></label><label>Object frames<select name="frame"><option value="gold">Gold</option><option value="silver">Silver</option><option value="bronze">Bronze</option><option value="obsidian">Obsidian</option><option value="none">None</option></select></label><fieldset class="ccs-whitespace"><legend>Whitespace / center</legend><label><input name="whitespace" type="radio" value="default">Default</label><label><input name="whitespace" type="radio" value="black">Black</label><label><input name="whitespace" type="radio" value="white">White</label></fieldset></div><footer class="ccs-theme-actions"><button class="ccs-theme-cancel" type="button">Cancel</button><button class="ccs-theme-apply" type="button">Apply</button></footer></section></div>`;

    shell.querySelector('.ccs-close')?.addEventListener('click',()=>sheet.querySelector('.exact-sheet-toolbar button:last-child')?.click());
    shell.querySelector('.ccs-portrait-frame')?.addEventListener('click',()=>openPortraitEditor(sheet));
    shell.querySelectorAll('.ccs-nav-button').forEach(btn=>btn.addEventListener('click',()=>renderPage(shell,btn.dataset.key)));
    sheet.appendChild(shell); renderPage(shell,'profile'); buildThemeEditor(shell); syncPortrait(sheet,shell);
  }

  function decorate(){document.querySelectorAll('.character-mixer.universal-sheet').forEach(sheet=>{build(sheet);const shell=sheet.querySelector(':scope > .character-card-shell');if(shell)syncPortrait(sheet,shell);});}
  const observer=new MutationObserver(decorate); observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
  document.addEventListener('DOMContentLoaded',decorate); requestAnimationFrame(decorate);
})();
