(() => {
  const boot = () => {
    const root = document.querySelector("[data-admin-alerts]");
    if (!root || root.dataset.ready === "1") return;
    root.dataset.ready = "1";

    const url = root.dataset.adminAlertsUrl;
    const pollMs = Math.max(10000, parseInt(root.dataset.adminAlertsPoll || "30000", 10) || 30000);
    if (!url) return;

    const totalEl = root.querySelector("[data-admin-alerts-total]");
    const emptyEl = root.querySelector("[data-admin-alerts-empty]");
    const keys = ["orders", "requests", "messages"];

    const escapeHtml = (value) =>
      String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");

    const setBadge = (key, count) => {
      const n = Number(count) || 0;
      document.querySelectorAll(`[data-admin-alert-badge="${key}"]`).forEach((el) => {
        el.textContent = String(n);
        if (n > 0) el.removeAttribute("hidden");
        else el.setAttribute("hidden", "");
      });
    };

    const setTotal = (total) => {
      const n = Number(total) || 0;
      if (!totalEl) return;
      totalEl.textContent = n > 99 ? "99+" : String(n);
      if (n > 0) totalEl.removeAttribute("hidden");
      else totalEl.setAttribute("hidden", "");
    };

    const renderList = (key, items) => {
      const list = root.querySelector(`[data-admin-alerts-list="${key}"]`);
      if (!list) return;
      list.innerHTML = (items || [])
        .map(
          (item) =>
            `<li><a class="admin-alerts__item" href="${escapeHtml(item.url)}">` +
            `<span class="admin-alerts__item-title">${escapeHtml(item.title)}</span>` +
            `<span class="admin-alerts__item-meta">${escapeHtml(item.meta || "")}</span>` +
            `<span class="admin-alerts__item-time">${escapeHtml(item.time || "")}</span>` +
            `</a></li>`
        )
        .join("");
    };

    const applyPayload = (data) => {
      if (!data) return;
      setTotal(data.total);
      let any = false;
      keys.forEach((key) => {
        const count = Number(data[key]) || 0;
        setBadge(key, count);
        const section = root.querySelector(`[data-admin-alerts-section="${key}"]`);
        const countEl = root.querySelector(`[data-admin-alerts-section-count="${key}"]`);
        const linkEl = root.querySelector(`[data-admin-alerts-section-link="${key}"]`);
        if (countEl) countEl.textContent = String(count);
        if (linkEl && data.links && data.links[key]) linkEl.href = data.links[key];
        renderList(key, (data.feed && data.feed[key]) || []);
        if (section) {
          if (count > 0) {
            section.removeAttribute("hidden");
            any = true;
          } else {
            section.setAttribute("hidden", "");
          }
        }
      });
      if (emptyEl) {
        if (any) emptyEl.setAttribute("hidden", "");
        else emptyEl.removeAttribute("hidden");
      }
    };

    let timer = null;
    let loading = false;

    const fetchAlerts = async () => {
      if (loading || document.hidden) return;
      loading = true;
      try {
        const res = await fetch(url, {
          credentials: "same-origin",
          headers: { Accept: "application/json", "Cache-Control": "no-store" },
        });
        if (!res.ok) return;
        const data = await res.json();
        applyPayload(data);
      } catch (_err) {
        /* ignore transient network errors */
      } finally {
        loading = false;
      }
    };

    const schedule = () => {
      if (timer) window.clearInterval(timer);
      timer = window.setInterval(fetchAlerts, pollMs);
    };

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) fetchAlerts();
    });

    fetchAlerts();
    schedule();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
