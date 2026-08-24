/** Копіювання реквізитів. Fallback потрібен для http та старих iOS Safari. */

function fallbackCopy(text) {
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.top = '-1000px';
  area.style.opacity = '0';
  document.body.appendChild(area);

  const selection = document.getSelection();
  const previous = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;

  area.focus();
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

function collectAll(scopeRoot) {
  const scope = scopeRoot.closest('[data-copy-scope]');
  if (!scope) return '';
  return Array.from(scope.querySelectorAll('[data-copy-line]'))
    .map((el) => `${el.dataset.copyLine}: ${el.textContent.trim()}`)
    .join('\n');
}

function markCopied(button) {
  if (!button) return;
  button.classList.add('is-copied');
  setTimeout(() => button.classList.remove('is-copied'), 1600);
}

function resolveFromRow(row) {
  const button = row.querySelector('.requisite__copy[data-copy]');
  const line = row.querySelector('[data-copy-line]');
  const text = (button?.dataset.copy || line?.textContent || '').trim();
  return {
    text,
    done: button?.dataset.copyDone || 'Скопійовано',
    button,
  };
}

async function handleCopy({ text, done, button }) {
  if (!text) return;
  const ok = await copyText(text);
  showToast(ok ? done : 'Не вдалось скопіювати');
  if (ok) markCopied(button);
}

export function initCopy() {
  document.addEventListener('click', async (event) => {
    const allBtn = event.target.closest('.requisites__all[data-copy]');
    if (allBtn) {
      event.preventDefault();
      await handleCopy({
        text: collectAll(allBtn),
        done: allBtn.dataset.copyDone || 'Скопійовано',
        button: allBtn,
      });
      return;
    }

    const copyBtn = event.target.closest('.requisite__copy[data-copy]');
    if (copyBtn) {
      event.preventDefault();
      const row = copyBtn.closest('.requisite');
      await handleCopy(row ? resolveFromRow(row) : {
        text: (copyBtn.dataset.copy || '').trim(),
        done: copyBtn.dataset.copyDone || 'Скопійовано',
        button: copyBtn,
      });
      return;
    }

    const row = event.target.closest('.requisite');
    if (!row || !row.closest('[data-copy-scope]')) return;
    event.preventDefault();
    await handleCopy(resolveFromRow(row));
  });
}
