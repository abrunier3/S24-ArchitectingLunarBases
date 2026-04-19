// ============================================
// NOTIFICATIONS MODULE
// ============================================

export function showSuccess(message) {
    const banner = document.getElementById('successBanner');
    const check  = banner.querySelector('.check');
    const msgEl  = document.getElementById('successMsg');

    banner.style.background = '';
    banner.style.borderColor = '';
    banner.style.color = '';

    check.textContent = '✓';
    msgEl.textContent = message;

    banner.style.display = 'flex';

    clearTimeout(banner._timeout);
    banner._timeout = setTimeout(() => {
        banner.style.display = 'none';
    }, 3000);
}


export function showError(message) {
    const banner = document.getElementById('successBanner');
    const check  = banner.querySelector('.check');
    const msgEl  = document.getElementById('successMsg');

    banner.style.background   = 'rgba(255,77,109,0.1)';
    banner.style.borderColor  = 'rgba(255,77,109,0.3)';
    banner.style.color        = 'var(--danger)';

    check.textContent = '✗';
    msgEl.textContent = message;

    banner.style.display = 'flex';

    clearTimeout(banner._timeout);
    banner._timeout = setTimeout(() => {
        banner.style.display = 'none';
        banner.style.background = '';
        banner.style.borderColor = '';
        banner.style.color = '';
        check.textContent = '✓';
    }, 3000);
}