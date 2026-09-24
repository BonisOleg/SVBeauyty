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
  let queuedHistory = null;
  const draftUrls = [];

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

  const fileInput = root.querySelector("[data-chat-file]");
  const picked = root.querySelector("[data-chat-picked]");
  const rulesText = root.querySelector("[data-chat-hint]")?.textContent || "";
  const allowedExt = new Set(["jpg", "jpeg", "png", "webp", "pdf"]);

  const previewLabels = () => ({
    close: root.dataset.previewClose || "Закрити перегляд",
    download: root.dataset.previewDownload || "Завантажити",
  });

  const openPreview = (trigger) => {
    if (!trigger || typeof window.svOpenFilePreview !== "function") return;
    window.svOpenFilePreview({
      url: trigger.dataset.previewUrl,
      name: trigger.dataset.previewName,
      kind: trigger.dataset.previewKind,
      labels: previewLabels(),
    });
  };

  const appendFiles = (el, files, prefix) => {
    if (!files || !files.length) return;
    const wrap = document.createElement("span");
    wrap.className = `${prefix}__files`;
    files.forEach((file) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `${prefix}__file${file.kind === "pdf" ? ` ${prefix}__file--pdf` : ""}`;
      button.dataset.chatPreview = "1";
      button.dataset.previewUrl = file.url;
      button.dataset.previewName = file.name || "";
      button.dataset.previewKind = file.kind || "image";
      if (file.kind === "image") {
        const img = document.createElement("img");
        img.src = file.url;
        img.alt = file.name || "";
        button.appendChild(img);
      } else {
        button.textContent = file.name || "PDF";
      }
      wrap.appendChild(button);
    });
    el.appendChild(wrap);
  };

  const selectedFiles = () => (fileInput && fileInput.files ? Array.from(fileInput.files) : []);

  const fileError = () => {
    const files = selectedFiles();
    if (files.length > 3) return rulesText;
    for (const file of files) {
      const ext = (file.name.split(".").pop() || "").toLowerCase();
      if (!allowedExt.has(ext) || file.size > 5 * 1024 * 1024) return rulesText;
    }
    return "";
  };

  const removeLabel = root.dataset.chatRemoveFile || "Прибрати файл";

  const syncFiles = (files) => {
    if (!fileInput) return;
    const bag = new DataTransfer();
    files.forEach((file) => bag.items.add(file));
    fileInput.files = bag.files;
    renderPicked();
  };

  const renderPicked = () => {
    if (!picked) return;
    draftUrls.splice(0).forEach((url) => URL.revokeObjectURL(url));
    picked.replaceChildren();
    const files = selectedFiles();
    picked.hidden = files.length === 0;
    files.forEach((file, index) => {
      const item = document.createElement("div");
      item.className = "chat__draft-item";
      if ((file.type || "").startsWith("image/")) {
        const img = document.createElement("img");
        const url = URL.createObjectURL(file);
        draftUrls.push(url);
        img.src = url;
        img.alt = file.name;
        item.appendChild(img);
      }
      const name = document.createElement("span");
      name.className = "chat__draft-name";
      name.textContent = file.name;
      item.appendChild(name);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "chat__draft-remove";
      remove.setAttribute("aria-label", removeLabel);
      remove.textContent = "×";
      remove.addEventListener("click", () => {
        syncFiles(selectedFiles().filter((_, fileIndex) => fileIndex !== index));
      });
      item.appendChild(remove);
      picked.appendChild(item);
    });
  };

  if (fileInput) fileInput.addEventListener("change", renderPicked);

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
    const prevText = textNode ? textNode.textContent : "";
    const prevFiles = el.dataset.files || "";
    const nextFiles = (message.attachments || []).map((file) => file.url).join("|");
    const changed =
      created || prevDeleted !== deleted || prevText !== (message.text || "") || prevFiles !== nextFiles;

    el.className = nextClass;
    el.dataset.files = nextFiles;
    el.replaceChildren();
    if (deleted) {
      const note = document.createElement("span");
      note.className = "chat__deleted";
      note.textContent = message.text;
      el.appendChild(note);
    } else if (message.text) {
      const text = document.createElement("span");
      text.className = "chat__text";
      text.textContent = message.text;
      el.appendChild(text);
    }
    if (!deleted) appendFiles(el, message.attachments, "chat");
    const time = document.createElement("span");
    time.className = "chat__time";
    time.textContent = message.time || "";
    el.appendChild(time);

    lastId = Math.max(lastId, Number(message.id) || 0);
    return changed;
  };

  const loadHistory = async ({ scrollIfNew = true } = {}) => {
    if (!urls.history) return;
    if (loading) {
      queuedHistory = { scrollIfNew: scrollIfNew || Boolean(queuedHistory && queuedHistory.scrollIfNew) };
      return;
    }
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
      if (queuedHistory) {
        const next = queuedHistory;
        queuedHistory = null;
        loadHistory(next);
      }
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

  if (body) {
    body.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-chat-preview]");
      if (!trigger) return;
      event.preventDefault();
      openPreview(trigger);
    });
  }

  if (hasHtmx && form) {
    form.addEventListener(
      "submit",
      (event) => {
        const problem = fileError();
        const hasText = Boolean((input.value || "").trim());
        const hasFiles = selectedFiles().length > 0;
        const needContacts = lead && !lead.hidden && !contactsFilled();
        if (!problem && (hasText || hasFiles) && !needContacts) return;
        event.preventDefault();
        event.stopPropagation();
        const sendBtn = form.querySelector("[type=submit]");
        if (sendBtn) sendBtn.disabled = false;
        if (needContacts && !problem) {
          errorBox.textContent = contactsError;
          (nameInput?.value || "").trim() ? phoneInput?.focus() : nameInput?.focus();
          return;
        }
        errorBox.textContent = problem || rulesText;
      },
      true
    );

    form.addEventListener("htmx:afterRequest", (event) => {
      const sendBtn = form.querySelector("[type=submit]");
      if (sendBtn) sendBtn.disabled = false;
      if (!event.detail.successful) {
        const xhr = event.detail.xhr;
        const bodyText = (xhr && xhr.responseText || "").trim();
        errorBox.textContent = bodyText || root.dataset.chatErrorText || "";
        return;
      }
      errorBox.textContent = "";
      input.value = "";
      if (fileInput) fileInput.value = "";
      renderPicked();
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
