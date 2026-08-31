import { initCart } from './modules/cart.js';
import { initChat } from './modules/chat.js';
import { initCopy } from './modules/copy.js';
import { initHeroSlider } from './modules/hero-slider.js';
import { initMessages } from './modules/messages.js';
import { initNovaPoshta } from './modules/nova-poshta.js';
import { initDeliveryMethod } from './modules/delivery.js';
import { initProductCards } from './modules/product-card.js';
import { initWishlist } from './modules/wishlist.js';
import { initCarousels, initGallery, initPanel, initProfileCard, initQuantity, initTabs, initVariantPicker } from './modules/ui.js';
import { initGallerySlider, initPdpSticky, initGiftPromoTooltip } from './modules/pdp.js';

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
  const totalEl = document.querySelector('[data-checkout-total]');
  const discountEl = document.querySelector('[data-checkout-discount]');
  const discountRow = document.querySelector('[data-checkout-discount-row]');
  const box = document.querySelector('[data-loyalty-box]');
  if (!input || !output) return;

  const parseNum = (value) => {
    const n = Number(String(value ?? '').replace(',', '.').trim());
    return Number.isFinite(n) ? n : 0;
  };

  const formatUah = (value) => {
    const fixed = value.toFixed(2);
    const [intPart, decPart] = fixed.split('.');
    const withSpaces = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return `${withSpaces},${decPart}`;
  };

  const rate = parseNum(input.dataset.rate || 1);
  const subtotal = parseNum(box ? box.dataset.subtotal : 0);

  const update = () => {
    const max = parseNum(input.max);
    const points = Math.max(0, Math.min(max, parseNum(input.value || 0)));
    const discount = points * rate;
    const payable = Math.max(0, subtotal - discount);

    output.textContent = Number.isFinite(discount) ? discount.toFixed(2) : '0.00';

    if (discountEl) discountEl.textContent = formatUah(discount);
    if (discountRow) discountRow.hidden = discount <= 0;
    if (totalEl) totalEl.textContent = formatUah(payable);
  };

  input.addEventListener('input', update);
  update();
}

function initCheckoutPayHint() {
  const hints = document.querySelectorAll('[data-checkout-pay-hint]');
  if (!hints.length) return;

  const sync = () => {
    const selected = document.querySelector('input[name="payment_method"]:checked');
    const code = selected ? selected.value : '';
    hints.forEach((el) => {
      el.hidden = el.dataset.checkoutPayHint !== code;
    });
    document.querySelectorAll('input[name="payment_method"]').forEach((radio) => {
      const card = radio.closest('.radio-card');
      if (card) card.classList.toggle('is-active', radio.checked);
    });
  };

  document.querySelectorAll('input[name="payment_method"]').forEach((radio) => {
    radio.addEventListener('change', sync);
  });
  sync();
}

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initCart();
  initCopy();
  initMessages();
  initChat();
  initNovaPoshta();
  initDeliveryMethod();
  initTabs();
  initGallery();
  initGallerySlider();
  initVariantPicker();
  initQuantity();
  initCarousels();
  initPdpSticky();
  initGiftPromoTooltip();
  initProductCards();
  initSortAutoSubmit();
  initLoyaltySlider();
  initCheckoutPayHint();
  initHeroSlider();
  initProfileCard();
  initWishlist();
});
