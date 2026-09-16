/** Sticky chrome: hide promo strip on scroll down, show on scroll up (Malyar pattern). */
export function initTopbarScroll() {
  const chrome = document.querySelector('[data-site-chrome]');
  const promo = chrome && chrome.querySelector('.promo');
  if (!chrome || !promo || chrome.dataset.topbarBound === '1') return;
  chrome.dataset.topbarBound = '1';

  /* Hide потребує більшого «наміру» вниз; show — вгору або майже top.
     Lock після toggle глушить зворотний зв’язок від зміни висоти sticky. */
  const HIDE_AFTER = 48;
  const SHOW_AFTER = 72;
  const TOP = 16;
  /* трохи довше за CSS transition (0.28s), щоб layout-стрибок не гойдав стан */
  const LOCK_MS = 320;

  let lastY = window.pageYOffset || 0;
  let acc = 0;
  let hidden = false;
  let ticking = false;
  let lockedUntil = 0;

  const yPos = () => {
    const y = window.pageYOffset || document.documentElement.scrollTop || 0;
    return y < 0 ? 0 : y;
  };

  const setHidden = (next) => {
    if (next === hidden) return;
    hidden = next;
    chrome.classList.toggle('is-topbar-hidden', hidden);
    promo.setAttribute('aria-hidden', hidden ? 'true' : 'false');
    if (hidden) promo.setAttribute('inert', '');
    else promo.removeAttribute('inert');
    lockedUntil = performance.now() + LOCK_MS;
    acc = 0;
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        lastY = yPos();
        acc = 0;
      });
    });
  };

  const update = () => {
    ticking = false;
    const y = yPos();
    const now = performance.now();
    if (now < lockedUntil) {
      lastY = y;
      acc = 0;
      return;
    }

    const delta = y - lastY;
    lastY = y;

    if (y <= TOP) {
      acc = 0;
      setHidden(false);
      return;
    }

    /* Ігноруємо субпіксельний шум трекпада / iOS */
    if (delta > -0.5 && delta < 0.5) return;

    if ((acc > 0 && delta < 0) || (acc < 0 && delta > 0)) acc = 0;
    acc += delta;

    if (!hidden && acc >= HIDE_AFTER) {
      setHidden(true);
    } else if (hidden && acc <= -SHOW_AFTER) {
      setHidden(false);
    }
  };

  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  };

  window.addEventListener('scroll', onScroll, { passive: true });
}
