(() => {
  const views = [
    { key: 'profile', label: 'Profile', glyph: '◉' },
    { key: 'entries', label: 'Entries', glyph: '✦' },
    { key: 'equipment', label: 'Equipment', glyph: '⚒' },
    { key: 'linked', label: 'Linked', glyph: '⛓' },
    { key: 'spellbook', label: 'Cards', glyph: '▣' }
  ];

  function currentIndex(screen) {
    const cls = Array.from(screen.classList).find(x => x.startsWith('exact-') && x !== 'exact-sheet-screen');
    if (!cls) return 0;
    const key = cls.slice(6);
    const i = views.findIndex(v => v.key === key);
    return i < 0 ? 0 : i;
  }

  function hiddenNav(sheet) {
    return sheet.querySelector('.exact-page-arrows');
  }

  function syncActive(sheet) {
    const screen = sheet.querySelector('.exact-sheet-screen');
    const nav = sheet.querySelector('.universal-layer-nav');
    if (!screen || !nav) return;
    const active = currentIndex(screen);
    nav.querySelectorAll('.layer-nav-button').forEach((button, index) => {
      button.classList.toggle('active', index === active);
      button.setAttribute('aria-current', index === active ? 'page' : 'false');
    });
  }

  function moveTo(target) {
    let guard = 0;
    const step = () => {
      const sheet = document.querySelector('.character-mixer.universal-sheet');
      const screen = sheet?.querySelector('.exact-sheet-screen');
      const sourceNav = sheet ? hiddenNav(sheet) : null;
      if (!sheet || !screen || !sourceNav || guard++ > 8) return;

      const now = currentIndex(screen);
      if (now === target) {
        syncActive(sheet);
        return;
      }

      const next = sourceNav.querySelector(':scope > .next');
      if (!next) return;
      next.click();
      setTimeout(step, 0);
    };
    step();
  }

  function buildNav(sheet) {
    let nav = sheet.querySelector(':scope > .universal-layer-nav');
    if (nav) return nav;

    nav = document.createElement('nav');
    nav.className = 'universal-layer-nav';
    nav.setAttribute('aria-label', 'Character sheet layers');

    views.forEach((view, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'layer-nav-button';
      button.setAttribute('aria-label', view.label);
      button.title = view.label;
      button.innerHTML = `<span aria-hidden="true">${view.glyph}</span>`;
      button.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        moveTo(index);
      });
      nav.appendChild(button);
    });

    sheet.appendChild(nav);
    return nav;
  }

  function decorate() {
    const sheet = document.querySelector('.character-mixer.universal-sheet');
    if (!sheet) return;
    const screen = sheet.querySelector('.exact-sheet-screen');
    const sourceNav = hiddenNav(sheet);
    if (!screen || !sourceNav) return;

    buildNav(sheet);
    syncActive(sheet);
  }

  let queued = false;
  const observer = new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      decorate();
    });
  });

  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
  document.addEventListener('DOMContentLoaded', decorate);
  requestAnimationFrame(decorate);
})();
