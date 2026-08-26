(() => {
  const pending = () => document.getElementById('pending-packet');
  const status = () => document.getElementById('pending-packet-status');
  const startedAt = Date.now();
  let bootFailed = false;
  let timer = 0;
  let stopped = false;

  const setStatus = (text) => {
    const node = status();
    if (node) node.textContent = text;
  };

  const isPending = () => !!pending();
  const randomDelay = () => 15000 + Math.floor(Math.random() * 45001);

  const schedule = () => {
    if (stopped || !isPending()) return;
    clearTimeout(timer);
    timer = window.setTimeout(probe, randomDelay());
  };

  const probe = async () => {
    if (stopped || !isPending()) return;

    if (!navigator.onLine) {
      setStatus('Offline — waiting for connection…');
      schedule();
      return;
    }

    const stalled = Date.now() - startedAt > 90000;
    if (bootFailed || stalled) setStatus('Waiting for packet…');

    try {
      const response = await fetch(`./data/asset-config.json?packet=${Date.now()}`, {
        cache: 'no-store',
        credentials: 'same-origin'
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      if (bootFailed || stalled) {
        setStatus('Packet ready — opening…');
        stopped = true;
        clearTimeout(timer);
        window.setTimeout(() => location.reload(), 350);
        return;
      }
    } catch {
      bootFailed = true;
      setStatus(navigator.onLine ? 'Waiting for packet…' : 'Offline — waiting for connection…');
    }

    schedule();
  };

  window.addEventListener('offline', () => {
    if (isPending()) setStatus('Offline — waiting for connection…');
  });

  window.addEventListener('online', () => {
    if (!isPending()) return;
    setStatus('Connecting…');
    clearTimeout(timer);
    timer = window.setTimeout(probe, 1200);
  });

  window.addEventListener('error', (event) => {
    if (!isPending()) return;
    const target = event.target;
    if (target && target !== window && (target.tagName === 'SCRIPT' || target.tagName === 'LINK')) {
      bootFailed = true;
      setStatus('Waiting for packet…');
    }
  }, true);

  window.addEventListener('unhandledrejection', () => {
    if (!isPending()) return;
    bootFailed = true;
    setStatus('Waiting for packet…');
  });

  const observer = new MutationObserver(() => {
    if (!isPending()) {
      stopped = true;
      clearTimeout(timer);
      observer.disconnect();
    }
  });

  const app = document.getElementById('app');
  if (app) observer.observe(app, { childList: true, subtree: true });

  if (!navigator.onLine) setStatus('Offline — waiting for connection…');
  schedule();
})();
