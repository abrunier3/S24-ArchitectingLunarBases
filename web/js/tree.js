import {
    tree,
    selectedNodeId,
    setSelectedNode,
    findNode
} from './state.js';


// ============================================
// TREE RENDERING
// ============================================

export function renderTree() {
    const container = document.getElementById('treeContainer');

    if (tree.length === 0) {
        container.innerHTML = '<div class="tree-empty">No nodes</div>';
        return;
    }

    container.innerHTML = '';

    tree.forEach(node => {
        container.appendChild(buildNodeEl(node));
    });
}

function buildNodeEl(node) {
    const el = document.createElement('div');
    el.className = 'tree-node';
    el.textContent = node.name;

    el.onclick = () => {
        setSelectedNode(node.id);
        renderTree();
    };

    if (node.id === selectedNodeId) {
        el.style.fontWeight = 'bold';
    }

    return el;
}