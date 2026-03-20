// ============================================
// FORM MODULE
// ============================================

export function collectFormData() {
    return {
        length: document.getElementById('dimLength').value,
        width: document.getElementById('dimWidth').value,
        height: document.getElementById('dimHeight').value
    };
}

export function resetForm() {
    document.getElementById('dimLength').value = '';
    document.getElementById('dimWidth').value = '';
    document.getElementById('dimHeight').value = '';
}