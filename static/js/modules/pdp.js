/** PDP mobile: gallery slider, sticky buy, volume chips sync */

export function initGallerySlider(root = document) {
  root.querySelectorAll('[data-gallery-slider]').forEach((gallery) => {
    const track = gallery.querySelector('[data-gallery-track]');
    const slides = [...gallery.querySelectorAll('.gallery__slide')];
    const dots = [...gallery.querySelectorAll('[data-gallery-dot]')];
    const thumbs = [...gallery.querySelectorAll('[data-gallery-thumb-index]')];
    const prev = gallery.querySelector('[data-gallery-prev]');
    const next = gallery.querySelector('[data-gallery-next]');
    if (!track || slides.length < 2) return;

    let index = Math.max(0, slides.findIndex((s) => s.classList.contains('is-active')));

    const goTo = (nextIndex) => {
      index = (nextIndex + slides.length) % slides.length;
      track.style.transform = `translate3d(-${index * 100}%, 0, 0)`;
      slides.forEach((slide, i) => slide.classList.toggle('is-active', i === index));
      dots.forEach((dot, i) => dot.classList.toggle('is-active', i === index));
      thumbs.forEach((thumb, i) => thumb.classList.toggle('is-active', i === index));
    };

    goTo(index);

    if (prev) prev.addEventListener('click', () => goTo(index - 1));
    if (next) next.addEventListener('click', () => goTo(index + 1));
    dots.forEach((dot) => {
      dot.addEventListener('click', () => goTo(Number(dot.dataset.galleryDot) || 0));
    });
    thumbs.forEach((thumb) => {
      thumb.addEventListener('click', () => goTo(Number(thumb.dataset.galleryThumbIndex) || 0));
    });

    let startX = 0;
    let deltaX = 0;
    let dragging = false;

    track.addEventListener(
      'touchstart',
      (event) => {
        if (!event.touches[0]) return;
        dragging = true;
        startX = event.touches[0].clientX;
        deltaX = 0;
        track.style.transition = 'none';
      },
      { passive: true },
    );

    track.addEventListener(
      'touchmove',
      (event) => {
        if (!dragging || !event.touches[0]) return;
        deltaX = event.touches[0].clientX - startX;
        const offset = -index * 100 + (deltaX / track.clientWidth) * 100;
        track.style.transform = `translate3d(${offset}%, 0, 0)`;
      },
      { passive: true },
    );

    track.addEventListener('touchend', () => {
      if (!dragging) return;
      dragging = false;
      track.style.transition = '';
      if (Math.abs(deltaX) > 40) goTo(index + (deltaX < 0 ? 1 : -1));
      else goTo(index);
    });
  });
}

export function initPdpSticky(root = document) {
  const sticky = root.querySelector('[data-pdp-sticky]');
  if (!sticky) return;
  const stickyBuy = sticky.querySelector('[data-pdp-sticky-buy]');
  const scrollTop = sticky.querySelector('[data-scroll-top]');
  const buyBtn = root.querySelector('[data-product-buybox] [data-buy-btn]');

  const syncDisabled = () => {
    if (!stickyBuy || !buyBtn) return;
    stickyBuy.disabled = Boolean(buyBtn.disabled);
    stickyBuy.textContent = buyBtn.textContent;
  };

  if (stickyBuy && buyBtn) {
    stickyBuy.addEventListener('click', () => {
      if (buyBtn.disabled) return;
      buyBtn.click();
    });
    syncDisabled();
    const observer = new MutationObserver(syncDisabled);
    observer.observe(buyBtn, { attributes: true, childList: true, characterData: true, subtree: true });
  }

  if (scrollTop) {
    scrollTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
}

export function syncVariantChips(buybox, selectedOption) {
  if (!buybox || !selectedOption) return;
  const id = selectedOption.dataset.variant;
  buybox.querySelectorAll('[data-variant-chip]').forEach((chip) => {
    chip.classList.toggle('is-selected', chip.dataset.variant === id);
  });
}

export function initGiftPromoTooltip(root = document) {
  const canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  root.querySelectorAll('[data-gift-promo]').forEach((banner) => {
    const btn = banner.querySelector('[data-gift-promo-info]');
    const tip = banner.querySelector('[data-gift-promo-tooltip]');
    if (!btn || !tip) return;

    const place = () => {
      // Трохи нижче іконки «і», ширина = банер (left/right: 0 у CSS)
      const top = btn.offsetTop + btn.offsetHeight + 8;
      const arrow = btn.offsetLeft + btn.offsetWidth / 2;
      banner.style.setProperty('--gift-tip-top', `${top}px`);
      banner.style.setProperty('--gift-tip-arrow-left', `${arrow}px`);
    };

    const close = () => {
      tip.hidden = true;
      btn.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
    };

    const open = () => {
      place();
      tip.hidden = false;
      btn.classList.add('is-open');
      btn.setAttribute('aria-expanded', 'true');
    };

    window.addEventListener('resize', () => {
      if (!tip.hidden) place();
    });

    if (canHover) {
      const leaveTo = (related, other) => related && (other === related || other.contains(related));

      btn.addEventListener('mouseenter', open);
      tip.addEventListener('mouseenter', open);

      btn.addEventListener('mouseleave', (event) => {
        if (!leaveTo(event.relatedTarget, tip)) close();
      });
      tip.addEventListener('mouseleave', (event) => {
        if (!leaveTo(event.relatedTarget, btn)) close();
      });

      btn.addEventListener('focus', open);
      btn.addEventListener('blur', close);
    } else {
      // iOS / touch: tap toggles (hover недоступний)
      btn.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (tip.hidden) open();
        else close();
      });
      document.addEventListener('click', (event) => {
        if (!banner.contains(event.target)) close();
      });
    }

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') close();
    });
  });
}
