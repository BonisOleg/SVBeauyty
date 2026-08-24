const LOCK_CLASS = 'is-locked';

export function lockScroll(lock) {
  document.body.classList.toggle(LOCK_CLASS, lock);
}

/** Панель, що виїжджає: бургер-меню, фільтри, popup кошика. */
export function initPanel({ panel, openers = [], closers = [], overlaySelector = null }) {
  if (!panel) return null;

  const close = () => {
    panel.classList.remove('is-open');
    panel.setAttribute('aria-hidden', 'true');
    lockScroll(false);
  };

  const open = () => {
    panel.classList.add('is-open');
    panel.setAttribute('aria-hidden', 'false');
    lockScroll(true);
  };

  openers.forEach((btn) => btn && btn.addEventListener('click', (e) => { e.preventDefault(); open(); }));
  closers.forEach((btn) => btn && btn.addEventListener('click', (e) => { e.preventDefault(); close(); }));

  if (overlaySelector) {
    const overlay = panel.querySelector(overlaySelector);
    if (overlay) overlay.addEventListener('click', close);
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel.classList.contains('is-open')) close();
  });

  return { open, close };
}

export function initTabs(root = document) {
  root.querySelectorAll('[data-tabs]').forEach((block) => {
    const buttons = block.querySelectorAll('[data-tab-btn]');
    const panels = block.querySelectorAll('[data-tab-panel]');
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tabBtn;
        buttons.forEach((b) => b.classList.toggle('is-active', b === btn));
        panels.forEach((p) => p.classList.toggle('is-active', p.dataset.tabPanel === target));
      });
    });
  });
}

export function initGallery(root = document) {
  const main = root.querySelector('[data-gallery-main]');
  if (!main) return;
  root.querySelectorAll('[data-gallery-thumb]').forEach((thumb) => {
    thumb.addEventListener('click', () => {
      main.src = thumb.dataset.galleryThumb;
      root.querySelectorAll('[data-gallery-thumb]').forEach((t) => t.classList.toggle('is-active', t === thumb));
    });
  });
}

export function initVariantPicker(root = document) {
  const chips = root.querySelectorAll('[data-variant]');
  if (!chips.length) return;
  const priceEl = root.querySelector('[data-variant-price]');
  const oldPriceEl = root.querySelector('[data-variant-old-price]');
  const input = root.querySelector('[data-variant-input]');

  const apply = (chip) => {
    chips.forEach((c) => c.classList.toggle('is-active', c === chip));
    if (input) input.value = chip.dataset.variant;
    if (priceEl) priceEl.textContent = chip.dataset.price;
    if (oldPriceEl) {
      oldPriceEl.textContent = chip.dataset.oldPrice || '';
      oldPriceEl.hidden = !chip.dataset.oldPrice;
    }
  };

  chips.forEach((chip) => {
    if (chip.classList.contains('is-out')) return;
    chip.addEventListener('click', () => apply(chip));
  });
}

export function initQuantity(root = document) {
  root.querySelectorAll('[data-qty]').forEach((widget) => {
    const input = widget.querySelector('input');
    if (!input) return;
    widget.querySelectorAll('[data-qty-step]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const step = Number(btn.dataset.qtyStep);
        const next = Math.max(1, Math.min(99, Number(input.value || 1) + step));
        input.value = next;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    });
  });
}
