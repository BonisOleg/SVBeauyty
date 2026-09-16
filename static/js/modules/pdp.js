/** PDP mobile: gallery slider, sticky buy, volume chips sync */

export function initGallerySlider(root = document) {
  root.querySelectorAll('[data-gallery-slider]').forEach((gallery) => {
    const track = gallery.querySelector('[data-gallery-track]');
    const slides = [...gallery.querySelectorAll('.gallery__slide')];
    const dots = [...gallery.querySelectorAll('[data-gallery-dot]')];
    const thumbs = [...gallery.querySelectorAll('[data-gallery-thumb-index]')];
    const mobilePrevs = [...gallery.querySelectorAll('.gallery__controls [data-gallery-prev]')];
    const mobileNexts = [...gallery.querySelectorAll('.gallery__controls [data-gallery-next]')];
    const deskPrevs = [...gallery.querySelectorAll('.gallery__thumb-arrow[data-gallery-prev]')];
    const deskNexts = [...gallery.querySelectorAll('.gallery__thumb-arrow[data-gallery-next]')];
    if (!track || slides.length < 2) return;

    let index = Math.max(0, slides.findIndex((s) => s.classList.contains('is-active')));

    const thumbsRow = gallery.querySelector('[data-gallery-thumbs]');

    const thumbsOverflow = () => {
      if (!thumbsRow) return false;
      return thumbsRow.scrollWidth > thumbsRow.clientWidth + 1;
    };

    const syncDeskArrows = () => {
      const overflow = thumbsOverflow();
      deskPrevs.forEach((btn) => {
        btn.hidden = !overflow || index <= 0;
      });
      deskNexts.forEach((btn) => {
        btn.hidden = !overflow || index >= slides.length - 1;
      });
    };

    const syncMobileArrows = () => {
      const atStart = index <= 0;
      const atEnd = index >= slides.length - 1;
      mobilePrevs.forEach((btn) => {
        btn.disabled = atStart;
        btn.setAttribute('aria-disabled', atStart ? 'true' : 'false');
        btn.classList.toggle('is-disabled', atStart);
      });
      mobileNexts.forEach((btn) => {
        btn.disabled = atEnd;
        btn.setAttribute('aria-disabled', atEnd ? 'true' : 'false');
        btn.classList.toggle('is-disabled', atEnd);
      });
    };

    const syncArrows = () => {
      syncDeskArrows();
      syncMobileArrows();
    };

    const goTo = (nextIndex) => {
      index = Math.max(0, Math.min(slides.length - 1, nextIndex));
      track.style.transform = `translate3d(-${index * 100}%, 0, 0)`;
      slides.forEach((slide, i) => slide.classList.toggle('is-active', i === index));
      dots.forEach((dot, i) => dot.classList.toggle('is-active', i === index));
      thumbs.forEach((thumb, i) => thumb.classList.toggle('is-active', i === index));
      const activeThumb = thumbs[index];
      if (activeThumb && typeof activeThumb.scrollIntoView === 'function') {
        activeThumb.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: 'smooth' });
      }
      syncArrows();
    };

    goTo(index);
    window.requestAnimationFrame(syncArrows);

    if (typeof ResizeObserver !== 'undefined' && thumbsRow) {
      const ro = new ResizeObserver(() => syncArrows());
      ro.observe(thumbsRow);
    }
    window.addEventListener('resize', syncArrows, { passive: true });

    mobilePrevs.forEach((btn) => btn.addEventListener('click', () => {
      if (index <= 0) return;
      goTo(index - 1);
    }));
    mobileNexts.forEach((btn) => btn.addEventListener('click', () => {
      if (index >= slides.length - 1) return;
      goTo(index + 1);
    }));
    deskPrevs.forEach((btn) => btn.addEventListener('click', () => goTo(index - 1)));
    deskNexts.forEach((btn) => btn.addEventListener('click', () => goTo(index + 1)));
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
        /* на краях — опір свайпу, без зациклення */
        if ((index <= 0 && deltaX > 0) || (index >= slides.length - 1 && deltaX < 0)) {
          deltaX *= 0.35;
        }
        const offset = -index * 100 + (deltaX / Math.max(1, track.clientWidth)) * 100;
        track.style.transform = `translate3d(${offset}%, 0, 0)`;
      },
      { passive: true },
    );

    track.addEventListener('touchend', () => {
      if (!dragging) return;
      dragging = false;
      track.style.transition = '';
      if (Math.abs(deltaX) > 40) {
        if (deltaX < 0 && index < slides.length - 1) goTo(index + 1);
        else if (deltaX > 0 && index > 0) goTo(index - 1);
        else goTo(index);
      } else {
        goTo(index);
      }
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
