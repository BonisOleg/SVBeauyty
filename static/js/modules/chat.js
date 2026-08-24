const POLL_INTERVAL = 12000;

export function initChat() {
  const root = document.querySelector('[data-chat]');
  if (!root) return;

  const toggle = root.querySelector('[data-chat-toggle]');
  const close = root.querySelector('[data-chat-close]');
  const body = root.querySelector('[data-chat-body]');
  const form = root.querySelector('[data-chat-form]');
  const input = root.querySelector('[data-chat-input]');
  const errorBox = root.querySelector('[data-chat-error]');
  const urls = { history: root.dataset.chatHistoryUrl };
  const hasHtmx = typeof window.htmx !== 'undefined';

  let lastId = 0;
  let timer = null;

  const scrollDown = () => { body.scrollTop = body.scrollHeight; };

  const appendMessage = (message) => {
    if (message.id <= lastId) return;
    lastId = message.id;
    if (body.querySelector(`[data-msg-id="${message.id}"]`)) return;
    const el = document.createElement('div');
    el.className = `chat__msg chat__msg--${message.author}`;
    el.dataset.msgId = message.id;
    el.textContent = message.text;
    const time = document.createElement('span');
    time.className = 'chat__time';
    time.textContent = message.time;
    el.appendChild(time);
    body.appendChild(el);
  };

  const loadHistory = async () => {
    try {
      const response = await fetch(urls.history, { credentials: 'same-origin' });
      if (!response.ok) return;
      const data = await response.json();
      const before = lastId;
      data.messages.forEach(appendMessage);
      if (lastId !== before) scrollDown();
    } catch (error) {
      /* тихо */
    }
  };

  const startPolling = () => {
    if (timer) return;
    timer = setInterval(loadHistory, POLL_INTERVAL);
  };

  const stopPolling = () => {
    clearInterval(timer);
    timer = null;
  };

  toggle.addEventListener('click', () => {
    const open = !root.classList.contains('is-open');
    root.classList.toggle('is-open', open);
    if (open) {
      loadHistory().then(scrollDown);
      startPolling();
      if (window.matchMedia('(min-width: 601px)').matches) input.focus();
    } else {
      stopPolling();
    }
  });

  if (close) {
    close.addEventListener('click', () => {
      root.classList.remove('is-open');
      stopPolling();
    });
  }

  if (hasHtmx && form) {
    form.addEventListener('htmx:afterRequest', (event) => {
      if (!event.detail.successful) {
        errorBox.textContent = root.dataset.chatErrorText || '';
        return;
      }
      errorBox.textContent = '';
      input.value = '';
      scrollDown();
      startPolling();
    });
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopPolling();
    else if (root.classList.contains('is-open')) startPolling();
  });
}
