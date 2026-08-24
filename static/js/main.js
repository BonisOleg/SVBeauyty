import { initCart } from './modules/cart.js';
import { initChat } from './modules/chat.js';
import { initCopy } from './modules/copy.js';
import { initNovaPoshta } from './modules/nova-poshta.js';
import { initGallery, initPanel, initQuantity, initTabs, initVariantPicker } from './modules/ui.js';

function initHeader() {
  initPanel({
    panel: document.querySelector('[data-drawer]'),
    openers: [document.querySelector('[data-drawer-open]')],
    closers: Array.from(document.querySelectorAll('[data-drawer-close]')),
    overlaySelector: '[data-drawer-overlay]',
  });

  initPanel({
    panel: document.querySelector('[data-cart-popup]'),
    openers: Array.from(document.querySelectorAll('[data-cart-open]')),
    closers: Array.from(document.querySelectorAll('[data-cart-close]')),
    overlaySelector: '[data-cart-overlay]',
  });

  initPanel({
    panel: document.querySelector('[data-filters-mobile]'),
    openers: [document.querySelector('[data-filters-open]')],
    closers: Array.from(document.querySelectorAll('[data-filters-close]')),
    overlaySelector: '[data-filters-overlay]',
  });
}

function initSortAutoSubmit() {
  document.querySelectorAll('[data-autosubmit]').forEach((el) => {
    el.addEventListener('change', () => el.form && el.form.submit());
  });
}

function initLoyaltySlider() {
  const input = document.querySelector('[data-loyalty-points]');
  const output = document.querySelector('[data-loyalty-value]');
  if (!input || !output) return;
  const rate = Number(input.dataset.rate || 1);
  const update = () => {
    const points = Math.max(0, Math.min(Number(input.max), Number(input.value || 0)));
    output.textContent = (points * rate).toFixed(2);
  };
  input.addEventListener('input', update);
  update();
}

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initCart();
  initCopy();
  initChat();
  initNovaPoshta();
  initTabs();
  initGallery();
  initVariantPicker();
  initQuantity();
  initSortAutoSubmit();
  initLoyaltySlider();
});
