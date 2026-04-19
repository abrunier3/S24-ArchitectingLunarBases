// ============================================
// MODALS MODULE
// ============================================

// ---------- Generic Helper ----------
function toggleModal(id, open) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('open', open);
}

// ============================================
// GitHub Publish Modal
// ============================================

export function openGitHubModal() {
    const saved = localStorage.getItem('gh_token');
    if (saved) {
        document.getElementById('ghToken').value = saved;
    }

    document.getElementById('ghStatus').textContent = '';
    toggleModal('ghModalOverlay', true);
}

export function closeGitHubModal() {
    toggleModal('ghModalOverlay', false);
}


// ============================================
// Run Pipeline Modal
// ============================================

export function openRunPipelineModal() {
    const saved = localStorage.getItem('gh_token');
    if (saved) {
        document.getElementById('pipelineToken').value = saved;
    }

    document.getElementById('pipelineStatus').textContent = '';
    toggleModal('pipelineModalOverlay', true);
}

export function closePipelineModal() {
    toggleModal('pipelineModalOverlay', false);
}


// ============================================
// Paste SysML Modal
// ============================================

export function openPasteModal() {
    document.getElementById('pasteInput').value = '';
    toggleModal('pasteModalOverlay', true);

    setTimeout(() => {
        document.getElementById('pasteInput').focus();
    }, 100);
}

export function closePasteModal() {
    toggleModal('pasteModalOverlay', false);
}


// ============================================
// Add Node Modal
// ============================================

export function openAddNodeModal(parentId = null) {
    window.modalParentId = parentId;

    const title = document.getElementById('modalTitle');
    title.textContent = parentId ? 'Add Child Node' : 'Add Root Node';

    document.getElementById('modalNodeName').value = '';

    toggleModal('modalOverlay', true);

    setTimeout(() => {
        document.getElementById('modalNodeName').focus();
    }, 100);
}

export function closeModal() {
    toggleModal('modalOverlay', false);
}