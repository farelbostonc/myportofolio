let toastTimer;
function showToast(title, message, type = 'normal', duration = 3000) {
    const toastComponent = document.getElementById('toast-component');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    if (!toastComponent) return;
    toastComponent.classList.remove('toast-success', 'toast-error', 'toast-normal');
    if (type === 'success') {
        toastComponent.classList.add('toast-success');
    } else if (type === 'error') {
        toastComponent.classList.add('toast-error');
    } else {
        toastComponent.classList.add('toast-normal');
    }
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    clearTimeout(toastTimer);
    // Buka ulang agar toast berada di atas modal yang baru dibuka.
    if (toastComponent.matches(':popover-open')) toastComponent.hidePopover();
    toastComponent.showPopover();
    void toastComponent.offsetHeight;
    toastComponent.classList.remove('toast-hidden');
    toastComponent.classList.add('toast-show');
    toastTimer = setTimeout(() => {
        toastComponent.classList.remove('toast-show');
        toastComponent.classList.add('toast-hidden');
        toastTimer = setTimeout(() => toastComponent.hidePopover(), 300);
    }, duration);
}
