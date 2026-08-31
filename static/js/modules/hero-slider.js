const SWIPE_THRESHOLD = 48;

export function initHeroSlider(root = document) {
  const slider = root.querySelector('[data-hero-slider]');
  if (!slider) return;

  const track = slider.querySelector('[data-hero-track]');
  const slides = Array.from(slider.querySelectorAll('[data-hero-slide]'));
  const dots = Array.from(slider.querySelectorAll('[data-hero-dot]'));
  if (!track || slides.length < 2) return;

  const intervalMs = Math.max(4000, Number(slider.dataset.interval || 7000));
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let index = 0;
  let timer = null;
  let startX = 0;
  let startY = 0;
  let deltaX = 0;
  let locking = null;
  let dragging = false;

  const setIndex = (next, { animate = true } = {}) => {
    index = ((next % slides.length) + slides.length) % slides.length;
    if (!animate) track.style.transition = 'none';
    track.style.transform = `translate3d(${-index * 100}%, 0, 0)`;
    if (!animate) {
      // force reflow so next transition works on iOS Safari
      void track.offsetWidth;
      track.style.transition = '';
    }

    slides.forEach((slide, i) => {
      slide.setAttribute('aria-hidden', i === index ? 'false' : 'true');
    });
    dots.forEach((dot, i) => {
      const active = i === index;
      dot.classList.toggle('is-active', active);
      dot.setAttribute('aria-selected', active ? 'true' : 'false');
    });
  };

  const stop = () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };

  const start = () => {
    if (reduceMotion || document.hidden) return;
    stop();
    timer = window.setInterval(() => setIndex(index + 1), intervalMs);
  };

  const restart = () => {
    stop();
    start();
  };

  dots.forEach((dot) => {
    dot.addEventListener('click', () => {
      setIndex(Number(dot.dataset.heroDot || 0));
      restart();
    });
  });

  const onPointerDown = (clientX, clientY) => {
    dragging = true;
    locking = null;
    startX = clientX;
    startY = clientY;
    deltaX = 0;
    slider.classList.add('is-dragging');
    stop();
  };

  const onPointerMove = (clientX, clientY, event) => {
    if (!dragging) return;
    const dx = clientX - startX;
    const dy = clientY - startY;
    if (locking === null && (Math.abs(dx) > 6 || Math.abs(dy) > 6)) {
      locking = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y';
    }
    if (locking === 'y') return;
    if (locking === 'x' && event && event.cancelable) event.preventDefault();
    deltaX = dx;
    const width = slider.offsetWidth || 1;
    const offset = (-index * 100) + (deltaX / width) * 100;
    track.style.transform = `translate3d(${offset}%, 0, 0)`;
  };

  const onPointerUp = () => {
    if (!dragging) return;
    dragging = false;
    slider.classList.remove('is-dragging');
    if (locking === 'x' && Math.abs(deltaX) >= SWIPE_THRESHOLD) {
      setIndex(index + (deltaX < 0 ? 1 : -1));
    } else {
      setIndex(index);
    }
    locking = null;
    deltaX = 0;
    restart();
  };

  track.addEventListener(
    'touchstart',
    (e) => {
      if (e.touches.length !== 1) return;
      onPointerDown(e.touches[0].clientX, e.touches[0].clientY);
    },
    { passive: true },
  );

  track.addEventListener(
    'touchmove',
    (e) => {
      if (e.touches.length !== 1) return;
      onPointerMove(e.touches[0].clientX, e.touches[0].clientY, e);
    },
    { passive: false },
  );

  track.addEventListener('touchend', onPointerUp, { passive: true });
  track.addEventListener('touchcancel', onPointerUp, { passive: true });

  slider.addEventListener('mouseenter', stop);
  slider.addEventListener('mouseleave', start);
  slider.addEventListener('focusin', stop);
  slider.addEventListener('focusout', (e) => {
    if (!slider.contains(e.relatedTarget)) start();
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else start();
  });

  setIndex(0, { animate: false });
  start();
}
