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

  function moveTo(nav, screen, target) {
    let guard = 0;
    const step = () => {
      const nowScreen = document.querySelector('.character-mixer.universal-sheet .exact-sheet-screen');
      const nowNav = document.querySelector('.character-mixer.universal-sheet .exact-page-arrows');
      if (!nowScreen || !nowNav || guard++ > 8) return;
      const now = currentIndex(nowScreen);
      if (now === target) {
        decorate();
        return;
      }
      const next = nowNav.querySelector(':scope > .next');
      if (!next) return;
      next.click();
      requestAnimationFrame(step);
    };
    step();
  }

  function decorate() {
    const sheet = document.querySelector('.character-mixer.universal-sheet');
    if (!sheet) return;
    const screen = sheet.querySelector('.exact-sheet-screen');
    const nav = sheet.querySelector('.exact-page-arrows');
    if (!screen || !nav) return;

    nav.querySelectorAll('.layer-nav-button').forEach(x => x.remove());
    const active = currentIndex(screen);

    views.forEach((view, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `layer-nav-button${index === active ? ' active' : ''}`;
      button.setAttribute('aria-label', view.label);
      button.title = view.label;
      button.innerHTML = `<span aria-hidden="true">${view.glyph}</span>`;
      button.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        moveTo(nav, screen, index);
      });
      nav.appendChild(button);
    });
  }

  const observer = new MutationObserver(() => requestAnimationFrame(decorate));
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
  document.addEventListener('DOMContentLoaded', decorate);
  requestAnimationFrame(decorate);
})();
