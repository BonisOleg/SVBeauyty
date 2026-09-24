(() => {
  let root = null;
  let lastFocus = null;

  const close = () => {
    if (!root) return;
    const frame = root.querySelector("[data-preview-frame]");
    const img = root.querySelector("[data-preview-img]");
    if (frame) frame.src = "";
    if (img) img.removeAttribute("src");
    root.hidden = true;
    document.documentElement.classList.remove("file-preview-open");
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
  };

  const ensure = () => {
    if (root) return root;
    root = document.createElement("div");
    root.className = "file-preview";
    root.hidden = true;
    root.innerHTML =
      '<div class="file-preview__stage" data-preview-stage>' +
      '<img class="file-preview__img" data-preview-img alt="">' +
      '<iframe class="file-preview__frame" data-preview-frame title=""></iframe>' +
      "</div>" +
      '<div class="file-preview__bar">' +
      '<p class="file-preview__name" data-preview-title></p>' +
      '<a class="file-preview__download" data-preview-download download></a>' +
      '<button type="button" class="file-preview__close" data-preview-close>×</button>' +
      "</div>";
    document.body.appendChild(root);
    root.querySelector("[data-preview-close]").addEventListener("click", close);
    root.querySelector("[data-preview-stage]").addEventListener("click", (event) => {
      if (event.target === event.currentTarget) close();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && root && !root.hidden) close();
    });
    return root;
  };

  window.svOpenFilePreview = ({ url, name, kind, labels }) => {
    if (!url) return;
    const box = ensure();
    const text = labels || { close: "Закрити перегляд", download: "Завантажити" };
    const title = box.querySelector("[data-preview-title]");
    const frame = box.querySelector("[data-preview-frame]");
    const img = box.querySelector("[data-preview-img]");
    const download = box.querySelector("[data-preview-download]");
    const closeBtn = box.querySelector("[data-preview-close]");
    title.textContent = name || "";
    frame.title = name || "PDF";
    closeBtn.setAttribute("aria-label", text.close);
    closeBtn.textContent = "×";
    download.textContent = text.download;
    const saveUrl = url + (url.includes("?") ? "&" : "?") + "download=1";
    download.href = saveUrl;
    download.setAttribute("download", name || "");
    if (kind === "pdf") {
      img.hidden = true;
      frame.hidden = false;
      frame.src = url;
    } else {
      frame.hidden = true;
      frame.src = "";
      img.hidden = false;
      img.src = url;
      img.alt = name || "";
    }
    lastFocus = document.activeElement;
    box.hidden = false;
    document.documentElement.classList.add("file-preview-open");
    closeBtn.focus();
  };
})();
