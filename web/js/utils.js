// ============================================
// UTILS
// ============================================

export function pad(n) {
    return '    '.repeat(n);
}

export function flashButton(btn, text = "✓ Done", duration = 2000) {
    const original = btn.textContent;
    btn.textContent = text;
    setTimeout(() => btn.textContent = original, duration);
}

export function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
}