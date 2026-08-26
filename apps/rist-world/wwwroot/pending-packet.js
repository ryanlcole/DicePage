(() => {
  const pending = () => document.getElementById('pending-packet');
  const status = () => document.getElementById('pending-packet-status');
  let timer = 0;
  let dotsTimer = 0;
  let dots = 0;
  let baseStatus = 'Preparing packets';
  let running = false;
  let stopped = false;

  const overlay = pending();
  if (overlay && overlay.parentElement?.id === 'app') document.body.appendChild(overlay);

  const setStatus = text => {
    baseStatus = String(text).replace(/\.*$/, '');
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
    timer = window.setTimeout(checkRequiredPackets, randomDelay());
  };

  const json = async url => {
    const response = await fetch(url, { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
    return response.json();
  };

  const localUrl = value => {
    const text = String(value || '');
    if (!text) return '';
    if (/^(?:https?:)?\/\//i.test(text) || text.startsWith('/') || text.startsWith('./')) return text;
    return `./${text}`;
  };

  const collectFrameworkFiles = (value, output) => {
    if (!value) return;
    if (Array.isArray(value)) { value.forEach(item => collectFrameworkFiles(item, output)); return; }
    if (typeof value !== 'object') return;
    for (const [key, child] of Object.entries(value)) {
      if (/\.(?:dll|wasm|webcil|js|json|dat)$/i.test(key)) output.add(key);
      collectFrameworkFiles(child, output);
    }
  };

  const frameworkUrl = name => /^(?:https?:)?\/\//i.test(name) || name.startsWith('./') || name.startsWith('/')
    ? name
    : `./_framework/${name.replace(/^_framework\//, '')}`;

  const waitForApp = async () => {
    const deadline = Date.now() + 45000;
    while (Date.now() < deadline) {
      const root = document.getElementById('app');
      if (root && root.children.length > 0) return true;
      await new Promise(resolve => setTimeout(resolve, 150));
    }
    return false;
  };

  const available = async url => {
    let response = await fetch(url, { method: 'HEAD', cache: 'no-store', credentials: 'same-origin' });
    if (response.ok) return true;
    if (response.status === 405) {
      response = await fetch(url, { method: 'GET', cache: 'no-store', credentials: 'same-origin', headers: { Range: 'bytes=0-0' } });
      return response.ok || response.status === 206;
    }
    return false;
  };

  const verifyAll = async urls => {
    let ready = 0;
    const total = urls.length;
    let cursor = 0;
    setStatus(`${ready} of ${total} items ready`);
    const workers = Array.from({ length: Math.min(6, Math.max(1, total)) }, async () => {
      while (cursor < total) {
        const url = urls[cursor++];
        if (!await available(url)) throw new Error(`${url} unavailable`);
        ready += 1;
        setStatus(`${ready} of ${total} items ready`);
      }
    });
    await Promise.all(workers);
    return total;
  };

  async function checkRequiredPackets() {
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
      const stamp = Date.now();
      const [config, boot, atlas] = await Promise.all([
        json(`./data/asset-config.json?packet=${stamp}`),
        json(`./_framework/blazor.boot.json?packet=${stamp}`),
        json(`./data/atlas-public.json?packet=${stamp}`)
      ]);
      const framework = new Set();
      collectFrameworkFiles(boot.resources || boot, framework);
      const urls = new Set([
        './data/asset-config.json',
        './data/atlas-public.json',
        './data/cards-public.json'
      ]);
      framework.forEach(name => urls.add(frameworkUrl(name)));
      for (const asset of Array.isArray(atlas) ? atlas : []) {
        const url = localUrl(asset?.image);
        if (url) urls.add(url);
      }
      const total = await verifyAll([...urls]);
      setStatus(`${total} of ${total} items ready — opening RIST WORLD`);
      if (!await waitForApp()) throw new Error('App did not finish starting');
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
    timer = window.setTimeout(checkRequiredPackets, 800);
  });

  startDots();
  checkRequiredPackets();
})();
