(() => {
  const pending = () => document.getElementById('pending-packet');
  const status = () => document.getElementById('pending-packet-status');
  const app = () => document.getElementById('app');
  let timer = 0;
  let dotsTimer = 0;
  let dots = 0;
  let baseStatus = 'Preparing packets';
  let running = false;
  let stopped = false;

  const overlay = pending();
  if (overlay && overlay.parentElement?.id === 'app') document.body.appendChild(overlay);

  const setStatus = (text) => {
    baseStatus = text.replace(/\.*$/, '');
    const node = status();
    if (node) node.textContent = `${baseStatus}${'.'.repeat(dots)}`;
  };

  const startDots = () => {
    clearInterval(dotsTimer);
    dotsTimer = window.setInterval(() => {
      dots = (dots + 1) % 4;
      const node = status();
      if (node) node.textContent = `${baseStatus}${'.'.repeat(dots)}`;
    }, 420);
  };

  const randomDelay = () => 15000 + Math.floor(Math.random() * 45001);
  const scheduleRetry = () => {
    if (stopped) return;
    clearTimeout(timer);
    timer = window.setTimeout(loadRequiredPackets, randomDelay());
  };

  const json = async (url, cache = 'no-store') => {
    const response = await fetch(url, { cache, credentials: 'same-origin' });
    if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
    return response.json();
  };

  const collectFrameworkFiles = (value, output) => {
    if (!value) return;
    if (Array.isArray(value)) {
      value.forEach(item => collectFrameworkFiles(item, output));
      return;
    }
    if (typeof value !== 'object') return;
    for (const [key, child] of Object.entries(value)) {
      if (/\.(?:dll|wasm|webcil|js|json|dat|pdb)$/i.test(key)) output.add(key);
      collectFrameworkFiles(child, output);
    }
  };

  const frameworkUrl = name => {
    if (/^(?:https?:)?\/\//i.test(name) || name.startsWith('./') || name.startsWith('/')) return name;
    return `./_framework/${name.replace(/^_framework\//, '')}`;
  };

  const waitForApp = async () => {
    const deadline = Date.now() + 30000;
    while (Date.now() < deadline) {
      const root = app();
      if (root && root.children.length > 0) return true;
      await new Promise(resolve => setTimeout(resolve, 120));
    }
    return false;
  };

  const fetchAll = async urls => {
    let loaded = 0;
    const total = urls.length;
    setStatus(`Receiving ${loaded} of ${total} items`);
    let cursor = 0;
    const workers = Array.from({ length: Math.min(4, Math.max(1, total)) }, async () => {
      while (cursor < total) {
        const index = cursor++;
        const url = urls[index];
        const response = await fetch(url, { cache: 'force-cache', credentials: 'same-origin' });
        if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
        await response.arrayBuffer();
        loaded += 1;
        setStatus(`Receiving ${loaded} of ${total} items`);
      }
    });
    await Promise.all(workers);
    return total;
  };

  async function loadRequiredPackets() {
    if (running || stopped) return;
    running = true;
    if (!navigator.onLine) {
      setStatus('Offline — waiting for connection');
      running = false;
      scheduleRetry();
      return;
    }

    try {
      setStatus('Counting required items');
      const config = await json(`./data/asset-config.json?packet=${Date.now()}`);
      const boot = await json(`./_framework/blazor.boot.json?packet=${Date.now()}`);
      const framework = new Set();
      collectFrameworkFiles(boot.resources || boot, framework);

      const urls = new Set([
        './data/asset-config.json',
        './data/atlas-public.json',
        './data/cards-public.json',
        './data/maps/index.json'
      ]);
      framework.forEach(name => urls.add(frameworkUrl(name)));

      const manifestUrl = config.worldMapManifestUrl;
      if (manifestUrl) {
        urls.add(`./${manifestUrl.replace(/^\.\//, '')}`);
        const manifest = await json(`./${manifestUrl.replace(/^\.\//, '')}?packet=${Date.now()}`);
        for (const tile of manifest.tiles || []) {
          if (tile?.image) urls.add(`./${String(tile.image).replace(/^\.\//, '')}`);
        }
      }

      const list = [...urls];
      const total = await fetchAll(list);
      setStatus(`${total} of ${total} items ready — opening RIST WORLD`);
      const ready = await waitForApp();
      if (!ready) throw new Error('App did not finish starting');
      stopped = true;
      clearTimeout(timer);
      clearInterval(dotsTimer);
      pending()?.remove();
    } catch (error) {
      console.warn('RIST packet gate:', error);
      setStatus(navigator.onLine ? 'Waiting for required items' : 'Offline — waiting for connection');
      scheduleRetry();
    } finally {
      running = false;
    }
  }

  window.addEventListener('offline', () => setStatus('Offline — waiting for connection'));
  window.addEventListener('online', () => {
    clearTimeout(timer);
    timer = window.setTimeout(loadRequiredPackets, 800);
  });

  startDots();
  loadRequiredPackets();
})();
