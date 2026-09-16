/** Кастомний вертикальний бігунок для .pdp-specs (≥1024). */
const DESKTOP_MQ = '(min-width: 1024px)';

function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n));
}

function bindSpecsScroll(block) {
  if (block.dataset.specsScrollReady === '1') return;

  const viewport = block.querySelector('.pdp-specs__viewport');
  const scroller = block.querySelector('[data-specs-scroll]');
  const rail = block.querySelector('[data-specs-rail]');
  const thumb = block.querySelector('[data-specs-thumb]');
  if (!viewport || !scroller || !rail || !thumb) return;

  block.dataset.specsScrollReady = '1';

  const mq = window.matchMedia(DESKTOP_MQ);
  let drag = null;
  let raf = 0;

  const sync = () => {
    if (!mq.matches) {
      rail.hidden = true;
      return;
    }

    const viewH = scroller.clientHeight;
    const scrollH = scroller.scrollHeight;
    const maxScroll = scrollH - viewH;

    if (maxScroll <= 1) {
      rail.hidden = true;
      thumb.style.height = '';
      thumb.style.transform = '';
      return;
    }

    rail.hidden = false;
    const railH = rail.clientHeight || viewH;
    const thumbH = clamp((viewH / scrollH) * railH, 28, railH);
    const maxTop = Math.max(0, railH - thumbH);
    const top = maxScroll > 0 ? (scroller.scrollTop / maxScroll) * maxTop : 0;

    thumb.style.height = `${thumbH}px`;
    thumb.style.transform = `translateY(${top}px)`;
  };

  const schedule = () => {
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => {
      raf = 0;
      sync();
    });
  };

  const scheduleAfterLayout = () => {
    schedule();
    window.setTimeout(sync, 0);
    window.setTimeout(sync, 50);
  };

  scroller.addEventListener('scroll', schedule, { passive: true });
  block.querySelectorAll('[data-tab-btn]').forEach((btn) => {
    btn.addEventListener('click', () => {
      scroller.scrollTop = 0;
      scheduleAfterLayout();
    });
  });

  if (typeof ResizeObserver !== 'undefined') {
    const ro = new ResizeObserver(scheduleAfterLayout);
    ro.observe(scroller);
    ro.observe(viewport);
  }

  window.addEventListener('resize', scheduleAfterLayout, { passive: true });
  if (mq.addEventListener) mq.addEventListener('change', scheduleAfterLayout);
  else if (mq.addListener) mq.addListener(scheduleAfterLayout);

  const onPointerMove = (e) => {
    if (!drag) return;
    e.preventDefault();
    const railH = rail.clientHeight;
    const thumbH = thumb.offsetHeight;
    const maxTop = Math.max(0, railH - thumbH);
    const y = e.clientY - drag.railTop - drag.offset;
    const top = clamp(y, 0, maxTop);
    const maxScroll = scroller.scrollHeight - scroller.clientHeight;
    scroller.scrollTop = maxTop > 0 ? (top / maxTop) * maxScroll : 0;
  };

  const onPointerUp = () => {
    if (!drag) return;
    drag = null;
    thumb.classList.remove('is-dragging');
    window.removeEventListener('pointermove', onPointerMove);
    window.removeEventListener('pointerup', onPointerUp);
    window.removeEventListener('pointercancel', onPointerUp);
  };

  thumb.addEventListener('pointerdown', (e) => {
    if (!mq.matches || rail.hidden) return;
    e.preventDefault();
    const rect = rail.getBoundingClientRect();
    const thumbTop = thumb.getBoundingClientRect().top - rect.top;
    drag = { railTop: rect.top, offset: e.clientY - rect.top - thumbTop };
    thumb.classList.add('is-dragging');
    if (thumb.setPointerCapture) thumb.setPointerCapture(e.pointerId);
    window.addEventListener('pointermove', onPointerMove, { passive: false });
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
  });

  rail.addEventListener('pointerdown', (e) => {
    if (!mq.matches || rail.hidden || e.target === thumb) return;
    const rect = rail.getBoundingClientRect();
    const thumbH = thumb.offsetHeight;
    const maxTop = Math.max(0, rail.clientHeight - thumbH);
    const top = clamp(e.clientY - rect.top - thumbH / 2, 0, maxTop);
    const maxScroll = scroller.scrollHeight - scroller.clientHeight;
    scroller.scrollTop = maxTop > 0 ? (top / maxTop) * maxScroll : 0;
  });

  scheduleAfterLayout();
}

export function initPdpSpecsScroll(root = document) {
  root.querySelectorAll('.pdp-specs').forEach(bindSpecsScroll);
}
