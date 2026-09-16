/** Мобільне розгортання пошуку + підказки + clear + recent. */

const RECENT_KEY = "svbeauty_search_recent";
const RECENT_LIMIT = 5;

function debounce(fn, delay = 280) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function normalizeQuery(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

function readRecent() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    const list = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list.filter((item) => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function pushRecent(query) {
  const q = normalizeQuery(query);
  if (q.length < 2) return;
  const next = [q, ...readRecent().filter((item) => item.toLowerCase() !== q.toLowerCase())].slice(
    0,
    RECENT_LIMIT
  );
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  } catch {
    /* ignore quota */
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function suggestLabels(suggest) {
  return {
    recent: (suggest && suggest.dataset.labelRecent) || "Нещодавні",
    empty: (suggest && suggest.dataset.labelEmpty) || "Нічого не знайдено",
    short:
      (suggest && suggest.dataset.labelShort) ||
      "Введіть щонайменше 2 символи для пошуку.",
    all: (suggest && suggest.dataset.labelAll) || "Усі результати",
  };
}

function initMobileSearchToggle(header) {
  if (!header) return;
  const openBtn = header.querySelector("[data-search-open]");
  const closeBtn = header.querySelector("[data-search-close]");
  const input = header.querySelector("[data-search-input]");

  const open = () => {
    header.classList.add("is-search-open");
    if (openBtn) openBtn.setAttribute("aria-expanded", "true");
    if (closeBtn) closeBtn.hidden = false;
    if (openBtn) openBtn.hidden = true;
    requestAnimationFrame(() => input && input.focus());
  };

  const close = () => {
    header.classList.remove("is-search-open");
    if (openBtn) {
      openBtn.hidden = false;
      openBtn.setAttribute("aria-expanded", "false");
    }
    if (closeBtn) closeBtn.hidden = true;
    const suggest = header.querySelector("[data-search-suggest]");
    if (suggest) {
      suggest.hidden = true;
      suggest.innerHTML = "";
    }
  };

  openBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    open();
  });
  closeBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    close();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && header.classList.contains("is-search-open")) close();
  });
}

