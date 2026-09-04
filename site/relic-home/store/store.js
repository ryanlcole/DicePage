(() => {
  'use strict';

  const defaultCategories = ['All', 'Maps', 'Tiles', 'Tokens', 'Miniatures', 'Sprites', 'Cards', 'Scenery', 'Audio', 'Campaign Tools'];
  const state = { products: [], category: 'All', query: '', provenance: 'all', invitationsIssued: false };

  const grid = document.querySelector('[data-product-grid]');
  const empty = document.querySelector('[data-catalog-empty]');
  const error = document.querySelector('[data-catalog-error]');
  const count = document.querySelector('[data-catalog-count]');
  const categoryList = document.querySelector('[data-category-list]');
  const search = document.querySelector('[data-store-search]');
  const provenance = document.querySelector('[data-store-provenance]');
  const invitationState = document.querySelector('[data-invitation-state]');
  const inviteForm = document.querySelector('[data-creator-invite-form]');
  const inviteMessage = document.querySelector('[data-invite-message]');

  function safeText(value) {
    return String(value ?? '').trim();
  }

  function safePreviewUrl(value) {
    const source = safeText(value);
    if (!source) return '';
    try {
      const url = new URL(source, location.origin);
      if (url.origin === location.origin || url.protocol === 'https:') return url.href;
    } catch {}
    return '';
  }

  function formatPrice(product) {
    if (product.free === true) return 'Free';
    const cents = Number(product.priceCents);
    if (!Number.isFinite(cents) || cents < 0) return 'Not available';
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: safeText(product.currency) || 'USD'
    }).format(cents / 100);
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function productCard(product) {
    const card = element('article', 'product-card');
    const preview = element('div', 'product-preview');
    const previewUrl = safePreviewUrl(product.previewUrl);
    if (previewUrl) {
      const image = document.createElement('img');
      image.src = previewUrl;
      image.alt = safeText(product.previewAlt) || '';
      image.loading = 'lazy';
      preview.append(image);
    } else {
      preview.append(element('span', '', 'Preview pending'));
    }

    const body = element('div', 'product-body');
    const meta = element('div', 'product-meta');
    meta.append(
      element('span', '', safeText(product.category) || 'Asset pack'),
      element('span', '', safeText(product.provenanceLabel) || 'Source disclosed')
    );
    body.append(meta);
    body.append(element('h3', '', safeText(product.title) || 'Untitled asset pack'));
    body.append(element('p', '', safeText(product.creatorName) ? `By ${safeText(product.creatorName)}` : 'Creator pending'));

    const bottom = element('div', 'product-bottom');
    bottom.append(element('span', 'product-price', formatPrice(product)));
    const detailUrl = safePreviewUrl(product.detailUrl);
    if (detailUrl) {
      const link = element('a', '', 'View details');
      link.href = detailUrl;
      bottom.append(link);
    } else {
      bottom.append(element('span', '', safeText(product.statusLabel) || 'Preview'));
    }
    body.append(bottom);
    card.append(preview, body);
    return card;
  }

  function matchingProducts() {
    const query = state.query.toLocaleLowerCase();
    return state.products.filter(product => {
      const categoryMatches = state.category === 'All' || safeText(product.category) === state.category;
      const provenanceMatches = state.provenance === 'all' || safeText(product.provenance) === state.provenance;
      const searchable = [product.title, product.creatorName, product.category, ...(Array.isArray(product.tags) ? product.tags : [])]
        .map(safeText)
        .join(' ')
        .toLocaleLowerCase();
      return categoryMatches && provenanceMatches && (!query || searchable.includes(query));
    });
  }

  function renderProducts() {
    const products = matchingProducts();
    grid.replaceChildren(...products.map(productCard));
    grid.hidden = products.length === 0;
    empty.hidden = products.length !== 0;
    const total = state.products.length;
    count.textContent = total === 0
      ? '0 published packs'
      : `${products.length} of ${total} published ${total === 1 ? 'pack' : 'packs'}`;
  }

  function renderCategories(categories) {
    const unique = [...new Set(['All', ...categories.map(safeText).filter(Boolean)])];
    categoryList.replaceChildren(...unique.map(category => {
      const button = element('button', '', category);
      button.type = 'button';
      button.dataset.category = category;
      button.setAttribute('aria-pressed', String(category === state.category));
      return button;
    }));
  }

  async function loadCatalog() {
    try {
      const response = await fetch('/store/catalog.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`Catalog ${response.status}`);
      const data = await response.json();
      state.products = Array.isArray(data.products) ? data.products.filter(product => product && product.published === true) : [];
      state.invitationsIssued = data.invitationsIssued === true;
      invitationState.textContent = state.invitationsIssued ? 'Invitations active' : 'No creator invitations issued';
      inviteMessage.textContent = state.invitationsIssued ? 'Enter the private code supplied by ReLiC.' : 'No invitations have been issued.';
      renderCategories(Array.isArray(data.categories) ? data.categories : defaultCategories);
      renderProducts();
    } catch (loadError) {
      console.error('ReLiC store catalog failed to load', loadError);
      count.textContent = 'Catalog unavailable';
      error.hidden = false;
      grid.hidden = true;
      empty.hidden = true;
      renderCategories(defaultCategories);
    }
  }

  categoryList.addEventListener('click', event => {
    const button = event.target.closest('button[data-category]');
    if (!button) return;
    state.category = button.dataset.category;
    categoryList.querySelectorAll('button').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    renderProducts();
  });

  search.addEventListener('input', () => {
    state.query = search.value.trim();
    renderProducts();
  });

  provenance.addEventListener('change', () => {
    state.provenance = provenance.value;
    renderProducts();
  });

  inviteForm.addEventListener('submit', async event => {
    event.preventDefault();
    inviteMessage.classList.remove('error');
    if (!state.invitationsIssued) {
      inviteMessage.textContent = 'Creator invitations have not opened yet.';
      return;
    }

    const code = safeText(new FormData(inviteForm).get('inviteCode')).slice(0, 64);
    if (!code) {
      inviteMessage.textContent = 'Enter the invitation code supplied by ReLiC.';
      inviteMessage.classList.add('error');
      return;
    }

    const submit = inviteForm.querySelector('button[type="submit"]');
    submit.disabled = true;
    inviteMessage.textContent = 'Checking invitation…';
    try {
      const response = await fetch('/api/store/invitations/redeem', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ code })
      });
      if (!response.ok) throw new Error(`Invitation ${response.status}`);
      const result = await response.json();
      if (!result.redirectUrl) throw new Error('Invitation response missing redirect');
      location.assign(result.redirectUrl);
    } catch {
      inviteMessage.textContent = 'This invitation is not recognized or is no longer active.';
      inviteMessage.classList.add('error');
      submit.disabled = false;
    }
  });

  loadCatalog();
})();
