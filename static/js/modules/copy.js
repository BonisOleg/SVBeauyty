/** Копіювання реквізитів. Fallback потрібен для http та старих iOS Safari. */

function fallbackCopy(text) {
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.top = '-1000px';
  document.body.appendChild(area);

  const selection = document.getSelection();
  const previous = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;

  area.select();
  area.setSelectionRange(0, area.value.length);
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch (error) {
    ok = false;
  }
  document.body.removeChild(area);
  if (previous) {
    selection.removeAllRanges();
    selection.addRange(previous);
  }
  return ok;
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      return fallbackCopy(text);
    }
  }
  return fallbackCopy(text);
}

function showToast(message) {
  let toast = document.querySelector('[data-copy-toast]');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'copy-toast';
    toast.setAttribute('data-copy-toast', '');
    toast.setAttribute('role', 'status');
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('is-visible');
  clearTimeout(toast.dataset.timer);
  toast.dataset.timer = setTimeout(() => toast.classList.remove('is-visible'), 2000);
}

export function initCopy() {
  document.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-copy]');
    if (!button) return;
    event.preventDefault();

    const value = button.dataset.copy;
    const text = value || collectAll(button);
    if (!text) return;

    const ok = await copyText(text);
    showToast(ok ? button.dataset.copyDone || 'Скопійовано' : 'Не вдалось скопіювати');
    if (ok) {
      button.classList.add('is-copied');
      setTimeout(() => button.classList.remove('is-copied'), 1600);
    }
  });
}

function collectAll(button) {
  const scope = button.closest('[data-copy-scope]');
  if (!scope) return '';
  return Array.from(scope.querySelectorAll('[data-copy-line]'))
    .map((el) => `${el.dataset.copyLine}: ${el.textContent.trim()}`)
    .join('\n');
}
