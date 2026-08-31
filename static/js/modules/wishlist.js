const STORAGE_KEY = 'svbeauty_wishlist';

function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

function isAuthenticated() {
  return document.body.dataset.wishlistAuth === '1';
}

function readGuestIds() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((id) => Number(id))
      .filter((id) => Number.isInteger(id) && id > 0);
  } catch (_err) {
    return [];
  }
}

function writeGuestIds(ids) {
  const unique = [];
  const seen = new Set();
  ids.forEach((id) => {
    const n = Number(id);
    if (!Number.isInteger(n) || n <= 0 || seen.has(n)) return;
    seen.add(n);
    unique.push(n);
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(unique));
  return unique;
}

function clearGuestIds() {
  localStorage.removeItem(STORAGE_KEY);
}

function syncCount(count) {
  document.querySelectorAll('[data-wishlist-count]').forEach((el) => {
    el.textContent = String(count);
    el.hidden = Number(count) === 0;
  });
}

function applyState(productId, inWishlist) {
  const labelAdd = 'Додати в обране';
  const labelRemove = 'Прибрати з обраного';
  document.querySelectorAll(`[data-wishlist-toggle][data-product-id="${productId}"]`).forEach((btn) => {
    btn.classList.toggle('is-active', inWishlist);
    btn.setAttribute('aria-pressed', inWishlist ? 'true' : 'false');
    btn.setAttribute('aria-label', inWishlist ? labelRemove : labelAdd);
    btn.setAttribute('title', inWishlist ? labelRemove : labelAdd);
  });
}

function hydrateFromIds(ids) {
  const set = new Set(ids.map(Number));
  document.querySelectorAll('[data-wishlist-toggle]').forEach((btn) => {
    const id = Number(btn.dataset.productId);
    if (!id) return;
    applyState(id, set.has(id));
  });
  syncCount(ids.length);
}

function removeFromWishlistPage(productId) {
  const page = document.querySelector('[data-wishlist-page]');
  if (!page) return;
  const card = page.querySelector(`[data-product-id="${productId}"]`);
  if (card) card.remove();
  if (page.querySelector('[data-product-id]')) return;

  const empty = document.querySelector('[data-wishlist-empty]');
  if (empty) {
    empty.hidden = false;
    page.hidden = true;
    return;
  }
  window.location.reload();
}

async function toggleGuest(productId) {
  let ids = readGuestIds();
  const idx = ids.indexOf(productId);
  let inWishlist;
  if (idx >= 0) {
    ids.splice(idx, 1);
    inWishlist = false;
  } else {
    ids.push(productId);
    inWishlist = true;
  }
  ids = writeGuestIds(ids);
  applyState(productId, inWishlist);
  syncCount(ids.length);
  if (!inWishlist) removeFromWishlistPage(productId);
  return { productId, inWishlist, count: ids.length };
}

async function toggleAuth(productId) {
  const url = document.body.dataset.wishlistToggleUrl;
  if (!url) throw new Error('missing toggle url');

  const body = new FormData();
  body.append('product_id', String(productId));
  const response = await fetch(url, {
    method: 'POST',
    body,
    headers: {
      'X-CSRFToken': csrfToken(),
      'X-Requested-With': 'XMLHttpRequest',
      Accept: 'application/json',
    },
    credentials: 'same-origin',
  });
  if (!response.ok) throw new Error('wishlist toggle failed');

  const data = await response.json();
  applyState(data.product_id, data.in_wishlist);
  syncCount(data.count);
  if (!data.in_wishlist) removeFromWishlistPage(data.product_id);
  return data;
}

async function mergeGuestIntoAccount() {
  const ids = readGuestIds();
  if (!ids.length) return;
  const url = document.body.dataset.wishlistMergeUrl;
  if (!url) return;

  const body = new FormData();
  body.append('ids', JSON.stringify(ids));
  try {
    const response = await fetch(url, {
      method: 'POST',
      body,
      headers: {
        'X-CSRFToken': csrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
        Accept: 'application/json',
      },
      credentials: 'same-origin',
    });
    if (!response.ok) return;
    const data = await response.json();
    clearGuestIds();
    if (typeof data.count === 'number') syncCount(data.count);
  } catch (_err) {
    // keep guest ids for next visit
  }
}

async function renderGuestWishlistPage() {
  const page = document.querySelector('[data-wishlist-guest]');
  if (!page) return;

  const empty = document.querySelector('[data-wishlist-empty]');
  const ids = readGuestIds();
  syncCount(ids.length);

  if (!ids.length) {
    page.hidden = true;
    if (empty) empty.hidden = false;
    return;
  }

  const url = document.body.dataset.wishlistProductsUrl;
  if (!url) return;

    try {
    const response = await fetch(`${url}?ids=${encodeURIComponent(ids.join(','))}`, {
      headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    });
    if (!response.ok) throw new Error('wishlist products failed');
    const data = await response.json();
    page.innerHTML = data.html || '';
    const cols = Number(data.grid_cols) || 3;
    page.dataset.gridCols = String(cols);
    page.classList.remove('product-grid--cols-2', 'product-grid--cols-3', 'product-grid--cols-4', 'product-grid--cols-5');
    page.classList.add('product-grid', `product-grid--cols-${cols}`);
    page.hidden = !data.count;
    if (empty) empty.hidden = Boolean(data.count);
    hydrateFromIds(data.ids || ids);
  } catch (_err) {
    page.hidden = true;
    if (empty) empty.hidden = false;
  }
}

export function initWishlist() {
  if (isAuthenticated()) {
    mergeGuestIntoAccount();
  } else {
    hydrateFromIds(readGuestIds());
    renderGuestWishlistPage();
  }

  document.addEventListener('click', async (event) => {
    const btn = event.target.closest('[data-wishlist-toggle]');
    if (!btn) return;
    event.preventDefault();
    event.stopPropagation();

    const productId = Number(btn.dataset.productId);
    if (!productId || btn.disabled) return;

    btn.disabled = true;
    try {
      if (isAuthenticated()) {
        await toggleAuth(productId);
      } else {
        await toggleGuest(productId);
      }
    } catch (_err) {
      // silently keep previous state
    } finally {
      btn.disabled = false;
    }
  });
}
