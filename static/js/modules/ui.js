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
        buttons.forEach((b) => {
          const active = b === btn;
          b.classList.toggle('is-active', active);
          b.setAttribute('aria-selected', active ? 'true' : 'false');
        });
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
  const buybox = root.querySelector('[data-product-buybox]');
  if (!buybox || buybox.dataset.variantPickerReady === '1') return;
  buybox.dataset.variantPickerReady = '1';

  const ui = buybox.querySelector('[data-product-variant-ui]');
  const trigger = buybox.querySelector('[data-product-variant-trigger]');
  const list = buybox.querySelector('[data-product-variant-list]');
  const options = [...buybox.querySelectorAll('[data-product-variant-option]')];
  const input = buybox.querySelector('[data-variant-input]');
  const priceEl = buybox.querySelector('[data-variant-price]');
  const oldPriceEl = buybox.querySelector('[data-variant-old-price]');
  const proHint = buybox.querySelector('[data-variant-pro-hint]');
  const cosmoNote = buybox.querySelector('[data-variant-cosmo-note]');
  const buyBtn = buybox.querySelector('[data-buy-btn]');
  const qty = buybox.querySelector('[data-qty]');
  const stockLabel = buybox.querySelector('[data-stock-label]') || root.querySelector('[data-stock-label]');
  const labelEl = buybox.querySelector('[data-product-variant-label]');
  const thumbEl = buybox.querySelector('[data-product-variant-thumb] img');

  if (!options.length) return;

  let selected = buybox.querySelector('[data-product-variant-option].is-selected:not(.is-disabled)')
    || buybox.querySelector('[data-product-variant-option]:not(.is-disabled)')
    || options[0];

  const showPrice = (option) => {
    if (!option) return;
    if (priceEl) {
      priceEl.textContent = option.dataset.price || '';
      priceEl.classList.toggle('product__price--sale', option.dataset.isSale === '1');
    }
    if (oldPriceEl) {
      const old = option.dataset.oldPrice || '';
      oldPriceEl.textContent = old;
      oldPriceEl.hidden = !old;
    }
  };

  const applySelection = (option) => {
    if (!option || option.classList.contains('is-disabled')) return;
    selected = option;
    options.forEach((item) => {
      const active = item === option;
      item.classList.toggle('is-selected', active);
      item.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    if (input) input.value = option.dataset.variant || '';
    if (labelEl) labelEl.textContent = option.dataset.label || '';
    if (thumbEl && option.dataset.thumb) thumbEl.src = option.dataset.thumb;
    showPrice(option);

    const isPro = option.dataset.isPro === '1';
    const isSale = option.dataset.isSale === '1';
    if (proHint) proHint.hidden = !isPro;
    if (cosmoNote) cosmoNote.hidden = isPro || isSale;

    const inStock = option.dataset.inStock === '1';
    if (buyBtn) {
      buyBtn.disabled = !inStock;
      buyBtn.textContent = inStock
        ? (buyBtn.dataset.labelIn || buyBtn.textContent)
        : (buyBtn.dataset.labelOut || buyBtn.textContent);
    }
    if (qty) {
      qty.hidden = !inStock;
      qty.querySelectorAll('input, button').forEach((el) => {
        el.disabled = !inStock;
      });
    }
    if (stockLabel) {
      stockLabel.textContent = inStock
        ? (stockLabel.dataset.labelIn || '')
        : (stockLabel.dataset.labelOut || '');
      stockLabel.classList.toggle('is-out', !inStock);
    }

    buybox.querySelectorAll('[data-variant-chip]').forEach((chip) => {
      chip.classList.toggle('is-selected', chip.dataset.variant === option.dataset.variant);
    });
  };

  const closeList = () => {
    if (!ui || !list || !trigger) return;
    ui.classList.remove('is-open');
    list.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    showPrice(selected);
  };

  const openList = () => {
    if (!ui || !list || !trigger || ui.classList.contains('product-variant--single')) return;
    ui.classList.add('is-open');
    list.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
  };

  if (trigger && list) {
    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (ui.classList.contains('product-variant--single')) return;
      if (ui.classList.contains('is-open')) closeList();
      else openList();
    });

    list.addEventListener('mouseover', (event) => {
      const option = event.target.closest('[data-product-variant-option]');
      if (!option || option.classList.contains('is-disabled')) return;
      showPrice(option);
    });

    list.addEventListener('mouseleave', () => {
      showPrice(selected);
    });

    list.addEventListener('click', (event) => {
      const option = event.target.closest('[data-product-variant-option]');
      if (!option || option.classList.contains('is-disabled')) return;
      event.stopPropagation();
      applySelection(option);
      closeList();
    });

    document.addEventListener('click', (event) => {
      if (!ui.contains(event.target)) closeList();
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeList();
    });
  }

  applySelection(selected);

  buybox.querySelectorAll('[data-variant-chip]').forEach((chip) => {
    chip.addEventListener('click', () => {
      if (chip.disabled || chip.classList.contains('is-disabled')) return;
      const option = options.find((item) => item.dataset.variant === chip.dataset.variant);
      if (option) applySelection(option);
    });
  });
}

export function initCarousels(root = document) {
  root.querySelectorAll('[data-carousel]').forEach((carousel) => {
    const track = carousel.querySelector('[data-carousel-track]');
    const prev = carousel.querySelector('[data-carousel-prev]');
    const next = carousel.querySelector('[data-carousel-next]');
    if (!track) return;
    const step = () => Math.max(Math.floor(track.clientWidth * 0.75), 220);
    if (prev) {
      prev.addEventListener('click', () => {
        track.scrollBy({ left: -step(), behavior: 'smooth' });
      });
    }
    if (next) {
      next.addEventListener('click', () => {
        track.scrollBy({ left: step(), behavior: 'smooth' });
      });
    }
    // Горизонтальний жест трекпада / shift+wheel — без перехоплення вертикалі сторінки
    track.addEventListener(
      'wheel',
      (event) => {
        if (event.ctrlKey) return;
        const absX = Math.abs(event.deltaX);
        const absY = Math.abs(event.deltaY);
        const horizontal = event.shiftKey || absX > absY;
        if (!horizontal) return;
        const delta = event.shiftKey ? event.deltaY : event.deltaX || event.deltaY;
        if (!delta) return;
        track.scrollLeft += delta;
        event.preventDefault();
      },
      { passive: false },
    );
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

/** Перегляд / редагування особистих даних у кабінеті. */
export function initProfileCard(root = document) {
  root.querySelectorAll('[data-profile-card]').forEach((card) => {
    const view = card.querySelector('[data-profile-view]');
    const form = card.querySelector('[data-profile-form]');
    const editBtn = card.querySelector('[data-profile-edit]');
    const cancelBtn = card.querySelector('[data-profile-cancel]');
    if (!view || !form || !editBtn) return;

    const open = () => {
      card.classList.add('is-editing');
      form.hidden = false;
      view.hidden = true;
      const first = form.querySelector('input, textarea, select');
      if (first) first.focus();
    };

    const close = () => {
      card.classList.remove('is-editing');
      form.hidden = true;
      view.hidden = false;
      form.reset();
    };

    editBtn.addEventListener('click', open);
    if (cancelBtn) cancelBtn.addEventListener('click', close);

    if (card.dataset.editing === 'true' || card.classList.contains('is-editing')) {
      open();
    }
  });
}
