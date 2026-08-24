import { lockScroll } from './ui.js';

function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

function openPopup(popup) {
  if (!popup) return;
  popup.classList.add('is-open');
  popup.setAttribute('aria-hidden', 'false');
  lockScroll(true);
}

function syncCount(count) {
  document.querySelectorAll('[data-cart-count]').forEach((el) => {
    el.textContent = count;
    el.hidden = Number(count) === 0;
  });
}

/** Fallback без HTMX (старі браузери / відсутній CDN). */
async function postJson(url, data) {
  const body = new FormData();
  Object.entries(data).forEach(([key, value]) => body.append(key, value));
  const response = await fetch(url, {
    method: 'POST',
    body,
    headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
    credentials: 'same-origin',
  });
  if (!response.ok) throw new Error('cart request failed');
  return response.json();
}

function renderPopupFromJson(payload) {
  const popup = document.querySelector('[data-cart-popup]');
  const body = popup && popup.querySelector('[data-cart-popup-body]');
  const foot = popup && popup.querySelector('[data-cart-popup-foot]');
  if (body && payload.popup) body.innerHTML = payload.popup;
  if (foot && payload.popup_foot) foot.innerHTML = payload.popup_foot;
  syncCount(payload.count);
  return popup;
}

export function initCart() {
  const urls = document.body.dataset;
  const hasHtmx = typeof window.htmx !== 'undefined';

  document.body.addEventListener('cartOpen', () => {
    openPopup(document.querySelector('[data-cart-popup]'));
  });
  document.body.addEventListener('cartUpdated', (event) => {
    if (event.detail && event.detail.count != null) syncCount(event.detail.count);
  });

  if (hasHtmx) {
    // HTMX-форми: hx-post + OOB. Vanilla лишається для qty/remove без hx-атрибутів.
    document.addEventListener('click', (event) => {
      const remove = event.target.closest('[data-cart-remove]');
      if (remove && !remove.hasAttribute('hx-post')) {
        event.preventDefault();
        window.htmx.ajax('POST', urls.cartRemoveUrl, {
          values: { item_id: remove.dataset.cartRemove },
          swap: 'none',
          headers: { 'X-CSRFToken': csrfToken() },
        }).then(() => {
          if (document.querySelector('[data-cart-page]')) window.location.reload();
        });
      }
    });
    return;
  }

  document.addEventListener('submit', async (event) => {
    const form = event.target.closest('[data-cart-add]');
    if (!form) return;
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = true;
    try {
      openPopup(renderPopupFromJson(await postJson(urls.cartAddUrl, data)));
    } catch (error) {
      form.submit();
    } finally {
      if (button) button.disabled = false;
    }
  });

  document.addEventListener('click', async (event) => {
    const remove = event.target.closest('[data-cart-remove]');
    if (remove) {
      event.preventDefault();
      renderPopupFromJson(await postJson(urls.cartRemoveUrl, { item_id: remove.dataset.cartRemove }));
      if (document.querySelector('[data-cart-page]')) window.location.reload();
      return;
    }
    const step = event.target.closest('[data-cart-step]');
    if (step) {
      event.preventDefault();
      renderPopupFromJson(
        await postJson(urls.cartUpdateUrl, {
          item_id: step.dataset.itemId,
          quantity: step.dataset.cartStep,
        }),
      );
      if (document.querySelector('[data-cart-page]')) window.location.reload();
    }
  });

  document.addEventListener('change', async (event) => {
    const input = event.target.closest('[data-cart-qty]');
    if (!input) return;
    renderPopupFromJson(
      await postJson(urls.cartUpdateUrl, {
        item_id: input.dataset.cartQty,
        quantity: input.value,
      }),
    );
    if (document.querySelector('[data-cart-page]')) window.location.reload();
  });
}
