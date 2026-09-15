export function open(dialog) {
 if (!dialog || dialog.open) return;
 const previous = document.activeElement;
 dialog.showModal();
 dialog.querySelector('.asset-preview-close')?.focus();
 dialog.addEventListener('cancel', event => {
  event.preventDefault();
  dialog.querySelector('.asset-preview-close')?.click();
 }, { once: true });
 dialog.addEventListener('click', () => {
  queueMicrotask(() => { if (!dialog.isConnected && previous?.isConnected) previous.focus(); });
 });
}
