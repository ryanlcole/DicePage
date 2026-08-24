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

  function syncActive(nav, screen) {
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
      const nav = sheet?.querySelector('.exact-page-arrows');
      if (!screen || !nav || guard++ > 8) return;

      const now = currentIndex(screen);
      if (now === target) {
        syncActive(nav, screen);
        return;
      }

      const next = nav.querySelector(':scope > .next');
      if (!next) return;
      next.click();
      setTimeout(step, 0);
    };
    step();
  }

  function decorate() {
    const sheet = document.querySelector('.character-mixer.universal-sheet');
    if (!sheet) return;
    const screen = sheet.querySelector('.exact-sheet-screen');
    const nav = sheet.querySelector('.exact-page-arrows');
    if (!screen || !nav) return;

    let buttons = nav.querySelectorAll('.layer-nav-button');
    if (buttons.length !== views.length) {
      nav.querySelectorAll('.layer-nav-button').forEach(x => x.remove());

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
      buttons = nav.querySelectorAll('.layer-nav-button');
    }

    syncActive(nav, screen);
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
