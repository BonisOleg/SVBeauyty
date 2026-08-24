/** Flash-повідомлення Django: автозакриття + кнопка. */

const AUTO_MS = 4000;
const AUTO_TAGS = new Set(['success', 'info']);

function dismissMessage(el) {
  if (!el || el.dataset.dismissing === '1') return;
  el.dataset.dismissing = '1';
  el.classList.add('is-leaving');
  const remove = () => {
    const wrap = el.closest('.messages');
    el.remove();
    if (wrap && !wrap.querySelector('.message')) wrap.remove();
  };
  el.addEventListener('transitionend', remove, { once: true });
  setTimeout(remove, 320);
}

export function initMessages() {
  const root = document.querySelector('[data-messages]');
  if (!root) return;

  root.querySelectorAll('[data-message]').forEach((el) => {
    const close = el.querySelector('[data-message-close]');
    if (close) {
      close.addEventListener('click', (event) => {
        event.preventDefault();
        dismissMessage(el);
      });
    }

    const tag = (el.dataset.messageTag || '').split(/\s+/)[0];
    if (!AUTO_TAGS.has(tag)) return;

    let timer = setTimeout(() => dismissMessage(el), AUTO_MS);
    el.addEventListener('mouseenter', () => clearTimeout(timer));
    el.addEventListener('mouseleave', () => {
      clearTimeout(timer);
      timer = setTimeout(() => dismissMessage(el), AUTO_MS);
    });
    el.addEventListener(
      'focusin',
      () => clearTimeout(timer),
    );
  });
}
