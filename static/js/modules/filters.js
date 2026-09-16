/** Кастомний select сортування + згортання опцій фільтрів (по 3). */

function closestForm(el) {
  return el && el.closest("form");
}

function collapseLabels(group) {
  const form = closestForm(group);
  return {
    more: (form && form.dataset.filtersMoreLabel) || "Показати ще",
    less: (form && form.dataset.filtersLessLabel) || "Згорнути",
  };
}

function initFilterSortSelect(root) {
  if (!root || root.dataset.ready === "1") return;
  root.dataset.ready = "1";

  const trigger = root.querySelector("[data-filters-select-trigger]");
  const list = root.querySelector("[data-filters-select-list]");
  const label = root.querySelector("[data-filters-select-label]");
  const input = root.querySelector("[data-filters-select-input]");
  if (!trigger || !list || !label || !input) return;

  const close = () => {
    root.classList.remove("is-open");
    list.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  };

  const open = () => {
    root.classList.add("is-open");
    list.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
  };

  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    if (root.classList.contains("is-open")) close();
    else open();
  });

  list.querySelectorAll("[data-value]").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.preventDefault();
      const value = btn.getAttribute("data-value") || "";
      const text = btn.getAttribute("data-label") || btn.textContent || "";
      input.value = value;
      label.textContent = text.trim();
      list.querySelectorAll(".filters-select__option").forEach((opt) => {
        opt.classList.toggle("is-selected", opt === btn);
      });
      close();
      const form = closestForm(root);
      if (form) form.submit();
    });
  });

  document.addEventListener("click", (event) => {
    if (!root.contains(event.target)) close();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
}

function initFilterCollapse(group) {
  if (!group || group.dataset.collapseReady === "1") return;
  const limit = Math.max(1, parseInt(group.dataset.filtersLimit || "3", 10) || 3);
  const options = Array.from(group.querySelectorAll(".filters__option"));
  if (options.length <= limit) return;

  group.dataset.collapseReady = "1";
  const labels = collapseLabels(group);
  const extra = options.slice(limit);
  let expanded = extra.some((opt) => {
    const input = opt.querySelector("input");
    return input && input.checked;
  });

  const apply = () => {
    extra.forEach((opt) => {
      opt.hidden = !expanded;
      opt.classList.toggle("is-extra", true);
    });
    const hiddenCount = extra.filter((opt) => opt.hidden).length;
    moreBtn.textContent = expanded
      ? labels.less
      : `${labels.more} (${hiddenCount || extra.length})`;
    moreBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
  };

  const moreBtn = document.createElement("button");
  moreBtn.type = "button";
  moreBtn.className = "filters__more";
  moreBtn.setAttribute("data-filters-more", "");
  moreBtn.addEventListener("click", (event) => {
    event.preventDefault();
    expanded = !expanded;
    apply();
  });

  const actions = group.querySelector(".filters__actions");
  if (actions) group.insertBefore(moreBtn, actions);
  else group.appendChild(moreBtn);

  apply();
}

export function initFilters() {
  document.querySelectorAll("[data-filters-select]").forEach(initFilterSortSelect);
  document.querySelectorAll("[data-filters-collapse]").forEach(initFilterCollapse);
}