function initSearchBox(root) {
  if (!root || root.dataset.searchReady === "1") return;
  root.dataset.searchReady = "1";

  const form = root.querySelector("[data-search-form]") || root.querySelector("form");
  const input = root.querySelector("[data-search-input]") || root.querySelector('input[type="search"]');
  const clearBtn = root.querySelector("[data-search-clear]");
  const suggest = root.querySelector("[data-search-suggest]");
  if (!form || !input) return;

  const suggestUrl = input.getAttribute("data-search-suggest-url") || "";
  let activeIndex = -1;
  let items = [];

  const syncClear = () => {
    if (!clearBtn) return;
    clearBtn.hidden = !normalizeQuery(input.value);
  };

  const hideSuggest = () => {
    if (!suggest) return;
    suggest.hidden = true;
    suggest.innerHTML = "";
    activeIndex = -1;
    items = [];
  };

  const renderRecent = () => {
    if (!suggest) return;
    const recent = readRecent();
    if (!recent.length) {
      hideSuggest();
      return;
    }
    const labels = suggestLabels(suggest);
    suggest.innerHTML = `
      <p class="search-suggest__label">${escapeHtml(labels.recent)}</p>
      ${recent
        .map(
          (q, index) => `
        <button type="button" class="search-suggest__item" role="option" data-index="${index}" data-recent="${escapeHtml(q)}">
          <span class="search-suggest__meta">${escapeHtml(q)}</span>
        </button>`
        )
        .join("")}
    `;
    suggest.hidden = false;
    items = [...suggest.querySelectorAll(".search-suggest__item")];
  };

  const renderResults = (results, query) => {
    if (!suggest) return;
    const labels = suggestLabels(suggest);
    if (!results.length) {
      suggest.innerHTML = `<p class="search-suggest__empty">${escapeHtml(labels.empty)}</p>`;
      suggest.hidden = false;
      items = [];
      return;
    }
    const allUrl = `${form.action}?q=${encodeURIComponent(query)}`;
    suggest.innerHTML = `
      ${results
        .map(
          (item, index) => `
        <a class="search-suggest__item" role="option" href="${escapeHtml(item.url)}" data-index="${index}">
          ${
            item.image
              ? `<img class="search-suggest__img" src="${escapeHtml(item.image)}" alt="" width="40" height="40" loading="lazy">`
              : `<span class="search-suggest__img search-suggest__img--empty" aria-hidden="true"></span>`
          }
          <span class="search-suggest__text">
            <span class="search-suggest__name">${escapeHtml(item.name)}</span>
            ${item.brand ? `<span class="search-suggest__meta">${escapeHtml(item.brand)}</span>` : ""}
          </span>
        </a>`
        )
        .join("")}
      <a class="search-suggest__more" href="${escapeHtml(allUrl)}">${escapeHtml(labels.all)}</a>
    `;
    suggest.hidden = false;
    items = [...suggest.querySelectorAll(".search-suggest__item")];
  };

  const renderShortHint = () => {
    if (!suggest) return;
    const labels = suggestLabels(suggest);
    suggest.innerHTML = `<p class="search-suggest__empty">${escapeHtml(labels.short)}</p>`;
    suggest.hidden = false;
    items = [];
    activeIndex = -1;
  };

  const fetchSuggest = debounce(async () => {
    const query = normalizeQuery(input.value);
    if (query.length < 2 || !suggestUrl) {
      if (!query) renderRecent();
      else if (query.length === 1) renderShortHint();
      else hideSuggest();
      return;
    }
    try {
      const response = await fetch(`${suggestUrl}?q=${encodeURIComponent(query)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;
      const data = await response.json();
      if (normalizeQuery(input.value) !== query) return;
      renderResults(data.results || [], query);
    } catch {
      hideSuggest();
    }
  }, 280);

  const setActive = (index) => {
    activeIndex = index;
    items.forEach((el, i) => el.classList.toggle("is-active", i === activeIndex));
  };

  clearBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    input.value = "";
    syncClear();
    hideSuggest();
    input.focus();
  });

  input.addEventListener("input", () => {
    syncClear();
    fetchSuggest();
  });

  input.addEventListener("focus", () => {
    const query = normalizeQuery(input.value);
    if (query.length >= 2) fetchSuggest();
    else if (query.length === 1) renderShortHint();
    else renderRecent();
  });

  form.addEventListener("submit", (event) => {
    const query = normalizeQuery(input.value);
    if (!query) {
      event.preventDefault();
      hideSuggest();
      input.focus();
      return;
    }
    pushRecent(query);
  });

  suggest?.addEventListener("click", (event) => {
    const recentBtn = event.target.closest("[data-recent]");
    if (recentBtn) {
      event.preventDefault();
      input.value = recentBtn.getAttribute("data-recent") || "";
      syncClear();
      pushRecent(input.value);
      form.submit();
    }
  });

  input.addEventListener("keydown", (event) => {
    if (!suggest || suggest.hidden || !items.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive(Math.min(activeIndex + 1, items.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive(Math.max(activeIndex - 1, 0));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      const el = items[activeIndex];
      if (!el) return;
      if (el.dataset.recent) {
        input.value = el.dataset.recent;
        pushRecent(input.value);
        form.submit();
      } else if (el.href) {
        pushRecent(input.value);
        window.location.href = el.href;
      }
    } else if (event.key === "Escape") {
      hideSuggest();
    }
  });

  document.addEventListener("click", (event) => {
    if (!root.contains(event.target)) hideSuggest();
  });

  syncClear();
}

export function initSearch() {
  document.querySelectorAll("[data-header]").forEach(initMobileSearchToggle);
  document.querySelectorAll("[data-search]").forEach(initSearchBox);
}
