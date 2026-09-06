/* Dismiss only a complete backdrop gesture, never a drag out of a dialog. */
(() => {
  let gesture = null;
  const dialogAt = event => event.target?.closest?.('dialog[open]');
  const outside = (dialog, event) => {
    const rect = dialog.getBoundingClientRect();
    return event.clientX < rect.left || event.clientX > rect.right ||
      event.clientY < rect.top || event.clientY > rect.bottom;
  };
  const clear = () => { gesture = null; };

  document.addEventListener('pointerdown', event => {
    clear();
    const dialog = dialogAt(event);
    if (event.button !== 0 || event.isPrimary === false || !dialog || !outside(dialog, event)) return;
    gesture = { dialog, pointerId: event.pointerId, released: false };
  }, true);

  document.addEventListener('pointerup', event => {
    if (!gesture) return;
    const { dialog, pointerId } = gesture;
    if (event.pointerId !== pointerId || event.button !== 0 || !dialog.open ||
        dialogAt(event) !== dialog || !outside(dialog, event)) return clear();
    gesture.released = true;
  }, true);

  // Consume the click before closing so it cannot activate the page underneath.
  document.addEventListener('click', event => {
    const completed = gesture;
    clear();
    if (!completed?.released || !completed.dialog.open || event.detail === 0 ||
        dialogAt(event) !== completed.dialog || !outside(completed.dialog, event)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    completed.dialog.close();
  }, true);

  document.addEventListener('pointercancel', clear, true);
  document.addEventListener('close', clear, true);
  window.addEventListener('blur', clear);
})();
