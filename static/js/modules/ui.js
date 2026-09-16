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
    if (ui.dataset.variantPinnedClosed === '1') return;
    ui.classList.add('is-open');
    list.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
  };

  const hoverOpen = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  if (trigger && list) {
    // Завжди старт у закритому стані (раніше при 1 варіанті list був без hidden).
    closeList();

    if (hoverOpen) {
      ui.addEventListener('mouseenter', openList);
      ui.addEventListener('mouseleave', () => {
        ui.dataset.variantPinnedClosed = '';
        closeList();
      });
    }

    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (ui.classList.contains('product-variant--single')) return;
      ui.dataset.variantPinnedClosed = '';
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
      // Поки курсор ще над селектом — не відкривати знову через mouseenter-логіку.
      if (hoverOpen) ui.dataset.variantPinnedClosed = '1';
      closeList();
    });

    document.addEventListener('click', (event) => {
      if (!ui.contains(event.target)) {
        ui.dataset.variantPinnedClosed = '';
        closeList();
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        ui.dataset.variantPinnedClosed = '';
        closeList();
      }
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
    const dotsWrap = carousel.querySelector('[data-carousel-dots]');
    if (!track) return;

    const gapOf = () => {
      const g = getComputedStyle(track).gap || getComputedStyle(track).columnGap || '0';
      return parseFloat(g) || 0;
    };

    const cardPitch = () => {
      const slide = track.querySelector('.pdp-carousel__slide');
      if (!slide) return Math.max(220, Math.floor(track.clientWidth * 0.8));
      return slide.getBoundingClientRect().width + gapOf();
    };

    const visibleCount = () => {
      const pitch = cardPitch();
      if (pitch <= 0) return 1;
      return Math.max(1, Math.floor((track.clientWidth + gapOf()) / pitch));
    };

    /** Крок = цілі картки, що вміщуються у трек (мін. 1). */
    const step = () => cardPitch() * visibleCount();

    const maxScroll = () => Math.max(0, track.scrollWidth - track.clientWidth);

    const pageCount = () => {
      const max = maxScroll();
      if (max <= 2) return 1;
      const s = step();
      if (s <= 0) return 1;
      return Math.max(1, Math.ceil((max + 1) / s));
    };

    const currentPage = () => {
      const s = step();
      if (s <= 0) return 0;
      const max = maxScroll();
      if (track.scrollLeft >= max - 2) return Math.max(0, pageCount() - 1);
      return Math.max(0, Math.min(pageCount() - 1, Math.round(track.scrollLeft / s)));
    };

    const rebuildDots = () => {
      if (!dotsWrap) return;
      const count = pageCount();
      const isCompact = window.matchMedia('(max-width: 1024px)').matches;
      if (!isCompact || count <= 1) {
        dotsWrap.hidden = true;
        dotsWrap.setAttribute('aria-hidden', 'true');
        dotsWrap.innerHTML = '';
        return;
      }
      dotsWrap.hidden = false;
      dotsWrap.setAttribute('aria-hidden', 'false');
      const active = currentPage();
      dotsWrap.innerHTML = '';
      for (let i = 0; i < count; i += 1) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `pdp-carousel__dot${i === active ? ' is-active' : ''}`;
        btn.setAttribute('aria-label', `Слайд ${i + 1}`);
        btn.dataset.carouselPage = String(i);
        btn.addEventListener('click', () => {
          const s = step();
          const max = maxScroll();
          track.scrollTo({ left: Math.min(max, i * s), behavior: 'smooth' });
        });
        dotsWrap.appendChild(btn);
      }
    };

    const syncDots = () => {
      if (!dotsWrap || dotsWrap.hidden) return;
      const active = currentPage();
      dotsWrap.querySelectorAll('.pdp-carousel__dot').forEach((dot, i) => {
        dot.classList.toggle('is-active', i === active);
      });
    };

    const syncArrows = () => {
      const max = maxScroll();
      const left = track.scrollLeft;
      if (prev) {
        const atStart = left <= 2 || max <= 2;
        prev.disabled = atStart;
        prev.setAttribute('aria-disabled', atStart ? 'true' : 'false');
        prev.classList.toggle('is-disabled', atStart);
      }
      if (next) {
        const atEnd = left >= max - 2 || max <= 2;
        next.disabled = atEnd;
        next.setAttribute('aria-disabled', atEnd ? 'true' : 'false');
        next.classList.toggle('is-disabled', atEnd);
      }
      syncDots();
    };

    const scrollByDir = (dir) => {
      const max = maxScroll();
      if (max <= 0) return;
      const pitch = cardPitch();
      const current = track.scrollLeft;
      const aligned = Math.round(current / pitch) * pitch;
      const target = Math.max(0, Math.min(max, aligned + dir * step()));
      track.scrollTo({ left: target, behavior: 'smooth' });
    };

    if (prev) prev.addEventListener('click', () => scrollByDir(-1));
    if (next) next.addEventListener('click', () => scrollByDir(1));

    let scrollTick = 0;
    track.addEventListener(
      'scroll',
      () => {
        if (scrollTick) return;
        scrollTick = requestAnimationFrame(() => {
          scrollTick = 0;
          syncArrows();
        });
      },
      { passive: true },
    );

    const refresh = () => {
      rebuildDots();
      syncArrows();
    };

    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(refresh);
      ro.observe(track);
    }
    window.addEventListener('resize', refresh, { passive: true });
    refresh();

    const isCompact = () => window.matchMedia('(max-width: 1024px)').matches;

    /* ≤1024 на ноуті: вертикальний wheel/trackpad → горизонталь каруселі */
    track.addEventListener(
      'wheel',
      (event) => {
        if (event.ctrlKey) return;
        const max = maxScroll();
        if (max <= 0) return;

        const absX = Math.abs(event.deltaX);
        const absY = Math.abs(event.deltaY);
        let delta = 0;

        if (event.shiftKey) {
          delta = event.deltaY || event.deltaX;
        } else if (absX > absY) {
          delta = event.deltaX;
        } else if (isCompact() && absY > 0) {
          delta = event.deltaY;
        } else {
          return;
        }

        if (!delta) return;

        const before = track.scrollLeft;
        const nextLeft = Math.max(0, Math.min(max, before + delta));
        if (nextLeft === before) return;

        track.scrollLeft = nextLeft;
        event.preventDefault();
      },
      { passive: false },
    );

    /* Drag-свайп мишкою / трекпадом (клік-тягни), ≤1024 */
    let drag = null;
    track.addEventListener('pointerdown', (event) => {
      if (!isCompact() || event.button !== 0) return;
      /* touch — нативний overflow-свайп; drag лише mouse/pen */
      if (event.pointerType === 'touch') return;
      if (event.target.closest('a, button, input, label')) return;
      if (maxScroll() <= 0) return;
      drag = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startScroll: track.scrollLeft,
        moved: false,
      };
      track.classList.add('is-dragging');
      try {
        track.setPointerCapture(event.pointerId);
      } catch (_) {
        /* ignore */
      }
    });

    track.addEventListener('pointermove', (event) => {
      if (!drag || event.pointerId !== drag.pointerId) return;
      const dx = event.clientX - drag.startX;
      if (Math.abs(dx) > 4) drag.moved = true;
      track.scrollLeft = drag.startScroll - dx;
      if (drag.moved) event.preventDefault();
    });

    const endDrag = (event) => {
      if (!drag || (event && event.pointerId !== drag.pointerId)) return;
      const wasMoved = drag.moved;
      drag = null;
      track.classList.remove('is-dragging');
      if (wasMoved) {
        /* блокуємо кліки по картці після драгу */
        const block = (e) => {
          e.preventDefault();
          e.stopPropagation();
          track.removeEventListener('click', block, true);
        };
        track.addEventListener('click', block, true);
      }
    };

    track.addEventListener('pointerup', endDrag);
    track.addEventListener('pointercancel', endDrag);
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
