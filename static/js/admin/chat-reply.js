(() => {
  const boot = () => {
    const root = document.querySelector("[data-admin-chat]");
    if (!root || root.dataset.ready === "1") return;
    root.dataset.ready = "1";

    const body = root.querySelector("[data-admin-chat-body]");
    const empty = root.querySelector("[data-admin-chat-empty]");
    const form = root.querySelector("[data-admin-chat-form]");
    const input = root.querySelector("[data-admin-chat-input]");
    const errorEl = root.querySelector("[data-admin-chat-error]");
    const messagesUrl = root.dataset.messagesUrl;
    const replyUrl = root.dataset.replyUrl;
    const deleteUrlTemplate = root.dataset.deleteUrlTemplate || "";
    const pollMs = Math.max(3000, parseInt(root.dataset.pollMs || "6000", 10) || 6000);
    const closed = root.dataset.closed === "1";
    const labelCustomer = root.dataset.labelCustomer || "Клієнт";
    const labelManager = root.dataset.labelManager || "Менеджер";
    const labelDelete = root.dataset.labelDelete || "Видалити";
    const confirmDelete = root.dataset.confirmDelete || "Видалити це повідомлення?";

    let loading = false;
    let pollTimer = null;

    const csrfToken = () => {
      const field = form && form.querySelector("[name=csrfmiddlewaretoken]");
      if (field && field.value) return field.value;
      const cookie = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
      return cookie ? decodeURIComponent(cookie[1]) : "";
    };

    const showError = (text) => {
      if (!errorEl) return;
      if (!text) {
        errorEl.hidden = true;
        errorEl.textContent = "";
        return;
      }
      errorEl.hidden = false;
      errorEl.textContent = text;
    };

    const escapeHtml = (value) =>
      String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");

    const deleteUrlFor = (id) =>
      deleteUrlTemplate ? deleteUrlTemplate.replace("{id}", String(id)) : "";

    const renderMessageHtml = (msg) => {
      const isManager = msg.author === "manager";
      const deleted = !!msg.is_deleted;
      const author = escapeHtml(
        msg.author_label || (isManager ? labelManager : labelCustomer)
      );
      const text = escapeHtml(msg.text || "");
      const time = escapeHtml(msg.time || "");
      const delBtn =
        !closed && msg.can_delete && !deleted
          ? `<button type="button" class="admin-chat__delete" data-admin-chat-delete data-msg-id="${msg.id}" aria-label="${escapeHtml(labelDelete)}" title="${escapeHtml(labelDelete)}">×</button>`
          : "";
      return (
        `<span class="admin-chat__author">${author}</span>` +
        delBtn +
        `<div class="admin-chat__text">${text}</div>` +
        `<span class="admin-chat__time">${time}</span>`
      );
    };

    const upsertMessage = (msg, { scroll = false } = {}) => {
      if (!body || !msg || !msg.id) return;
      if (empty) empty.hidden = true;

      let el = body.querySelector(`[data-msg-id="${msg.id}"]`);
      const isManager = msg.author === "manager";
      const deleted = !!msg.is_deleted;
      if (!el) {
        el = document.createElement("div");
        el.dataset.msgId = String(msg.id);
        body.appendChild(el);
      }
      el.className =
        `admin-chat__msg admin-chat__msg--${isManager ? "manager" : "customer"}` +
        (deleted ? " admin-chat__msg--deleted" : "");
      el.innerHTML = renderMessageHtml(msg);
      if (scroll) body.scrollTop = body.scrollHeight;
    };

    const fetchMessages = async ({ scroll = false, initial = false } = {}) => {
      if (!messagesUrl || loading) return;
      loading = true;
      try {
        const response = await fetch(messagesUrl, {
          headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin",
        });
        if (!response.ok) return;
        const data = await response.json();
        const list = Array.isArray(data.messages) ? data.messages : [];
        list.forEach((msg) => upsertMessage(msg, { scroll: false }));
        if (initial && list.length === 0 && empty) empty.hidden = false;
        if (scroll || initial) body.scrollTop = body.scrollHeight;
      } catch (_err) {
        // silent poll failures
      } finally {
        loading = false;
      }
    };

    const sendReply = async () => {
      if (closed || !replyUrl || !input) return;
      const text = (input.value || "").trim();
      if (!text) {
        showError(root.dataset.errorEmpty || "");
        input.focus();
        return;
      }
      showError("");
      const btn = root.querySelector("[data-admin-chat-send]");
      if (btn) btn.disabled = true;
      try {
        const bodyData = new URLSearchParams();
        bodyData.set("text", text);
        const response = await fetch(replyUrl, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfToken(),
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          },
          credentials: "same-origin",
          body: bodyData.toString(),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          showError(data.error || root.dataset.errorSend || "");
          return;
        }
        if (data.message) upsertMessage(data.message, { scroll: true });
        try {
          new BroadcastChannel("svbeauty-chat").postMessage({ type: "chat-updated" });
        } catch (_err) {
          /* ignore */
        }
        input.value = "";
        input.focus();
      } catch (_err) {
        showError(root.dataset.errorSend || "");
      } finally {
        if (btn && !closed) btn.disabled = false;
      }
    };

    const deleteMessage = async (messageId) => {
      const url = deleteUrlFor(messageId);
      if (!url) return;
      if (!window.confirm(confirmDelete)) return;
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfToken(),
          },
          credentials: "same-origin",
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          showError(data.error || root.dataset.errorSend || "");
          return;
        }
        if (data.message) upsertMessage(data.message, { scroll: false });
        try {
          new BroadcastChannel("svbeauty-chat").postMessage({ type: "chat-updated" });
        } catch (_err) {
          /* ignore */
        }
      } catch (_err) {
        showError(root.dataset.errorSend || "");
      }
    };

    if (form) {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        sendReply();
      });
    }

    if (input) {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
          event.preventDefault();
          sendReply();
        }
      });
    }

    if (body) {
      body.addEventListener("click", (event) => {
        const btn = event.target.closest("[data-admin-chat-delete]");
        if (!btn) return;
        event.preventDefault();
        deleteMessage(btn.dataset.msgId);
      });
    }

    fetchMessages({ initial: true, scroll: true }).then(() => {
      pollTimer = window.setInterval(() => {
        if (document.hidden) return;
        fetchMessages({ scroll: false });
      }, pollMs);
    });

    window.addEventListener(
      "beforeunload",
      () => {
        if (pollTimer) window.clearInterval(pollTimer);
      },
      { once: true }
    );
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
