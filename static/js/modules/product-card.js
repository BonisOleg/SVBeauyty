function closeAllVariantPickers(except) {
  document.querySelectorAll('[data-card-variant-ui].is-open').forEach((ui) => {
    if (except && ui === except) return;
    ui.classList.remove('is-open');
    const card = ui.closest('[data-product-card]');
    if (card) card.classList.remove('is-open');
    const trigger = ui.querySelector('[data-card-variant-trigger]');
    const list = ui.querySelector('[data-card-variant-list]');
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    if (list) list.hidden = true;
  });
}

function applyVariant(card, option) {
  if (!option || option.dataset.inStock === '0') return;

  const input = card.querySelector('[data-card-variant-input]');
  const label = card.querySelector('[data-card-variant-label]');
  const thumb = card.querySelector('[data-card-variant-thumb] img');
  const priceValue = card.querySelector('[data-card-price-value]');
  const priceOld = card.querySelector('[data-card-price-old]');
  const buyBtn = card.querySelector('[data-card-buy-btn]');

  if (input) input.value = option.dataset.value || '';
  if (label) label.textContent = option.dataset.label || '';
  if (thumb && option.dataset.thumb) thumb.src = option.dataset.thumb;

  if (priceValue) {
    priceValue.textContent = option.dataset.price || '';
    priceValue.classList.toggle('price__value--sale', option.dataset.isSale === '1');
  }
  if (priceOld) {
    const old = option.dataset.oldPrice || '';
    priceOld.textContent = old;
    priceOld.hidden = !old;
  }
  if (buyBtn) buyBtn.disabled = option.dataset.inStock !== '1';

  card.querySelectorAll('[data-card-variant-option]').forEach((item) => {
    const selected = item === option;
    item.classList.toggle('is-selected', selected);
    item.setAttribute('aria-selected', selected ? 'true' : 'false');
  });
}

export function initProductCards(root = document) {
  root.querySelectorAll('[data-product-card]').forEach((card) => {
    const ui = card.querySelector('[data-card-variant-ui]');
    if (!ui || ui.dataset.ready === '1') return;
    ui.dataset.ready = '1';

    const trigger = ui.querySelector('[data-card-variant-trigger]');
    const list = ui.querySelector('[data-card-variant-list]');
    const buyBtn = card.querySelector('[data-card-buy-btn]');
    const selected = ui.querySelector('[data-card-variant-option].is-selected')
      || ui.querySelector('[data-card-variant-option]:not(.is-disabled)');
    if (selected) applyVariant(card, selected);
    else if (buyBtn) buyBtn.disabled = false;

    if (!trigger || !list) return;

    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      const willOpen = !ui.classList.contains('is-open');
      closeAllVariantPickers(willOpen ? ui : null);
      ui.classList.toggle('is-open', willOpen);
      card.classList.toggle('is-open', willOpen);
      trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      list.hidden = !willOpen;
    });

    list.addEventListener('click', (event) => {
      const option = event.target.closest('[data-card-variant-option]');
      if (!option || option.classList.contains('is-disabled')) return;
      applyVariant(card, option);
      closeAllVariantPickers();
    });
  });
}

document.addEventListener('click', (event) => {
  if (event.target.closest('[data-card-variant-ui]')) return;
  closeAllVariantPickers();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeAllVariantPickers();
});
