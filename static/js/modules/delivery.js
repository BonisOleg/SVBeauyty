export function initDeliveryMethod(root = document) {
  const form = root.querySelector('[data-checkout-delivery]');
  if (!form) return;

  const radios = form.querySelectorAll('[data-delivery-method]');
  const panels = form.querySelectorAll('[data-delivery-panel]');
  if (radios.length && panels.length) {
    const sync = () => {
      const selected = form.querySelector('[data-delivery-method]:checked');
      const method = selected ? selected.value : 'nova_poshta';
      panels.forEach((panel) => {
        const match = panel.dataset.deliveryPanel === method;
        panel.hidden = !match;
      });
      form.querySelectorAll('.delivery-methods .radio-card').forEach((card) => {
        const input = card.querySelector('[data-delivery-method]');
        card.classList.toggle('is-active', Boolean(input && input.checked));
      });
    };

    radios.forEach((radio) => radio.addEventListener('change', sync));
    sync();
  }

  const otherRecipient = form.querySelector('[data-other-recipient]');
  const recipientPanel = form.querySelector('[data-recipient-panel]');
  if (otherRecipient && recipientPanel) {
    const syncRecipient = () => {
      recipientPanel.hidden = !otherRecipient.checked;
      recipientPanel.querySelectorAll('input').forEach((input) => {
        if (otherRecipient.checked) input.removeAttribute('disabled');
        else input.setAttribute('disabled', 'disabled');
      });
    };
    otherRecipient.addEventListener('change', syncRecipient);
    syncRecipient();
  }
}
