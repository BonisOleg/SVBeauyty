const POLL_INTERVAL = 4000;
const CHAT_BUS = "svbeauty-chat";

export function initChat() {
  const root = document.querySelector("[data-chat]");
  if (!root) return;

  const toggle = root.querySelector("[data-chat-toggle]");
  const close = root.querySelector("[data-chat-close]");
  const body = root.querySelector("[data-chat-body]");
  const form = root.querySelector("[data-chat-form]");
  const input = root.querySelector("[data-chat-input]");
  const errorBox = root.querySelector("[data-chat-error]");
  const lead = root.querySelector("[data-chat-lead]");
  const nameInput = root.querySelector("[data-chat-name]");
  const phoneInput = root.querySelector("[data-chat-phone]");
  const urls = { history: root.dataset.chatHistoryUrl };
  const contactsError =
    root.dataset.chatContactsError || "Вкажіть імʼя та телефон перед першим повідомленням.";
  const hasHtmx = typeof window.htmx !== "undefined";

  let lastId = 0;
  let timer = null;
  let loading = false;

  const scrollDown = () => {
    body.scrollTop = body.scrollHeight;
  };

  const setLeadVisible = (visible) => {
    if (!lead) return;
    lead.hidden = !visible;
    [nameInput, phoneInput].forEach((field) => {
      if (!field) return;
      if (visible) field.setAttribute("required", "required");
      else field.removeAttribute("required");
    });
  };

  const hideLead = () => setLeadVisible(false);

  const contactsFilled = () =>
    Boolean((nameInput?.value || "").trim() && (phoneInput?.value || "").trim());

  const upsertMessage = (message) => {
    if (!message || message.id == null) return false;
    const id = String(message.id);
    const deleted = !!message.is_deleted;
    let el = body.querySelector(`[data-msg-id="${id}"]`);
    let created = false;
    if (!el) {
      el = document.createElement("div");
      el.dataset.msgId = id;
      body.appendChild(el);
      created = true;
    }

    const nextClass = `chat__msg chat__msg--${message.author}${
      deleted ? " chat__msg--deleted" : ""
    }`;
    const prevDeleted = el.classList.contains("chat__msg--deleted");
    const textNode = el.querySelector(".chat__deleted, .chat__text");
    const prevText = textNode ? textNode.textContent : el.childNodes[0]?.textContent || "";
    const changed = created || prevDeleted !== deleted || prevText !== (message.text || "");

    el.className = nextClass;
    el.replaceChildren();
    if (deleted) {
      const note = document.createElement("span");
      note.className = "chat__deleted";
      note.textContent = message.text;
      el.appendChild(note);
    } else {
      const text = document.createElement("span");
      text.className = "chat__text";
      text.textContent = message.text;
      el.appendChild(text);
    }
    const time = document.createElement("span");
    time.className = "chat__time";
    time.textContent = message.time || "";
    el.appendChild(time);

    lastId = Math.max(lastId, Number(message.id) || 0);
    return changed;
  };

  const loadHistory = async ({ scrollIfNew = true } = {}) => {
    if (!urls.history || loading) return;
    loading = true;
    try {
      const response = await fetch(
        `${urls.history}${urls.history.includes("?") ? "&" : "?"}ts=${Date.now()}`,
        {
          credentials: "same-origin",
          cache: "no-store",
          headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
        }
      );
      if (!response.ok) return;
      const data = await response.json();
      let changed = false;
      (data.messages || []).forEach((msg) => {
        if (upsertMessage(msg)) changed = true;
      });
      if (data.needs_contacts === false) hideLead();
      else if ((data.messages || []).length > 0) hideLead();
      if (changed && scrollIfNew) scrollDown();
    } catch (_error) {
      /* тихо */
    } finally {
      loading = false;
    }
  };

  const startPolling = () => {
    if (timer) return;
    timer = setInterval(() => {
      if (document.hidden) return;
      loadHistory({ scrollIfNew: false });
    }, POLL_INTERVAL);
  };

  const stopPolling = () => {
    clearInterval(timer);
    timer = null;
  };

  toggle.addEventListener("click", () => {
    const open = !root.classList.contains("is-open");
    root.classList.toggle("is-open", open);
    if (open) {
      loadHistory({ scrollIfNew: true });
      startPolling();
      if (window.matchMedia("(min-width: 601px)").matches) {
        if (lead && !lead.hidden && nameInput) nameInput.focus();
        else input.focus();
      }
    } else {
      stopPolling();
    }
  });

  if (close) {
    close.addEventListener("click", () => {
      root.classList.remove("is-open");
      stopPolling();
    });
  }

  if (hasHtmx && form) {
    form.addEventListener("htmx:beforeRequest", (event) => {
      if (!lead || lead.hidden) return;
      if (contactsFilled()) {
        errorBox.textContent = "";
        return;
      }
      event.preventDefault();
      errorBox.textContent = contactsError;
      (nameInput?.value || "").trim() ? phoneInput?.focus() : nameInput?.focus();
    });

    form.addEventListener("htmx:afterRequest", (event) => {
      if (!event.detail.successful) {
        const xhr = event.detail.xhr;
        const bodyText = (xhr && xhr.responseText || "").trim();
        errorBox.textContent = bodyText || root.dataset.chatErrorText || "";
        return;
      }
      errorBox.textContent = "";
      input.value = "";
      hideLead();
      scrollDown();
      loadHistory({ scrollIfNew: true });
      startPolling();
    });
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopPolling();
      return;
    }
    if (root.classList.contains("is-open")) {
      loadHistory({ scrollIfNew: false });
      startPolling();
    }
  });

  try {
    const bus = new BroadcastChannel(CHAT_BUS);
    bus.addEventListener("message", (event) => {
      if (!root.classList.contains("is-open")) return;
      if (event?.data?.type === "chat-updated") {
        loadHistory({ scrollIfNew: false });
      }
    });
  } catch (_err) {
    /* BroadcastChannel може бути недоступний */
  }
}
