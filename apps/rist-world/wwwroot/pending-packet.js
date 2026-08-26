(() => {
  const overlay = document.getElementById('pending-packet');
  const status = document.getElementById('pending-packet-status');
  const app = document.getElementById('app');
  if (overlay && overlay.parentElement === app) document.body.appendChild(overlay);

  let dots = 0;
  let base = 'Starting RIST WORLD';
  let expected = 0;
  let seen = 0;
  let hidden = false;
  const resources = new Set();

  const paint = () => {
    if (!status || hidden) return;
    const count = expected > 0 ? `${Math.min(seen, expected)} of ${expected} items · ` : '';
    status.textContent = `${count}${base}${'.'.repeat(dots)}`;
  };
  const set = text => { base = text; paint(); };
  const tick = setInterval(() => { dots = (dots + 1) % 4; paint(); }, 420);

  // Count resources the browser is ACTUALLY loading. Never issue duplicate HEAD
  // requests: Pending Packet is a monitor, not a second downloader.
  const note = name => {
    if (!name || resources.has(name)) return;
    resources.add(name);
    seen = resources.size;
    paint();
  };
  try {
    performance.getEntriesByType('resource').forEach(entry => note(entry.name));
    const observer = new PerformanceObserver(list => list.getEntries().forEach(entry => note(entry.name)));
    observer.observe({ type: 'resource', buffered: true });
  } catch { /* older browser: status still works */ }

  // Boot JSON is tiny and usually requested by Blazor immediately. Reading it
  // from cache lets us show an expected count without gating application start.
  fetch('./_framework/blazor.boot.json', { cache: 'force-cache', credentials: 'same-origin' })
    .then(r => r.ok ? r.json() : null)
    .then(boot => {
      if (!boot) return;
      const names = new Set();
      const walk = value => {
        if (!value) return;
        if (Array.isArray(value)) { value.forEach(walk); return; }
        if (typeof value !== 'object') return;
        for (const [key, child] of Object.entries(value)) {
          if (/\.(?:dll|wasm|webcil|js|json|dat)$/i.test(key)) names.add(key);
          walk(child);
        }
      };
      walk(boot.resources || boot);
      // Include the document/shell itself. Optional libraries/maps are deliberately
      // excluded because they are viewport-loaded later.
      expected = Math.max(expected, names.size + 1);
      set('Loading application');
    })
    .catch(() => set(navigator.onLine ? 'Connecting' : 'Offline — waiting for connection'));

  const finish = () => {
    if (hidden) return;
    hidden = true;
    clearInterval(tick);
    if (overlay) overlay.remove();
    window.dispatchEvent(new CustomEvent('rist:app-ready'));
  };

  // Blazor replaces the placeholder contents when the first real render lands.
  // That is the moment the user can use the app; optional assets continue to
  // stream afterward through their own viewport loaders.
  const usable = () => {
    if (!app) return false;
    return app.children.length > 0 || (app.textContent || '').trim().length > 0;
  };
  const mutation = new MutationObserver(() => {
    if (usable()) { mutation.disconnect(); finish(); }
  });
  if (app) mutation.observe(app, { childList: true, subtree: true, characterData: true });

  addEventListener('offline', () => set('Offline — waiting for connection'));
  addEventListener('online', () => set('Connecting'));

  window.ristPendingPacket = {
    status: set,
    ready: finish,
    setExpected: total => { expected = Math.max(0, Number(total) || 0); paint(); }
  };

  paint();
})();
